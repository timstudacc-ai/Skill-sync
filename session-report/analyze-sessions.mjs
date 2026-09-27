#!/usr/bin/env node
/* eslint-disable */
/**
 * analyze-sessions.mjs — agent-agnostic session usage analyzer.
 *
 * Consumes session logs in this skill's generic JSONL interchange format
 * (see references/format.md) and reports token usage, cost, message counts,
 * runtime, cache breaks, subagent, skill and model activity.
 *
 * Input: a single .jsonl file or a directory of .jsonl files (positional
 * argument, or --dir). One JSON record per line, two kinds:
 *
 *   {"ts":"ISO-or-epoch-ms","session":"id","kind":"api","project":"name",
 *    "model":"provider/model","subagent":null,"parent_session":null,
 *    "skill":null,"input":N,"cache_create":N,"cache_read":N,"output":N,
 *    "cost_usd":N}
 *   {"ts":...,"session":...,"kind":"human","project":...,"text":"...","skill":null}
 *
 * Output is human-readable text by default; --json emits the schema
 * consumed by template.html.
 *
 * Usage:
 *   node analyze-sessions.mjs [--dir PATH | PATH] [--json]
 *        [--since <ISO|7d|24h>] [--top N] [--cache-break N]
 *
 * Semantics:
 *  - "human": a human-typed prompt. Opens a new prompt entry and, if it
 *    carries (or starts with) a slash command, a skill attribution window
 *    that lasts until the next human record in the same session.
 *  - "api": one LLM API response. input = uncached input tokens;
 *    cache_create/cache_read = prompt-cache write/read tokens.
 *  - subagent runs: records tagged `subagent` (label) and `parent_session`.
 *    Tokens roll into the parent project and count as subagent usage; each
 *    contiguous run of one label counts as one subagent call.
 *  - Duplicate records (same session+ts+kind+usage) are dropped, so
 *    concatenating re-exported logs is safe.
 */

import fs from 'fs'
import path from 'path'
import readline from 'readline'

// ---------------------------------------------------------------------------
// CLI args
// ---------------------------------------------------------------------------
const argv = process.argv.slice(2)
const VALUE_FLAGS = new Set(['--dir', '--since', '--top', '--cache-break'])
function flag(name, dflt) {
  const i = argv.indexOf(name)
  if (i === -1) return dflt
  const v = argv[i + 1]
  return v === undefined || v.startsWith('--') ? true : v
}
const positional = []
for (let i = 0; i < argv.length; i++) {
  if (VALUE_FLAGS.has(argv[i])) { i++; continue }
  if (argv[i].startsWith('--')) continue
  positional.push(argv[i])
}
const ROOT = flag('--dir', positional[0] || null)
const AS_JSON = argv.includes('--json')
const TOP_N = parseInt(flag('--top', '15'), 10)
const SINCE_STR = flag('--since', null)
const SINCE = parseSince(SINCE_STR)
const CACHE_BREAK_THRESHOLD = parseInt(flag('--cache-break', '100000'), 10)
const IDLE_GAP_MS = 5 * 60 * 1000 // gaps >5min don't count toward "active" time

function parseSince(s) {
  if (!s) return null
  const m = /^(\d+)([dh])$/.exec(s)
  if (m) {
    const ms = m[2] === 'd' ? 86400000 : 3600000
    return new Date(Date.now() - parseInt(m[1], 10) * ms)
  }
  const d = new Date(s)
  return isNaN(d) ? null : d
}
// ---------------------------------------------------------------------------
// Stats container
// ---------------------------------------------------------------------------
function newStats() {
  return {
    sessions: new Set(),
    apiCalls: 0,
    inputUncached: 0, // input tokens (uncached)
    inputCacheCreate: 0, // prompt-cache write tokens
    inputCacheRead: 0, // prompt-cache read tokens
    outputTokens: 0,
    costUsd: 0,
    humanMessages: 0,
    wallClockMs: 0,
    activeMs: 0,
    cacheBreaks: [], // [{ts, session, project, uncached, total, kind, agentType, prompt}]
    subagentCalls: 0,
    subagentTokens: 0, // total (in+out) inside subagent runs
    skillInvocations: {}, // name -> count
    firstTs: null,
    lastTs: null,
  }
}

function addUsage(s, r) {
  s.apiCalls++
  s.inputUncached += r.inTok
  s.inputCacheCreate += r.cc
  s.inputCacheRead += r.cr
  s.outputTokens += r.out
  s.costUsd += r.cost
}

function bucket(map, key) {
  let s = map.get(key)
  if (!s) map.set(key, (s = newStats()))
  return s
}

function bumpSkill(s, name) {
  s.skillInvocations[name] = (s.skillInvocations[name] || 0) + 1
}

function* walk(dir) {
  let ents
  try {
    ents = fs.readdirSync(dir, { withFileTypes: true })
  } catch {
    return
  }
  for (const e of ents) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) yield* walk(p)
    else if (e.isFile() && e.name.endsWith('.jsonl')) yield p
  }
}

function normTs(v) {
  if (typeof v === 'number') return v // epoch ms
  if (typeof v === 'string') {
    const d = new Date(v)
    return isNaN(d) ? null : d.getTime()
  }
  return null
}

function slashName(text) {
  // A command name must be followed by whitespace or EOL, so file paths
  // like "/home/tim/..." are not mistaken for slash commands.
  const m = /^\/([A-Za-z][\w-]*)(?:\s|$)/.exec(String(text || '').trim())
  return m ? m[1] : null
}

function preview(text) {
  const t = String(text || '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  if (!t) return '(non-text)'
  return t.length > 240 ? t.slice(0, 237) + '…' : t
}

// ---------------------------------------------------------------------------
// Load records
// ---------------------------------------------------------------------------
const records = [] // normalized, in-range records, sorted by ts
const seen = new Set() // global dedupe of identical records

async function loadRecords(files) {
  for (const f of files) {
    const rl = readline.createInterface({
      input: fs.createReadStream(f),
      crlfDelay: Infinity,
    })
    for await (const line of rl) {
      const t = line.trim()
      if (!t) continue
      let e
      try {
        e = JSON.parse(t)
      } catch {
        continue
      }
      const ts = normTs(e.ts)
      if (ts === null) continue
      if (SINCE && ts < SINCE.getTime()) continue
      const kind = e.kind
      if (kind !== 'api' && kind !== 'human') continue
      const sid = e.session || 'unknown'
      const key =
        kind === 'api'
          ? `${sid}|${ts}|api|${e.input || 0}|${e.cache_create || 0}|${e.cache_read || 0}|${e.output || 0}`
          : `${sid}|${ts}|human`
      if (seen.has(key)) continue
      seen.add(key)
      records.push({
        ts,
        session: sid,
        project: e.project || 'unknown',
        kind,
        model: e.model || null,
        subagent: e.subagent || null,
        parent: e.parent_session || null,
        skill: e.skill || null,
        cost: +e.cost_usd || 0,
        inTok: +e.input || 0,
        cc: +e.cache_create || 0,
        cr: +e.cache_read || 0,
        out: +e.output || 0,
        text: kind === 'human' ? String(e.text || '') : null,
      })
    }
  }
  records.sort((a, b) => a.ts - b.ts) // Array#sort is stable
}
// ---------------------------------------------------------------------------
// Aggregation
// ---------------------------------------------------------------------------
const overall = newStats()
const perProject = new Map() // project -> stats
const perSubagent = new Map() // subagent label -> stats
const perSkill = new Map() // skill -> stats (token-attributed)
const perModel = new Map() // model id -> stats
const prompts = new Map() // promptKey -> {text, ts, project, sessionId, apiCalls, usage, subagentCalls}
const sessionTurns = new Map() // sessionId -> [promptKey, ...] in order
const sessionSpans = new Map() // spanKey (parent||session) -> {project, firstTs, lastTs, tokens}
const sessionState = new Map() // sessionId -> per-session accumulator

function processRecords() {
  for (const r of records) {
    const sid = r.session
    let S = sessionState.get(sid)
    if (!S) {
      S = {
        project: r.project,
        subLabel: r.subagent || null,
        currentPrompt: null,
        currentSkill: null,
        lastSubLabel: null,
        firstTs: r.ts,
        lastTs: r.ts,
        activeMs: 0,
        turnCount: 0,
      }
      sessionState.set(sid, S)
    }
    // active time (gaps > IDLE_GAP_MS excluded)
    if (r.ts - S.lastTs < IDLE_GAP_MS) S.activeMs += r.ts - S.lastTs
    S.lastTs = r.ts

    const project = bucket(perProject, r.project)
    const subagent = r.subagent ? bucket(perSubagent, r.subagent) : null

    overall.sessions.add(sid)
    project.sessions.add(sid)
    if (subagent) subagent.sessions.add(sid)

    // Each contiguous run of one subagent label counts as one subagent call.
    if (r.subagent && S.lastSubLabel !== r.subagent) {
      overall.subagentCalls++
      project.subagentCalls++
      if (subagent) subagent.subagentCalls++
      const ownerS = r.parent ? sessionState.get(r.parent) : S
      const pk = ownerS && ownerS.currentPrompt
      if (pk) {
        const pr = prompts.get(pk)
        if (pr) pr.subagentCalls++
      }
    }
    S.lastSubLabel = r.subagent || null

    // session span (for by_day timeline) — subagent runs roll into parent
    const spanKey = r.parent || sid
    let span = sessionSpans.get(spanKey)
    if (!span) {
      span = { project: r.project, firstTs: r.ts, lastTs: r.ts, tokens: 0 }
      sessionSpans.set(spanKey, span)
    }
    if (r.ts < span.firstTs) span.firstTs = r.ts
    if (r.ts > span.lastTs) span.lastTs = r.ts

    if (r.kind === 'human') {
      if (!r.subagent) {
        overall.humanMessages++
        project.humanMessages++
        S.turnCount++
        const pk = `${sid}:${S.turnCount}`
        prompts.set(pk, {
          text: preview(r.text),
          ts: new Date(r.ts).toISOString(),
          project: r.project,
          sessionId: sid,
          apiCalls: 0,
          inTok: 0,
          cc: 0,
          cr: 0,
          out: 0,
          cost: 0,
          subagentCalls: 0,
        })
        let turns = sessionTurns.get(sid)
        if (!turns) sessionTurns.set(sid, (turns = []))
        turns.push(pk)
        S.currentPrompt = pk
        const skill = r.skill || slashName(r.text)
        S.currentSkill = skill
        if (skill) {
          bumpSkill(overall, skill)
          bumpSkill(project, skill)
        }
      }
      continue
    }

    // api record
    const tot = r.inTok + r.cc + r.cr + r.out
    span.tokens += tot

    const skill = r.skill || S.currentSkill
    const skillStats = skill ? bucket(perSkill, skill) : null
    const targets = [overall, project]
    if (subagent) targets.push(subagent)
    if (skillStats) targets.push(skillStats)
    if (r.model) targets.push(bucket(perModel, r.model))
    for (const s of targets) addUsage(s, r)

    // prompt attribution (subagent records attribute to the parent session's
    // currently-active prompt, if the exporter provided parent_session)
    const ownerS = r.parent ? sessionState.get(r.parent) || S : S
    const pk = ownerS.currentPrompt
    if (pk) {
      const pr = prompts.get(pk)
      if (pr) {
        pr.apiCalls++
        pr.inTok += r.inTok
        pr.cc += r.cc
        pr.cr += r.cr
        pr.out += r.out
        pr.cost += r.cost
      }
    }

    // subagent token accounting on parent buckets
    if (r.subagent) {
      overall.subagentTokens += tot
      project.subagentTokens += tot
      if (subagent) subagent.subagentTokens += tot
    }

    // cache break detection
    const uncached = r.inTok + r.cc
    if (uncached > CACHE_BREAK_THRESHOLD) {
      const cb = {
        ts: new Date(r.ts).toISOString(),
        session: sid,
        project: r.project,
        uncached,
        total: uncached + r.cr,
        kind: r.subagent ? 'subagent' : 'main',
        agentType: r.subagent,
        prompt: pk,
      }
      overall.cacheBreaks.push(cb)
      project.cacheBreaks.push(cb)
      if (subagent) subagent.cacheBreaks.push(cb)
    }
  }
}

// Wall-clock / active time per session → overall, project, subagent buckets.
function distributeTime() {
  for (const [, S] of sessionState) {
    const wall = S.lastTs - S.firstTs
    const targets = [overall, bucket(perProject, S.project)]
    if (S.subLabel) targets.push(bucket(perSubagent, S.subLabel))
    for (const s of targets) {
      s.wallClockMs += wall
      s.activeMs += S.activeMs
      if (!s.firstTs || S.firstTs < s.firstTs) s.firstTs = S.firstTs
      if (!s.lastTs || S.lastTs > s.lastTs) s.lastTs = S.lastTs
    }
  }
}
// ---------------------------------------------------------------------------
// Prompt context / drill-down helpers
// ---------------------------------------------------------------------------
// ±2 user prompts around a given prompt, with the api-call count that
// followed each one. Used for drill-down in the HTML report.
function buildContext(pk) {
  const r = prompts.get(pk)
  if (!r) return null
  const turns = sessionTurns.get(r.sessionId)
  if (!turns) return null
  const i = turns.indexOf(pk)
  if (i === -1) return null
  const lo = Math.max(0, i - 2)
  const hi = Math.min(turns.length, i + 3)
  return turns.slice(lo, hi).map((k, j) => {
    const t = prompts.get(k) || {}
    return {
      text: t.text || '',
      ts: t.ts || null,
      calls: t.apiCalls || 0,
      here: lo + j === i,
    }
  })
}

// Group sessions into local-date buckets for the timeline view. A session is
// placed on the day its first record landed; tokens for that session
// (incl. subagent runs, which share the parent span) count toward that day.
function buildByDay() {
  const DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  const days = new Map() // yyyy-mm-dd -> {date, dow, tokens, sessions:[]}
  for (const [id, s] of sessionSpans) {
    if (s.firstTs === null || s.tokens === 0) continue
    const d0 = new Date(s.firstTs)
    const key = `${d0.getFullYear()}-${String(d0.getMonth() + 1).padStart(2, '0')}-${String(d0.getDate()).padStart(2, '0')}`
    let day = days.get(key)
    if (!day) {
      day = { date: key, dow: DOW[d0.getDay()], tokens: 0, sessions: [] }
      days.set(key, day)
    }
    const base = new Date(d0.getFullYear(), d0.getMonth(), d0.getDate()).getTime()
    day.tokens += s.tokens
    day.sessions.push({
      id,
      project: s.project,
      tokens: s.tokens,
      start_min: Math.max(0, Math.round((s.firstTs - base) / 60000)),
      end_min: Math.max(1, Math.round((s.lastTs - base) / 60000)),
    })
  }
  for (const d of days.values()) {
    // peak concurrency via 10-min buckets, capped at 24h for display
    const b = new Array(144).fill(0)
    for (const s of d.sessions) {
      const lo = Math.min(143, Math.floor(s.start_min / 10))
      const hi = Math.min(144, Math.ceil(Math.min(s.end_min, 1440) / 10))
      for (let i = lo; i < hi; i++) b[i]++
    }
    d.peak = Math.max(0, ...b)
    d.peak_at_min = d.peak > 0 ? b.indexOf(d.peak) * 10 : 0
    d.sessions.sort((a, b) => a.start_min - b.start_min)
  }
  return [...days.values()].sort((a, b) => a.date.localeCompare(b.date))
}

function promptTotal(r) {
  return r.inTok + r.cc + r.cr + r.out
}

function topPrompts(n) {
  return [...prompts.entries()]
    .filter(([, r]) => r.apiCalls > 0)
    .sort((a, b) => promptTotal(b[1]) - promptTotal(a[1]))
    .slice(0, n)
    .map(([pk, r]) => ({
      ts: r.ts,
      project: r.project,
      session: r.sessionId,
      text: r.text,
      api_calls: r.apiCalls,
      subagent_calls: r.subagentCalls,
      total_tokens: promptTotal(r),
      input: {
        uncached: r.inTok,
        cache_create: r.cc,
        cache_read: r.cr,
      },
      output: r.out,
      cost_usd: Math.round(r.cost * 1e4) / 1e4,
      context: buildContext(pk),
    }))
}
// ---------------------------------------------------------------------------
// Output
// ---------------------------------------------------------------------------
function fmt(n) {
  if (n >= 1e9) return (n / 1e9).toFixed(2) + 'B'
  if (n >= 1e6) return (n / 1e6).toFixed(2) + 'M'
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'k'
  return String(n)
}
function pct(a, b) {
  return b > 0 ? ((100 * a) / b).toFixed(1) + '%' : '—'
}
function hrs(ms) {
  return (ms / 3600000).toFixed(1)
}

function summarize(s) {
  const inTotal = s.inputUncached + s.inputCacheCreate + s.inputCacheRead
  return {
    sessions: s.sessions.size,
    api_calls: s.apiCalls,
    input_tokens: {
      uncached: s.inputUncached,
      cache_create: s.inputCacheCreate,
      cache_read: s.inputCacheRead,
      total: inTotal,
      pct_cached:
        inTotal > 0 ? +((100 * s.inputCacheRead) / inTotal).toFixed(1) : 0,
    },
    output_tokens: s.outputTokens,
    cost_usd: Math.round(s.costUsd * 1e4) / 1e4,
    human_messages: s.humanMessages,
    hours: { wall_clock: +hrs(s.wallClockMs), active: +hrs(s.activeMs) },
    cache_breaks_over_100k: s.cacheBreaks.length,
    subagent: {
      calls: s.subagentCalls,
      total_tokens: s.subagentTokens,
      avg_tokens_per_call:
        s.subagentCalls > 0
          ? Math.round(s.subagentTokens / s.subagentCalls)
          : 0,
    },
    skill_invocations: s.skillInvocations,
    span: s.firstTs
      ? {
          from: new Date(s.firstTs).toISOString(),
          to: new Date(s.lastTs).toISOString(),
        }
      : null,
  }
}

function printJson() {
  const out = {
    root: ROOT,
    generated_at: new Date().toISOString(),
    since: SINCE_STR || null,
    overall: summarize(overall),
    cache_breaks: overall.cacheBreaks
      .sort((a, b) => b.uncached - a.uncached)
      .slice(0, 100)
      .map(({ prompt, ...b }) => ({
        ...b,
        context: prompt ? buildContext(prompt) : null,
      })),
    by_project: Object.fromEntries(
      [...perProject].map(([k, v]) => [k, summarize(v)]),
    ),
    by_subagent_type: Object.fromEntries(
      [...perSubagent].map(([k, v]) => [k, summarize(v)]),
    ),
    by_skill: Object.fromEntries(
      [...perSkill].map(([k, v]) => [k, summarize(v)]),
    ),
    by_model: Object.fromEntries(
      [...perModel].map(([k, v]) => [k, summarize(v)]),
    ),
    top_prompts: topPrompts(100),
    by_day: buildByDay(),
  }
  process.stdout.write(JSON.stringify(out, null, 2) + '\n')
}
function totalIn(s) {
  return s.inputUncached + s.inputCacheCreate + s.inputCacheRead
}

function printText() {
  const line = (...a) => console.log(...a)
  const hr = () => line('─'.repeat(78))

  line()
  line(`Agent session analysis — ${ROOT}`)
  if (SINCE) line(`(since ${SINCE.toISOString()})`)
  hr()
  printBlock('OVERALL', overall)

  hr()
  line(
    `CACHE BREAKS (>${fmt(CACHE_BREAK_THRESHOLD)} uncached input on a single call)`,
  )
  const breaks = overall.cacheBreaks
    .sort((a, b) => b.uncached - a.uncached)
    .slice(0, TOP_N)
  if (breaks.length === 0) line('  none')
  for (const b of breaks) {
    line(
      `  ${fmt(b.uncached).padStart(8)} uncached / ${fmt(b.total).padStart(8)} total  ` +
        `${(b.ts || '').slice(0, 19)}  ${b.project}` +
        (b.kind === 'subagent' ? `  [${b.agentType}]` : ''),
    )
  }
  if (overall.cacheBreaks.length > TOP_N)
    line(`  … ${overall.cacheBreaks.length - TOP_N} more`)

  hr()
  line('MOST EXPENSIVE PROMPTS (total tokens incl. subagent runs during the turn)')
  const top = topPrompts(TOP_N)
  if (top.length === 0) line('  none')
  for (const r of top) {
    const inTot = r.input.uncached + r.input.cache_create + r.input.cache_read
    line(
      `  ${fmt(r.total_tokens).padStart(8)}  ` +
        `(in ${fmt(inTot)} ${pct(r.input.cache_read, inTot)} cached, out ${fmt(r.output)})  ` +
        `${r.api_calls} calls` +
        (r.subagent_calls ? `, ${r.subagent_calls} subagents` : '') +
        `  ${(r.ts || '').slice(0, 16)}  ${r.project}`,
    )
    line(`           "${r.text}"`)
  }

  hr()
  line('BY PROJECT (top by total input tokens)')
  const projects = [...perProject.entries()].sort(
    (a, b) => totalIn(b[1]) - totalIn(a[1]),
  )
  for (const [name, s] of projects.slice(0, TOP_N)) {
    printBlock(name, s, '  ')
    line()
  }
  if (projects.length > TOP_N)
    line(`  … ${projects.length - TOP_N} more projects`)

  hr()
  line('BY SUBAGENT TYPE')
  const agents = [...perSubagent.entries()].sort(
    (a, b) => totalIn(b[1]) - totalIn(a[1]),
  )
  for (const [name, s] of agents) {
    printBlock(name, s, '  ')
    line()
  }

  hr()
  line(
    'BY SKILL / SLASH COMMAND (tokens attributed = from invocation until next human msg)',
  )
  const skills = [...perSkill.entries()].sort(
    (a, b) => totalIn(b[1]) - totalIn(a[1]),
  )
  for (const [name, s] of skills.slice(0, TOP_N)) {
    printBlock(name, s, '  ')
    line()
  }
  if (skills.length > TOP_N) line(`  … ${skills.length - TOP_N} more`)

  hr()
  line('BY MODEL')
  const models = [...perModel.entries()].sort(
    (a, b) => totalIn(b[1]) - totalIn(a[1]),
  )
  for (const [name, s] of models) {
    printBlock(name, s, '  ')
    line()
  }
  line()
}

function printBlock(title, s, indent = '') {
  const inTotal = totalIn(s)
  console.log(`${indent}${title}`)
  console.log(
    `${indent}  sessions: ${s.sessions.size}   api calls: ${s.apiCalls}   human msgs: ${s.humanMessages}`,
  )
  console.log(
    `${indent}  input:  ${fmt(inTotal)} total  ` +
      `(uncached ${fmt(s.inputUncached)}, cache-create ${fmt(s.inputCacheCreate)}, cache-read ${fmt(s.inputCacheRead)} = ${pct(s.inputCacheRead, inTotal)} cached)`,
  )
  console.log(`${indent}  output: ${fmt(s.outputTokens)}`)
  if (s.costUsd > 0) console.log(`${indent}  cost:   $${s.costUsd.toFixed(4)}`)
  console.log(
    `${indent}  hours:  ${hrs(s.wallClockMs)} wall-clock, ${hrs(s.activeMs)} active (gaps >5m excluded)`,
  )
  console.log(
    `${indent}  cache breaks >${fmt(CACHE_BREAK_THRESHOLD)}: ${s.cacheBreaks.length}`,
  )
  console.log(
    `${indent}  subagents: ${s.subagentCalls} calls, ${fmt(s.subagentTokens)} tokens, avg ${fmt(
      s.subagentCalls ? Math.round(s.subagentTokens / s.subagentCalls) : 0,
    )}/call`,
  )
  const topSkills = Object.entries(s.skillInvocations)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
  if (topSkills.length)
    console.log(
      `${indent}  skills: ${topSkills.map(([k, v]) => `${k}×${v}`).join(', ')}`,
    )
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  if (!ROOT) {
    console.error(
      'usage: node analyze-sessions.mjs <file-or-dir> [--json] [--since 7d] [--top N] [--cache-break N]',
    )
    process.exit(1)
  }
  let st
  try {
    st = fs.statSync(ROOT)
  } catch {
    console.error(`analyze-sessions: no such file or directory: ${ROOT}`)
    process.exit(1)
  }
  const files = st.isFile() ? [ROOT] : [...walk(ROOT)]
  if (files.length === 0)
    console.error(`analyze-sessions: no .jsonl files under ${ROOT}`)

  await loadRecords(files)
  processRecords()
  distributeTime()

  // Drop empty buckets (e.g. everything filtered out by --since)
  for (const m of [perProject, perSubagent, perSkill, perModel]) {
    for (const [k, v] of m) {
      if (v.apiCalls === 0 && v.sessions.size === 0) m.delete(k)
    }
  }

  if (AS_JSON) printJson()
  else printText()
}

main().catch(e => {
  console.error(e)
  process.exit(1)
})
