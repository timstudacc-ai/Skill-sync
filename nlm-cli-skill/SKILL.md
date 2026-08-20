---
name: nlm-cli-skill
description: Brief description of what this skill does
---

# NotebookLM Retrieval & Synthesis Protocol

A pure retrieval pipeline. Query NotebookLM via the nlm **CLI**, combine retrieved content with conversation context, then pause for clarification. Does NOT manage sources, does NOT generate execution plans.

---

## Phase 1: Profile Routing & Notebook Discovery

Route to the correct profile and discover notebooks dynamically — never hardcode notebook IDs.

* **`work` profile:** Embedded engineering, firmware (STM32, ESP32, nRF54), datasheets, RTOS.
* **`personal` profile:** Non-embedded research, prompting, personal projects, general notes.

1. Determine domain (embedded/work vs. general/personal).
2. Switch profile if needed: `nlm login switch work` or `nlm login switch personal`.
3. Discover notebooks: nlm notebook list --json, then based on user request and conversation topic select appropriate notebook. 
### Notebook Taxonomy
- `"<Project Name>"` — memory bank (Drive sources, auto-synced)
- `"<Topic> docs (for Agent)"` — documentation for AI queries
- `"<Topic> docs (Human readable)"` — documentation for human reading
### Current ative notebook id's
"Nrf + zephyr docs (for Agent)" - 1e082400-927c-4694-b3e7-67f04ae62fc5
"ICM45686 Zephyr Driver" - 8178ecf4-351c-4236-848d-c925d2553797
"Nrf + zephyr docs (Human readable)" - 16314b9f-2098-4519-8517-3951a9aaf331
"nRF54L15 DK Schematic and PCB Layout Design" - 2f80b340-4046-4b11-bbc7-c48c97ceae25
"Cline Complete Documentation and Implementation Guide" - 03b269fb-08ad-4ef1-aab7-0bca0231d386
"STM32" - 4d3be3eb-621d-43f7-9434-5cd1a41b1343yy
"Xbox BLE HID" - a1dc0bb4-4005-4dbf-b8d3-188a4cfd9b05
"ESP32" - bc4c6332-3689-4672-9238-851d2dd06291
"ESP-IDF Programming Guide for ESP32 v5.3" - fde61edc-2cba-4acd-9317-bb0c00c2feda

---

## Phase 2: Query NotebookLM

Formulate a **detailed, architecturally descriptive question** and query the matched notebook:

**Query formulation rules:**
- Describe the full architecture in detail — state machine structure, RTOS primitives used, thread model, message passing, concurrency controls, and the specific problem you're solving.
- Do NOT ask brief or vague questions. Include module names, data structures, thread contexts, and the exact anti-pattern.
- If the codebase has a known flaw, describe it.
- The goal is to give NLM enough architectural context to provide specific, informed guidance — not generic advice.
- Do NOT interact with sources directly  — the user manages sources himself.
- When encountered an error, reffer nlm-cli-ai-ref skill for troubleshooting.
---
NEVER run asynchronious query, "&" at the end of the command s forbiden, each querry should be syncronyous and you should wait until the answer arrives
nlm notebook query <notebook_id> "<question>" --json | jq -r '.answer'
- Always sit there and wait until answer

## Phase 3: Synthesize — NLM + Conversation Context

Combine two streams into one unified response:

1. **What NLM returned** — the retrieved answer with citations.
2. **What you already know from the conversation** — the user's stated goal, previous clarifications, project context, constraints.

Weave them together. Do not paste NLM output verbatim; do not ignore the conversation context. The value is the synthesis of both, not either alone.

NLM handles its own knowledge boundaries — if it doesn't know, it says so. No need to double-guess it.

---

## Phase 4: Clarification

After presenting the synthesized response:

1. Identify what remains ambiguous or partial despite NLM + context.
2. Draft 1–3 clarifying questions for the user.
3. **STOP.** Wait for answers before proceeding.
---



## Tips for AI Assistants

1. **Always run `nlm login` first** if any auth error occurs
2. **Use `--confirm` for all generation/delete commands** to avoid blocking prompts
3. **Capture IDs from create outputs** - you'll need them for subsequent operations
4. **Use aliases** for frequently-used notebooks to simplify commands
5. **Poll for long operations** - audio/video takes 1-5 minutes; use `nlm studio status` or `nlm status artifacts`
6. **Research needs a destination** - use `--notebook-id` for an existing notebook or `--title` to create one
7. **Re-authenticate only for stale/missing credentials** - `unverified` means the probe was inconclusive
8. **Use `--max-wait 0`** for single status poll instead of blocking
9. **⚠️ ALWAYS ask user before delete** - Before running ANY delete command, ask the user for explicit confirmation.Deletions are IRREVERSIBLE. Show what will be deleted and warn about permanent data loss.
10. **Check aliases before creating** - Run `nlm alias list` or `nlm list aliases` before creating a new alias to avoid conflicts with existing names.
11. **DO NOT launch REPL** - Never use `nlm chat start` - it opens an interactive REPL that AI tools cannot control. Use `nlm notebook query` or `nlm query notebook` for one-shot Q&A instead.
12. **Choose output format wisely** - Default output (no flags) is compact and token-efficient—use it for status checks. Use `--quiet` to capture IDs for piping. Only use `--json` when you need to parse specific fields programmatically.
13. **Verb-first vs Noun-first** - Both command styles work identically. Use whichever is more natural for the context. Noun-first groups by resource (notebook, source), verb-first groups by action (create, list, delete).
14. **Download workflow** - Always wait for artifact completion before downloading. Check status with `nlm studio status <notebook>`, get the artifact ID, then download with `nlm download <type> <notebook> <artifact-id>`.
15. **Artifact generation takes time** - Audio/video: 1-5 minutes. Reports/quizzes: 30-60 seconds. Always poll status before attempting download.
16. **Download output files** - If no `--output` specified, files are saved with default names (e.g., `audio_<id>.mp3`, `video_<id>.mp4`, `report_<id>.txt`). Use `--output` to specify custom filenames.
17. **Streaming downloads** - All downloads use efficient streaming to handle large files without memory issues. This is automatic.
18. **Drive source sync** - Use `nlm source stale <notebook>` or `nlm list stale-sources <notebook>` to check whichDrive sources need syncing before running sync commands.
19. **Use --wait for blocking source adds** - When adding sources before querying, use `nlm source add ... --wait` to block until processing completes. This ensures the source is ready for queries.
20. **Export to Google Docs/Sheets** - Reports can be exported to Google Docs, Data Tables to Google Sheets. Use `nlm export to-docs/to-sheets <notebook> <artifact-id>`.
21. **Batch with tags** - Tag notebooks first (`nlm tag add ... --tags "topic"`), then use `--tags` flag with batchcommands for targeted multi-notebook operations.
22. **Pipelines for automation** - Use `nlm pipeline list` to see available workflows, then `nlm pipeline run` for automated multi-step operations (ingest → generate).