---
name: code-hygiene-audit
description: Use this skill whenever the user wants their changes cleaned up before submitting or after receiving feedback on a pull request — removing leftover debug code, duplicate macros or repeated blocks, dead/commented-out code, redundant #ifdef guards, and other code-clutter that causes a PR to be sent back. Trigger even when it isn't named explicitly — e.g. "clean this up before the PR", "why was this PR rejected", "remove the debug prints", "this has duplicate defines", "tidy this diff", "delete commented-out code", "make this merge-ready". Applies to C, C++, Zephyr/nRF Connect SDK, and any language where leftover code or repeated definitions bloat a contribution.
---

# Code Hygiene Audit

Harden a change for pull-request review by stripping the clutter and redundancy that commonly get a PR **sent back** by maintainers. The goal is a minimal, clean, merge-ready diff that a reviewer can read without wading through debug noise or duplicate logic.

Skip nothing. Every category below is a reason a PR gets rejected, and each produces real, listable findings.

## Finding categories & rules

For each of the following, audit the provided code and report wherever it occurs. Don't fix silently and stop — enumerate what you found so the reviewer/user can verify the intent.

### 1. Duplicate & redundant definitions
- Same macro / `#define` symbol defined more than once (even with identical bodies) — flag the duplicate.
- A `#define` that re-declares a symbol that already exists, or shadows one from a header.
- Multiple identical enum entries, re-declared constants (`const`), or duplicated struct fields with no behavioral difference.
- Redundant helper macros two files define identically instead of sharing one in a common header.

### 2. Dead & commented-out code
- Large commented-out code blocks (`/* ... */` or `// ...` spanning multiple lines) that implement logic instead of explaining it.
- Unreachable branches (`return` followed by code, `if (0)`, `while(0)` stubs, dead `else` arms).
- Unreferenced functions, variables, or constants never used anywhere in the build.
- Stubbed / empty handlers left as placeholders, and `TODO(FIXME)` blocks that aren't tracked in an issue list. A TODO you can't justify keeping becomes an open acceptance question the reviewer has to chase down.

### 3. Debug / scaffolding leftovers
Anything that must never ship:
- Unconditional `printk()`, `printf()`, `LOG_DBG()`, `ESP_LOGE()`-style debug prints (especially at hot-path or ISR priority).
- Temporary logging levels left bumped to DEBUG.
- Hard-coded test values, magic numbers, or forced return values used only to experiment.
- Temporary `k_msleep()`, timeouts, or delays that mask races instead of fixing them.
- Commented-out debug variants of the same call a few lines above the live one.

### 4. Redundant preprocessor structure
- Duplicate or nested `#ifdef` / `#ifndef` guards that add no behavior and just obscure the file.
- `#if 0` blocks, repeated include guards for the same header within one TU.
- Guards that wrap a single `#include` with no conditional need.

## Diagnostic vs. fixing decision

Some findings are **cosmetic** (safe to remove) and some are **behavioral** (removing could change runtime). For each finding classify:

* **CLEAN (safe):** Remove unconditionally — duplicate defines, dead comments, unreferenced symbols, unconditional debug prints, `#if 0`.
* **REQUIRES JUDGMENT:** Holds intent a reviewer must sign off on — commented-out variants, TODO/FIXME blocks, temporary tuning values. Don't delete these automatically; surface them as review items.
* **ESCALATE (do NOT touch):** Debug code that looks temporary but may be load-bearing (e.g., an intentionally kept diagnostic hook for field support), or anything the user hasn't asked you to alter.

## Digging rut / multi-file scope
- If the user supplies a diff (patch) versus a whole file, audit **only the changed region** plus adjacent lines needed to confirm a define is unused or a function has no references. Searching the whole repo is often too slow; search enough to confirm.
- Prefer finding the actual duplicate token once (regex for repeated symbol) over guessing.

## Task
Identify every occurrence of the four categories above in the code or diff the user provides. For each, give:
1. **Location:** file + line (or function).
2. **Category:** which of the 1–4 above.
3. **Verdict & reason:** CLEAN / REQUIRES JUDGMENT / MUST NOT TOUCH, and the one-line why.
4. **Remediation:** the exact edit if safe (a diff snippet); or the review-object card if judgment is needed.

Output a hard-outlined report:

# Code Hygiene Audit Report

## Summary
* **Duplicates found:** [n]
* **Commented-out / dead code items:** [n]
* **Debug leftovers:** [n]
* **Preprocessor cruft:** [n]
* **Merge status:** [CLEAN / NEEDS CLEANUP]

## Findings

1. [Symbol/line] — category, verdict, remediation
2. ...

## Recommended edit (if any)
[Exact diff/fragment of what to delete or merge.]

Do not mutate the file unless the user asked you to apply the cleanup. Default to reporting; apply only on an explicit "clean it" / "apply the fixes".