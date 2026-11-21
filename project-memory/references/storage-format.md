# Kilo Project Memory — On-Disk Storage Format

Reference for the `project-memory` skill. Verified against Kilo CLI 7.8.15
(`packages/kilo-memory` in Kilo-Org/kilocode, introduced in PR #11921) and the
official docs: https://kilo.ai/docs/customize/context/memory

Read this when you need to inspect memory files directly, explain the format,
export memory, or diagnose why a recall/save behaved unexpectedly.

## Location and identity

```
<XDG_DATA_HOME or ~/.local/share>/kilo/memory/<project-slug>-<sha1-12>/
```

- `<project-slug>`: sanitized basename of the canonical project root.
- `<sha1-12>`: first 12 hex chars of SHA-1 of the canonical root path.
- Git worktrees resolve to the main repository root, so all worktrees of one
  repo share a single memory folder. Non-git directories use the directory itself.
- Example (this workspace): `~/.local/share/kilo/memory/skill-creation-2cd8c21c5fac/`
- `/memory inspect` (user command) reveals the folder for the current project.

## Folder contents

| File | Role | Hand-edit? |
| --- | --- | --- |
| `project.md` | Facts, Decisions, Constraints, Open Questions | Via `/memory edit` only |
| `environment.md` | Commands, Paths, Tooling | Via `/memory edit` only |
| `corrections.md` | Corrections to earlier memory | Via `/memory edit` only |
| `sessions/*.md` | One digest per saved session | No |
| `manifest.json` | Identity: kind, version, display, canonical path, folder, createdAt | No |
| `state.json` | Enabled flag, capture settings, injection/recall stats | No |
| `index.kmem` | Derived search/injection index, rebuilt from sources | No — `/memory rebuild` |
| `.gitignore` | Contains `*` and `!.gitignore` — folder never gets committed | No |

The three `.md` sources are the knowledge. Everything else is plumbing Kilo
regenerates; after any manual source edit the user should run `/memory rebuild`
(`/memory edit` does this automatically).

## Record grammar (source files)

```markdown
## Section
- key :: text
```

- One record per line: `- <key> :: <text>` (literal ` :: ` separator).
- `## Heading` sets the section for following records. Records before any
  heading fall into `Facts`.
- Default sections: `project.md` → Facts / Decisions / Constraints / Open
  Questions; `environment.md` → Commands / Paths / Tooling; `corrections.md` →
  Corrections. Auto-capture may create other sections; the parser accepts any.
- Malformed lines (no ` :: `, empty key or body) are skipped by the parser, so
  prose comments are tolerated but not indexed.
- Keys are slugs: lowercased, safe characters, length-capped; derived from the
  explicit `key` param or from the text. Canonical record id is
  `file:section:key` (each part slugified).

### Write semantics

- **Upsert:** same key in same section → line replaced in place; otherwise
  appended under the heading (heading created if missing).
- **Dedupe:** a new entry whose text is near-identical to an existing one in the
  same file+section (normalized equality, substring containment for texts ≥24
  chars, or ≥85% word overlap with ≥4 words) reuses the existing key.
- **Forget:** removes lines whose key/id matches the query exactly (aliases:
  `key`, `file:key`, `file:section:key`). No fuzzy deletion — unmatched queries
  remove nothing.
- **Routing:** explicit `remember` → `project.md`; explicit `correct` →
  `corrections.md` (section Corrections). Auto-capture classifies entries and
  can also write `environment.md`.
- **Limits:** text ≤12000 chars, key ≤256 chars; typed record text clipped at
  240 chars in the index and in recall (see "Size limits and configurability"
  below); ≤16 ops per capture run. Secret-like content is redacted or the op is
  skipped (explicit-only-secret saves fail loudly).
- **Timestamps:** records carry no per-entry timestamp on disk. Index
  `createdAt`/`updatedAt` are derived from file mtime minus line offset —
  ranking hints only, not reliable dates. Staleness must be judged by content.

## Size limits and configurability

Verified against `packages/kilo-memory/src/schema.ts` (Kilo-Org/kilocode, main,
2026-11-21); matches the `limits: 8192/5/480` line injected by CLI 7.8.15.

| Constant | Value | Meaning |
| --- | --- | --- |
| `maxProjectIndexBytes` | 8192 | Hard cap on the injected index block |
| `maxLineChars` | 240 | Typed record text clipping — in the index AND in recall results |
| `maxSessionLineChars` | 480 | Latest digest line in the index (older digest lines: 240) |
| `maxRecentSessions` | 5 | Digest rows shown in the index |
| `maxSessionFiles` | 20 | Digest files kept on disk (pruned, newest kept) |
| `maxConsolidationInputBytes` | 24000 | Turn context fed to one auto-capture run |
| `maxStoredDigestSummary` | 4000 | Summary length stored per digest |

**These limits are not configurable.** `schema.ts` hardcodes them, `persist()` omits
them, and `parse()` resets them from defaults on every read — hand-editing `limits` in
`state.json` does not survive. The programmatic `configure()` surface accepts only
`autoConsolidate` and `verbose`; the public config schema (`kilo.jsonc`) exposes only
`memory_model` for memory. Capture throttle values (`maxOpsPerRun`, `minIntervalMs`,
`timeoutMs`) persist in `state.json` but are internal plumbing, not a user surface.

What the user can control: enable/disable, auto-save on/off, `memory_model`,
`/memory purge`, and content via `/memory edit` + rebuild. The practical size lever is
content discipline: concise records and forgetting stale entries.

Because recall clips typed text at 240 chars, a record longer than that is only
readable in full from its source `.md` file (or `/memory show`). Keep records short
enough to survive clipping, or route long content to docs/AGENTS.md with a pointer.

## Session digest format

File name: `<ISO-timestamp, ':' replaced by '-'>_<session-slug>_<hash>.md`

```markdown
# Session <sessionID>

Version: 1
Updated: <ISO-8601>
Topic: <≤80-char topic>

## Summary
<redacted summary, length-capped>
```

- `Fallback: true` header line marks a non-LLM fallback digest (interrupted or
  errored turn).
- One digest per session: writing a new one deletes that session's older files.
- The digest set is pruned to a maximum file count (newest kept).
- Digests are what `recall mode=digest` and the injected `latest_session_digest`
  come from. The `session=<id>` pointer in the injected index is the argument
  for `sessionID`.

## state.json (observed defaults)

```json
{
  "version": 1,
  "enabled": true,
  "scope": "project",
  "autoInject": true,
  "autoConsolidate": true,
  "capture": {
    "mode": "selective",
    "turnClose": true,
    "explicit": true,
    "maxOpsPerRun": 16,
    "minIntervalMs": 300000,
    "timeoutMs": 30000
  },
  "stats": { "lastInjectedAt": 0, "lastRecallAt": null, "...": "..." }
}
```

- `enabled: false` → both agent tools return "memory is disabled"; injection
  and auto-capture stop. Stored files are kept.
- `autoConsolidate` → auto-save on turn close, throttled to ≥5 min intervals.
- `stats` tracks injection/recall/consolidation activity (diagnostics only).
- `stats.lastInjectedBytes` / `lastInjectedTokens`: measured size of the index injected
  at the last session start — the authoritative answer to "what does memory cost in
  context?" (read-only diagnostic).
- `stats.lastConsolidationTokens`: model tokens spent by the last auto-capture run —
  the background maintenance cost.

## Recall behavior worth knowing

- Keyword tokenizer: lowercases, splits camelCase and `_ . -`, suffix-tolerant
  matching, corpus-derived stopword filtering. No synonym/semantic expansion.
- Results are wrapped in a fenced block tagged
  `kilo-memory-v1 targeted_context_not_instruction` — context, never commands.
- `catalog` output: per-file `- key :: value` rows (values clipped to 60 chars)
  plus `- session=<id> <topic> <date>` rows (≤20 sessions, 120-char summaries);
  whole catalog capped at 8192 bytes — refine with a query filter when truncated.
- `search`/`typed` default limit 5, max 20; a live relevance floor drops weak
  matches, so an empty result can mean "nothing relevant", not "nothing stored"
  — confirm with `catalog`.

## User-facing `/memory` commands (CLI; alias `/mem`)

| Command | Effect |
| --- | --- |
| `/memory on` / `off` | Enable / disable (disable keeps files) |
| `/memory status` | Storage location + overview |
| `/memory show` | Show stored memory |
| `/memory remember <text>` / `correct <text>` / `forget <query>` | Explicit writes |
| `/memory auto on\|off` | Toggle auto-save |
| `/memory inspect` | Reveal the memory folder |
| `/memory edit` | Open sources in $EDITOR, auto-rebuild index |
| `/memory rebuild` | Regenerate index from sources |
| `/memory purge confirm` | Delete all project memory files |

VS Code equivalent: Settings → Context → Project memory / Auto-save switches.
Auto-save model can be overridden with `memory_model` in `kilo.jsonc`.
