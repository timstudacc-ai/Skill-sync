# Generic session-log format (session-report skill)

The session-report skill analyzes agent usage from a simple, **agent-agnostic JSONL interchange format**. Any agent can use the skill by exporting its own session/transcript storage into this format: one JSON object per line, written in chronological order per session.

Two record kinds:

## `api` — one LLM API response

```json
{"ts":"2026-09-26T13:20:12.070Z","session":"1790428811527_yezvv","kind":"api",
 "project":"skill-creation","model":"cline-pass/glm-5.3",
 "subagent":null,"parent_session":null,"skill":null,
 "input":6044,"cache_create":0,"cache_read":288,"output":224,"cost_usd":0.00247}
```

## `human` — one human-typed prompt

```json
{"ts":"2026-09-26T13:20:11.739Z","session":"1790428811527_yezvv","kind":"human",
 "project":"skill-creation","text":"fix the flaky e2e test","skill":null}
```

## Fields

| field           | required            | meaning |
|-----------------|---------------------|---------|
| `ts`            | yes                 | ISO 8601 string or epoch-ms number |
| `session`       | yes                 | unique session id |
| `kind`          | yes                 | `"api"` or `"human"` |
| `project`       | recommended         | label for the working context (e.g. repo name); defaults to `"unknown"` |
| `input`         | api                 | uncached input tokens |
| `cache_create`  | api                 | prompt-cache write tokens (0 if your provider has none) |
| `cache_read`    | api                 | prompt-cache read tokens |
| `output`        | api                 | output tokens |
| `cost_usd`      | optional            | cost of the call in USD |
| `model`         | optional            | model id (enables the `by_model` breakdown) |
| `subagent`      | optional            | type label of the subagent run the record belongs to; `null`/omitted otherwise |
| `parent_session`| optional            | for subagent runs: the id of the parent session |
| `text`          | human               | prompt preview (tags stripped; first 240 chars shown) |
| `skill`         | optional            | skill/command name; on a human record it also opens an attribution window that lasts until the next human record in the same session |

## Rules

- **human records**: one per human-typed prompt. Tool results, auto-continuations, and injected context are *not* human records. Human records inside subagent runs are ignored by the analyzer.
- **subagent runs**: give them their **own session id**, tag every record with `subagent` (type label) and `parent_session` (parent's id). Each contiguous run of one label counts as one subagent call; its tokens roll into the parent's project and the parent's active prompt.
- **ordering**: records must be chronological within a session. Ordering across sessions doesn't matter — the analyzer sorts globally.
- **duplicates**: records with identical (session, ts, kind, token counts) are dropped, so re-running an exporter and concatenating output is safe.
- **cache metrics**: if your agent/provider has no prompt cache, emit 0s — cache-hit % and cache-break findings degrade gracefully.
- **slash commands**: if a human record's `text` starts with `/name` followed by whitespace or end-of-line, the analyzer attributes the following api records to that skill automatically (explicit `skill` field wins; leading file paths like `/home/...` are not treated as commands).

## Writing your own exporter

An exporter is a ~30-line script that walks your agent's native storage and prints these records to stdout. Sketch:

```js
// pseudocode — adapt to your agent's storage
for (const session of myAgent.listSessions()) {
  for (const ev of session.events) {            // chronological
    if (ev.isUserPrompt())                      // human-typed only
      console.log(JSON.stringify({
        ts: ev.ts, session: session.id, kind: 'human',
        project: session.project, text: ev.text,
      }))
    if (ev.isAssistantResponse())               // has token usage
      console.log(JSON.stringify({
        ts: ev.ts, session: session.id, kind: 'api',
        project: session.project, model: ev.model,
        input: ev.inputTokens, cache_create: ev.cacheWriteTokens,
        cache_read: ev.cacheReadTokens, output: ev.outputTokens,
        cost_usd: ev.cost, subagent: session.subagentType || null,
        parent_session: session.parentId || null,
      }))
  }
}
```

Then run `node analyze-sessions.mjs --json --since 7d my-log.jsonl > report.json` and continue with SKILL.md step 3.

**Bundled exporters:** `export-cline.mjs` — reads Cline's `~/.cline/data/db/sessions.db` and the per-session message files it references (needs Node ≥ 22.5 with `--experimental-sqlite`, or Node ≥ 23.4; the script re-execs itself with the flag when needed).
