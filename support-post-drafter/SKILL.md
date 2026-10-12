---
name: support-post-drafter
description: Drafts high-quality forum posts and GitHub issues/bug reports when the user needs to ask for help with a software/firmware problem. Actively investigates the problem (repo, docs, source code), then produces a well-structured Markdown post following the target repo's issue templates or forum conventions, including root-cause hypotheses and minimal reproducible code. Use when the user wants to "post an issue", "ask on the forum", "file a bug", or "ask a question about a library/driver".
---

# Support Post Drafter

Help the user write posts to forums and GitHub issues that get answered. A good support post does three things: makes the problem trivially reproducible, shows the author did their homework, and gives responders concrete hooks to latch onto. Your job is to build all three from whatever the user gives you — often just a vague description of the symptom.

## Workflow

### 1. Gather context
Collect from the user (or infer, flagging anything you assume):
- The exact symptom and error message(s) — verbatim, not paraphrased.
- Hardware/software environment: board/MCU, OS/RTOS, toolchain, library version or commit hash.
- Steps to reproduce, and what "expected vs actual" behavior is.
- Where the post is going: a GitHub repo with issue templates, a vendor forum (e.g. ST Community), etc.

If information is missing, ask before writing. Never invent version numbers or error messages.

### 2. Investigate before writing
For bug reports, dig in rather than just reformatting the user's description:
- Look at the target repo's source/docs (search or fetch it) for the API or code path involved.
- Check whether the target repo has issue templates in `.github/ISSUE_TEMPLATE/` and follow them exactly (field names, title prefixes like `[Bug]:`).
- Check open AND closed issues for duplicates — repos like ST's explicitly require this before posting.
- Form precise root-cause hypotheses grounded in evidence (specific source files, code lines, docs, firmware constraints). E.g. "this config option may be unimplemented in this component's firmware" — only when you can point to supporting evidence. If you can't find evidence, ask the community openly instead.

### 3. Draft the post

Write it as a **continuous, first-person narrative** — one engineer describing a problem to
another, not a form being filled in. A reader should be able to go top to bottom as a story:
what I built, what goes wrong, what I already ruled out, what I suspect, and what I am asking.
`references/forum_post_example.md` is the shape to imitate: a greeting, a couple of paragraphs
of context and symptom, one small numbered repro block, a code block, a short closing
paragraph, and one explicit question.

Think of the content as a sequence of movements, not a set of titled sections:
- **Title** — specific and searchable. "MX_WIFI_Socket_setsockopt fails with MX_SO_BLOCKMODE on EMW3080" beats "Wi-Fi not working".
- **Opening** — a greeting, what you are building and on what hardware/software, and the precise symptom, ideally within the same paragraph or two. Say what call, what input, what return value, what you observed.
- **Evidence** — what you already checked and ruled out, in prose. This is what earns answers: it proves the obvious causes are off the table. Name what is provably working and why (e.g. "it reads correctly at cold boot, so addressing and calibration are fine").
- **Configuration / minimal reproducible code** — a fenced code block, only if it adds clarity; the smallest snippet that shows the setup or the failure, with the failing line marked by a comment.
- **Hypotheses** — a short paragraph of reasoning. State what you believe and why, and say plainly when a hypothesis does not fit the evidence.
- **The question** — close with one explicit, open question addressed to the people reading. Place the repro steps and environment lines near it where the forum expects them.

**Voice rules — this is where drafts usually go wrong:**
- **Default to paragraphs.** Prefer connected sentences over lists; a wall of bullets reads like a bug-report template and gets skimmed. Reserve a numbered list for genuinely sequential steps to reproduce, and plain bullets only for parallel one-liners (environment/version lines, a set of options) that read worse in prose.
- **Do not scaffold the post with headings** such as "Context", "Symptom", "What I have already verified", "My current hypotheses", "Questions". Let the flow carry the reader; add a heading only if the target forum's format demands one.
- **First person, plain words, ordinary sentence length.** Write "I am seeing X when I do Y", not "The following issue is observed". Admit uncertainty instead of hedging.
- **Keep concrete detail inline.** Register addresses, hex values, error codes and function names belong inside the sentence (inline code), not in a table or a fact sheet.
- **Be brief, but keep the story complete.** Cut anything that does not help someone reproduce or reason about the problem.

**Before / after (same content, different feel):**

Over-structured — do not produce this:
> **Symptom** - Temperature reads high.
> **What I have already verified** - Conversion formula is correct; heater is disabled.
> **My current hypotheses** - 1. Board self-heating. 2. Stale one-shot data.
> **Questions** - Has anyone encountered this?

Human — produce this:
> Hi, I have an application running on the B-U585I-IOT02A (STM32U585, FreeRTOS). The onboard HTS221 reports ~20 °C right after reset, but over the next few minutes the reading rises steadily and settles near 30 °C while the room stays at ~20 °C. The drift is smooth and monotonic, which looks thermal rather than electrical. I have already checked the driver's conversion against the datasheet and it is correct, and the sensor's internal heater is disabled. My guess is that something on the board is heating up around the sensor. Has anyone seen this, or is it a known behaviour?

Formatting rules:
- Markdown, with fenced code blocks and inline code for all identifiers.
- For GitHub issues: the repo template fields override the flow above — map the same narrative content onto the required fields and fill every one.
- Include the repo/version link(s) so responders can check the exact code.

### 4. Present and refine
Show the draft, list the assumptions you made, and note what the user should verify or fill in (versions, serial numbers of boards, etc.) before posting.

## Reference material

- `references/forum_post_example.md` — real, successful ST Community post (MXCHIP Wi-Fi non-blocking socket bug). It is prose-first with minimal structure: use it as the gold-standard **flow and tone**, not as a heading checklist to replicate.
- `references/CONTRIBUTING.md` — STMicroelectronics stm32-mx-wifi contributing guide: pre-issue checklist (latest commit, no duplicate, not a vulnerability, on-topic), CLA notes, and the ST Community link for off-topic support.
- `references/issue_templates/` — ST's GitHub issue templates:
  - `bug_report.yml` — summary / detailed description / expected vs actual / environment / severity (Critical–Minor).
  - `question.yml` — summary / detailed description.
  - `feature_request.yml` — summary / details / use case.
  - `config.yml` — shows the security-vulnerability and support-request contact links (don't file bugs for vulnerabilities; use SECURITY.md).

These are the canonical ST templates, but the repo-agnostic rule stands: when posting to any other repo, check and use THAT repo's templates if they exist.
