---
name: nlm-cli-skill
description: Query the user's personal NotebookLM knowledge base through the nlm CLI via the nlmq wrapper. Use whenever the user asks to "ask my notebook", "query NotebookLM", "check my notes", or wants an answer grounded in their own material - Zephyr/nRF, ESP32/ESP-IDF, STM32, embedded Linux, computer architecture, physics labs, PySerial, oscilloscope manuals, Cline docs, or any notebook in their NotebookLM account. Retrieves an answer, synthesizes it with conversation context, then pauses for clarification. Does NOT manage sources and does NOT generate artifacts.
---

# NotebookLM Retrieval & Synthesis Protocol

Pure retrieval pipeline: route to the right notebook -> query it -> synthesize the answer with conversation context -> pause for clarification. Does NOT manage sources, does NOT generate execution plans.

## RULE Q1 - hard gate

- **Every** NotebookLM interaction goes through `nlmq`.
- If a command in your plan starts with bare `nlm `, that command is **invalid** - replace it with the `nlmq` equivalent before running.
- The only permitted direct `nlm` invocations are `nlm login --check` (auth diagnosis, see exit code 2) and `nlm login` itself (only if the check fails and the user agrees).
- Never run `nlm login switch` - it mutates global state for every other consumer of the CLI. Per-call profiles: `nlmq --profile <name>`.
- NEVER run `nlm chat start` - it opens an interactive REPL no agent can control. `nlmq` is synchronous by construction; backgrounding a query with `&` is forbidden.

## Phase 0 - Preconditions

1. `command -v nlmq` must succeed. If it does not, tell the user the `nlmq` shim is missing (it should run `scripts/nlmq.py` in this skill), use the Fallback at the bottom **once**, then stop.
2. No other setup. Notebook IDs are **never** hardcoded, copied from documents, or guessed - `nlmq` resolves them live.

## Phase 1 - Route to a notebook

Pass **domain keywords** as the topic; `nlmq` resolves keyword -> alias -> live notebook ID (order: alias name, routing keyword, exact title, keyword token, title substring):

    nlmq --discover <topic>     # dry run: shows what would be queried, spends no API call

- rc=4 (zero or several matches): run `nlmq --list`, then **ask the user** which notebook. Never guess between candidates.
- `nlmq --list` also shows alias coverage and dangling aliases.

## Phase 2 - Query

    nlmq <topic> "<detailed question>"

**Question formulation rules:**

- Describe the full architecture - state machine structure, RTOS primitives used, thread model, message passing, concurrency controls, data structures, and the exact anti-pattern. Never ask brief or vague questions.
- Include module names, the threads/ISRs involved, and the specific problem. If the codebase has a known flaw, describe it.
- The call is synchronous and blocking; wait for it to finish. Do not run queries in parallel.
- Do NOT interact with sources (add/remove/sync) - the user manages sources himself.

stdout of `nlmq` is the answer text - that is the retrieved material. stderr is provenance (which notebook answered); do not mix it into the answer.

## Phase 3 - Synthesize

Combine two streams into one unified response:

1. **What NLM returned** - the retrieved answer.
2. **What you already know from the conversation** - the user's goal, constraints, prior clarifications.

Weave them together. Do not paste NLM output verbatim; do not ignore the conversation context - the value is the synthesis of both. Bracketed numbers like `[1-5]` inside the answer are unresolvable reference markers in this pipeline: **never expand, explain, or invent what they point to.** NLM handles its own knowledge boundaries - if it does not know, it says so.

## Phase 4 - Clarification

1. Identify what remains ambiguous or partial despite NLM + context.
2. Draft 1-3 clarifying questions for the user.
3. **STOP.** Wait for answers before proceeding.

## Exit codes -> your action

| rc | Meaning | Action |
|----|---------|--------|
| 0 | Answer on stdout | use it |
| 1 | Bad invocation / local config (e.g. routing.json missing) | fix the command; if config is broken, tell the user |
| 2 | nlm/auth/network failure, or the resolved notebook vanished | run `nlm login --check`; report honestly; if "no longer exists", suggest `nlmq --sync-aliases --apply` |
| 3 | rc=0 but malformed/empty answer | retry **once**; then report as a tool failure - do not fabricate an answer |
| 4 | Topic resolved to zero or several notebooks | `nlmq --discover` / `nlmq --list`, then ask the user |
| 5 | Profile name not found | check spelling; ask the user which profile |

## Safety rules (always apply)

1. **Ask the user before ANY delete.** Deletions are irreversible; show what will be deleted and warn about permanent data loss.
2. Re-authenticate only for stale/missing credentials - `unverified` means the probe was inconclusive; check connectivity first.

## Deep troubleshooting

Only after the exit-code table and `nlm login --check` fail to resolve a problem: `reference/nlm_user_guide.md` (CLI internals, auth layers, error catalog).

## Fallback (only while `nlmq` is missing)

Use **once** to unblock, then tell the user to restore the shim (`~/.local/bin/nlmq` -> `scripts/nlmq.py` in this skill). This form cannot resolve topics - take the UUID from `nlm notebook list --json`. `jq -e` is mandatory: bare `jq -r '.answer'` prints the string `null` and exits 0 on API errors, which silently fakes a successful answer.

    nlm notebook query <uuid> "<question>" --json --timeout 180 | jq -er '.answer | select(length > 0)'
