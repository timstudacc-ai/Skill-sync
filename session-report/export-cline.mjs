#!/usr/bin/env node
/* eslint-disable */
/**
 * export-cline.mjs — Cline adapter for the session-report skill.
 *
 * Reads Cline's local session database and the per-session message files
 * it points to, and writes the skill's generic session-log JSONL format
 * (see references/format.md) to stdout.
 *
 * Usage:
 *   node export-cline.mjs [--db PATH] [--since <ISO|7d|24h>]
 *
 * Cline storage notes (v3.0.x):
 *  - sessions.db `sessions` table: one row per session with cwd (project
 *    label), model, provider, is_subagent, parent_session_id, agent_id,
 *    interactive, started_at, ended_at, prompt, messages_path.
 *  - messages_path is a full-snapshot JSON file:
 *    { messages: [{ id, role, content[], ts (epoch ms), metrics?, modelInfo? }] }.
 *    Assistant messages carry metrics { inputTokens, outputTokens,
 *    cacheReadTokens, cacheWriteTokens, cost }.
 *  - "human" records: interactive main sessions, user messages whose first
 *    content block is text (tool_result blocks are internal). Prompt text is
 *    unwrapped from <user_input>/<mode_notice> wrappers; a leading
 *    "/command" marks a skill invocation.
 *
 * If reading a live WAL database read-only fails, copy sessions.db plus its
 * -wal/-shm siblings to a temp dir and point --db at the copy.
 */

import fs from 'fs'
import path from 'path'
import os from 'os'
import { spawnSync } from 'child_process'

// node:sqlite ships behind --experimental-sqlite on Node 22.x; re-exec with
// the flag if the bare import fails. On Node >= 23.4 it just works.
let DatabaseSync
try {
  ;({ DatabaseSync } = await import('node:sqlite'))
} catch (e) {
  if (process.env.__SESSION_EXPORT_REEXEC) {
    console.error('export-cline: node:sqlite unavailable (' + e.message + ')')
    console.error('Need Node >= 22.5 run with --experimental-sqlite, or Node >= 23.4')
    process.exit(1)
  }
  const r = spawnSync(
    process.execPath,
    ['--experimental-sqlite', ...process.argv.slice(1)],
    { stdio: 'inherit', env: { ...process.env, __SESSION_EXPORT_REEXEC: '1' } },
  )
  process.exit(r.status ?? 1)
}

// ---------------------------------------------------------------------------
// CLI args
// ---------------------------------------------------------------------------
const argv = process.argv.slice(2)
const VALUE_FLAGS = new Set(['--db', '--since'])
function flag(name, dflt) {
  const i = argv.indexOf(name)
  if (i === -1) return dflt
  const v = argv[i + 1]
  return v === undefined || v.startsWith('--') ? true : v
}
const DB_PATH = flag('--db', path.join(os.homedir(), '.cline', 'data', 'db', 'sessions.db'))
const SINCE = parseSince(flag('--since', null))

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

function tsMs(v) {
  if (!v) return null
  const d = new Date(v)
  return isNaN(d) ? null : d.getTime()
}

function inRange(ts) {
  if (!SINCE) return true
  const ms = tsMs(ts)
  return ms !== null && ms >= SINCE.getTime()
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function emit(rec) {
  process.stdout.write(JSON.stringify(rec) + '\n')
}

// Strip <user_input>/<mode_notice> wrappers and other tags; keep a
// human-readable prompt preview (analyzer caps display at 240 chars).
function cleanPrompt(text) {
  let t = String(text || '')
  const w = /<user_input[^>]*>([\s\S]*?)<\/user_input>/.exec(t)
  if (w) t = w[1]
  t = t
    .replace(/<mode_notice>[\s\S]*?<\/mode_notice>/g, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  return t.length > 500 ? t.slice(0, 497) + '…' : t
}

function slashName(text) {
  // A command name must be followed by whitespace or EOL, so file paths
  // like "/home/tim/..." are not mistaken for slash commands.
  const m = /^\/([A-Za-z][\w-]*)(?:\s|$)/.exec(String(text || '').trim())
  return m ? m[1] : null
}

function subagentLabel(s) {
  if (s.metadata_json) {
    try {
      const m = JSON.parse(s.metadata_json)
      for (const k of ['agentType', 'role', 'name', 'label']) {
        if (m && typeof m[k] === 'string' && m[k]) return m[k]
      }
    } catch {
      /* not JSON */
    }
  }
  return s.agent_id || 'subagent'
}
// ---------------------------------------------------------------------------
// Export one session's records
// ---------------------------------------------------------------------------
function exportSession(s) {
  const project = s.cwd ? path.basename(s.cwd) : 'unknown'
  const sid = s.session_id
  const isSub = !!s.is_subagent
  const subLabel = isSub ? subagentLabel(s) : null
  const parent = isSub ? s.parent_session_id || null : null
  const model = s.model || null

  // Skip sessions that ended entirely before the --since window.
  if (SINCE) {
    const endedMs = tsMs(s.ended_at || s.updated_at || s.started_at)
    if (endedMs !== null && endedMs < SINCE.getTime()) return
  }

  let messages = null
  if (s.messages_path && fs.existsSync(s.messages_path)) {
    try {
      const j = JSON.parse(fs.readFileSync(s.messages_path, 'utf8'))
      if (Array.isArray(j.messages)) messages = j.messages
    } catch {
      /* corrupt or unreadable — fall back below */
    }
  }

  if (!messages) {
    // No message file — still emit the session's first prompt as a human
    // record (interactive main sessions) so the session shows in the report.
    if (!isSub && s.interactive && s.prompt) {
      const text = cleanPrompt(s.prompt)
      if (inRange(s.started_at))
        emit({
          ts: s.started_at,
          session: sid,
          project,
          kind: 'human',
          text,
          skill: slashName(text),
        })
    }
    return
  }

  for (const m of messages) {
    const ts = m.ts ? new Date(m.ts).toISOString() : s.started_at
    if (!inRange(ts)) continue

    if (m.role === 'assistant') {
      const met = m.metrics
      if (!met) continue // no usage recorded (e.g. errored request)
      emit({
        ts,
        session: sid,
        project,
        kind: 'api',
        model: (m.modelInfo && m.modelInfo.id) || model,
        subagent: subLabel,
        parent_session: parent,
        input: met.inputTokens || 0,
        cache_create: met.cacheWriteTokens || 0,
        cache_read: met.cacheReadTokens || 0,
        output: met.outputTokens || 0,
        cost_usd: typeof met.cost === 'number' ? met.cost : null,
      })
    } else if (m.role === 'user' && !isSub && s.interactive) {
      const first = Array.isArray(m.content) ? m.content[0] : null
      const raw =
        first && first.type === 'text' && first.text
          ? first.text
          : typeof m.content === 'string'
            ? m.content
            : null
      if (!raw) continue
      // Auto-injected continuation messages are not human-typed prompts.
      if (/^\[(TASK RESUMPTION|mode_notice)/.test(raw.trim())) continue
      const text = cleanPrompt(raw)
      if (text)
        emit({ ts, session: sid, project, kind: 'human', text, skill: slashName(text) })
    }
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
function main() {
  if (!fs.existsSync(DB_PATH)) {
    console.error(`export-cline: database not found: ${DB_PATH}`)
    process.exit(1)
  }
  let db
  try {
    db = new DatabaseSync(DB_PATH, { readOnly: true })
  } catch (e) {
    console.error('export-cline: cannot open database read-only: ' + e.message)
    console.error('If it is locked, copy sessions.db (+ -wal/-shm) to /tmp and pass --db')
    process.exit(1)
  }
  let rows
  try {
    rows = db
      .prepare(
        `SELECT session_id, cwd, model, provider, is_subagent, parent_session_id,
                agent_id, interactive, started_at, ended_at, updated_at,
                prompt, metadata_json, messages_path
           FROM sessions`,
      )
      .all()
  } catch (e) {
    console.error('export-cline: failed to query sessions: ' + e.message)
    process.exit(1)
  }
  for (const s of rows) exportSession(s)
}

main()

