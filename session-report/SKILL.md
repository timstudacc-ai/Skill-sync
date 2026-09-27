---
name: session-report
description: Generate an explorable HTML report of AI coding-agent session usage (tokens, cost, cache, subagents, skills, expensive prompts). Agent-agnostic via a generic JSONL session-log format; bundled exporter for Cline.
---

# Session Report

Produce a self-contained HTML report of agent session usage and save it to the current working directory. Agent-agnostic by design: data flows through a two-stage pipeline — **export** (agent-specific) → **analyze** (generic) → **report**.

## Steps

1. **Export session logs** to the skill's generic format. Default window: last 7 days; honor a different range if the user passed one (e.g. `24h`, `30d`, or all time).
   - **Cline** (bundled exporter; same directory as this SKILL.md — use absolute paths):
     ```sh
     node <skill-dir>/export-cline.mjs --since 7d > /tmp/session-log.jsonl
     ```
   - **Any other agent**: read `references/format.md` — the interchange format spec. Write a small exporter that converts your agent's native session/transcript storage into that format and saves it to `/tmp/session-log.jsonl`. You know your agent's storage layout; the spec is the only contract (~15 lines of JSON per event). Check whether a bundled exporter already matches your agent first.

2. **Analyze** the generic log:
   ```sh
   node <skill-dir>/analyze-sessions.mjs --json --since 7d /tmp/session-log.jsonl > /tmp/session-report.json
   ```
   Use the same window the user asked for; omit `--since` for all time. The analyzer is the source of truth for filtering, so it must always get the `--since` flag even if the exporter already filtered.

3. **Read** `/tmp/session-report.json`. Skim `overall`, `by_project`, `by_subagent_type`, `by_skill`, `by_model`, `cache_breaks`, `top_prompts`.

4. **Copy the template** (bundled alongside this SKILL.md) to the output path in the current working directory:
   ```sh
   cp <skill-dir>/template.html ./session-report-$(date +%Y%m%d-%H%M).html
   ```

5. **Edit the output file** with targeted edits — do not rewrite the file (preserve the template's JS/CSS):
   - Replace the contents of `<script id="report-data" type="application/json">` with the full JSON from step 2. The page's JS renders the hero total, all tables, bars, and drill-downs from this blob automatically.
   - Fill the `<!-- AGENT: anomalies -->` block with **3–5 one-line findings**. Express figures as a **% of total tokens** wherever possible (total = `overall.input_tokens.total + overall.output_tokens`). One line per finding, exact markup:
     ```html
     <div class="take bad"><div class="fig">41.2%</div><div class="txt"><b>cc-monitor</b> consumed 41% of the week across just 3 sessions</div></div>
     ```
     Classes: `.take bad` for waste/anomalies (red), `.take good` for healthy signals (green), `.take info` for neutral facts (blue). The `.fig` is one short number (a %, a count, or a multiplier like `12×`). The `.txt` is one plain-English sentence naming the project/skill/prompt; wrap the subject in `<b>`. Look for: a project or skill eating a disproportionate share, cache-hit <85%, a single prompt >2% of total, subagent types averaging >1M tokens/call, cache breaks clustering, one model in `by_model` dominating tokens or cost.
   - Fill the `<!-- AGENT: optimizations -->` block (at the **bottom** of the page) with 1–4 `<div class="callout">` suggestions tied to specific rows (e.g. "`/weekly-status` spawned 7 subagents for 8.1% of total — scope it to fewer parallel agents").
   - Do not restructure existing sections.

6. **Report** the saved file path to the user. Do not open it or render it.

## Notes

- The template is the source of interactivity (sorting, expand/collapse, block-char bars). Your job is data + narrative, not markup.
- Keep commentary terse and specific — reference actual project names, numbers, timestamps from the JSON.
- `top_prompts` includes subagent tokens in each prompt's total (subagent runs are attributed to the parent session's active prompt).
- If the JSON is >2MB, trim `top_prompts` to 100 entries and `cache_breaks` to 100 before embedding (they should already be capped).
- Exporters live next to this SKILL.md (`export-cline.mjs`); the format spec is in `references/format.md`. A new agent needs only a new exporter — the analyzer, template, and these steps stay unchanged.
