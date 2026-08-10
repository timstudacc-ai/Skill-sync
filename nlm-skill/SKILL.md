---
name: nlm-skill
description: Query NotebookLM on demand, synthesize retrieved information with existing conversation context, and draft clarifying questions. Use when the user explicitly asks to query NLM, search notebooks, or retrieve documentation. Triggered by phrases like "check NLM", "search notebook", "query nlm", "/nlm".
---

# NotebookLM Retrieval & Synthesis Protocol

A pure retrieval pipeline. Query NotebookLM via the `notebooklm-mcp` MCP server, combine retrieved content with conversation context, then pause for clarification. Does NOT manage sources, does NOT generate execution plans.

---

## Phase 1: Profile Routing & Notebook Discovery

Route to the correct profile and discover notebooks dynamically — never hardcode notebook IDs.

* **`work` profile:** Embedded engineering, firmware (STM32, ESP32, nRF54), datasheets, RTOS.
* **`personal` profile:** Non-embedded research, prompting, personal projects, general notes.

1. Determine domain (embedded/work vs. general/personal).
2. Switch profile if needed: `nlm login switch work` or `nlm login switch personal`.
3. Discover notebooks: `notebook_list` (MCP tool).

---

## Phase 2: Query NotebookLM

Formulate a **detailed, architecturally descriptive question** and query the matched notebook:

```
notebook_query(notebook_id="<id>", query="<your precise question>")
```

**Query formulation rules:**
- Describe the full architecture in detail — state machine structure, RTOS primitives used, thread model, message passing, concurrency controls, and the specific problem you're solving.
- Do NOT ask brief or vague questions. Include module names, data structures, thread contexts, and the exact anti-pattern.
- If the codebase has a known flaw, describe it.
- The goal is to give NLM enough architectural context to provide specific, informed guidance — not generic advice.

- Optionally scope to specific sources with `source_ids=[...]` if the user names them.
- Do NOT interact with sources directly (`source_get_content`, `source_describe`) — the user manages sources himself.

---

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

## Phase 5: Hand-off

* If the user asks for an execution plan, `planning-skill` takes over — pass it the NLM findings and conversation context you just assembled.
* If no plan is needed, execute the task directly using the enriched context.

---

## Memory Bank Protocol

Each project has ONE notebook. Memory bank lives as **Google Docs** in a Drive folder, added as Drive sources — auto-synced, no manual delete/re-add. The structure of the memory bank itself is described in the memory-bank skill.

### Notebook Taxonomy
- `"<Project Name>"` — memory bank (Drive sources, auto-synced)
- `"<Topic> docs (for Agent)"` — documentation for AI queries
- `"<Topic> docs (Human readable)"` — documentation for human reading

### Lifecycle
- **Create:** Create Google Doc in Drive folder → `source add <nb> --drive <doc_id> --type doc`
- **Update:** Edit the Google Doc in browser/Drive → `source stale <nb>` (check) → `source sync <nb> --confirm`
- **Trigger:** auto-sync at end of every coding session, or on `update memory bank` / `save progress`

### Drive Setup (per project)
- Create a Drive folder: `createFolder(name="<Project Name>")`
- Memory bank files: `projectbrief`, `productContext`, `techContext`, `activeContext`, `systemPatterns`, `progress`, `problemsSolved`
- Each file is a Google Doc, added as a Drive source to the notebook

### Knowledge Write-back
User confirmation required (`save to NLM`, `/save-nlm`): `source_add --type text` for ad-hoc notes.
Never upload anything without the user saying so.
