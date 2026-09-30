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
Follow the classic structure (see `references/forum_post_example.md` for a worked real-world example):
1. **Title** — specific, searchable. "MX_WIFI_Socket_setsockopt fails with MX_SO_BLOCKMODE on EMW3080" beats "Wi-Fi not working".
2. **Context** — one or two sentences: what you're building, on what hardware/software.
3. **Symptom** — the precise failure: what call, what input, what return value/error, immediately.
4. **Steps to reproduce** — numbered, minimal.
5. **Minimal reproducible code** — smallest code that shows the failure; mark the exact failing line with a comment. Include code only when it adds clarity.
6. **Environment notes** — versions, abstractions in use, anything unusual about the setup (and why).
7. **Workaround status** — what you're doing meanwhile; this tells responders you've already isolated it.
8. **Why it matters** — the downstream goal (e.g. "needed for coreMQTT agent non-blocking I/O").
9. **The question** — end with an explicit, open question addressed to people who may have hit the same thing.

Formatting rules:
- Markdown, with fenced code blocks and inline code for all identifiers.
- Keep it as short as the content allows; cut anything that doesn't help reproduction.
- For GitHub issues: map content onto the repo's template fields verbatim, fill every required field.
- Include the repo/version link(s) so responders can check the exact code.

### 4. Present and refine
Show the draft, list the assumptions you made, and note what the user should verify or fill in (versions, serial numbers of boards, etc.) before posting.

## Reference material

- `references/forum_post_example.md` — real, successful ST Community post (MXCHIP Wi-Fi non-blocking socket bug). Use as the gold-standard structure and tone.
- `references/CONTRIBUTING.md` — STMicroelectronics stm32-mx-wifi contributing guide: pre-issue checklist (latest commit, no duplicate, not a vulnerability, on-topic), CLA notes, and the ST Community link for off-topic support.
- `references/issue_templates/` — ST's GitHub issue templates:
  - `bug_report.yml` — summary / detailed description / expected vs actual / environment / severity (Critical–Minor).
  - `question.yml` — summary / detailed description.
  - `feature_request.yml` — summary / details / use case.
  - `config.yml` — shows the security-vulnerability and support-request contact links (don't file bugs for vulnerabilities; use SECURITY.md).

These are the canonical ST templates, but the repo-agnostic rule stands: when posting to any other repo, check and use THAT repo's templates if they exist.
