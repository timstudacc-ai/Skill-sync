---
name: code-documentation-style
description: Write, review, or clean up code comments and Doxygen documentation in the user's personal style - WHY-oriented, lean, ownership-aware. Use this skill whenever the user asks to add documentation, document functions, modules or files, write or improve Doxygen blocks, add comments, review or trim existing comments, or remove stale/obsolete comments - even if they just say "document this", "add docs", "comment this file", "clean up the comments", or "make the docs consistent". Also use it before writing any new doc block in this project's C code.
---

# Code Documentation Style

The one-sentence paradigm:

**A comment earns its place by explaining WHY this code exists in exactly this
form - never by restating WHAT the code visibly does.**

Rule of thumb: the function should be self-documenting. Everything the reader
can see by reading the function - its steps, its guard clauses, its visible
behavior - stays out of the comments. Comments explain only why the function
is written, and why it is written this way and not another way.

This style was extracted from the user's actual corrections to AI-drafted
documentation; the draft -> committed pairs below are real.

## Doc block format

- Doxygen block `/** ... */` above the declaration in the `.h`.
  Private/static functions: block above the definition in the `.c`.
- Fields used: `@brief`, `@param`, `@return`, `@note` (in that order).
- In-body comments: `/* ... */` only. Never `//`.
- `@param` describes the role the value plays for this function - what it is
  for, at intent level - not its mechanical layout.

## @brief - intent, one level above the mechanism

State the function's purpose and contract, compressed. Do not enumerate the
internal steps: a step list goes stale the moment the implementation changes,
and the steps are already readable in the body.

**Example (a Wi-Fi module init function):**

- AI draft (step enumeration - rejected):
  `@brief Probe the Wi-Fi module, hard reset it, initialize the component and register the station status callback`
- User's version (intent):
  `@brief Initialize the wifi module with statically provided SSID and PASSWORD`

Notice what the user kept: the *statically provided* part. That is a design
fact (credentials are compile-time constants, not runtime input) - a WHY.
The probe/reset/register sequence is a WHAT, and it vanished.

**Example (a queue send function) - leanness:**

- AI draft: `@brief Enqueue a message, dropping the oldest queued message when the queue is full so the newest data always wins`
- User's version: `@brief Enqueue a message, drop oldest policy`

When a design decision inside the function has a reason, put the reason in
the doc as bare prose, one line per decision:

- AI draft (a socket options function): `@brief Set SO_REUSEADDR plus the send and receive timeouts on the socket`
- User's version:
  ```
  @brief Sets options needed for the broker connection
  REUSEADDR needed to be able to reconnect to the broker without re-creating socket
  Configure timeout (in ms)
  ```

## @note and @return - constraints, quirks, ownership

`@note` is for the non-visible facts a maintainer would otherwise get wrong:

- **ISR-safety as a bare claim.** The user trimmed
  `@note ISR-safe: with a zero timeout the CMSIS port dispatches to the
  FromISR variant in interrupt context` down to just `@note ISR-safe:`.
  The claim is the contract; the mechanism is in the code. Its counterpart:
  `@note Not ISR-safe` - nothing more needed.
- **Ownership and consumers** - who owns this data and who is allowed to
  touch it. This is the single most valuable WHY content. Example (an RTC
  init function, written by the user):
  ```
  @brief Initialize the RTC peripheral not right after the boot, but when
  this function is called
  @note callback fires once upon initialization and sets event flag.
  event flag only ever consumed in the sensor state machine
  ```
  The brief carries the deferral decision (init happens on demand, not at
  boot) and the note carries the data flow (flag -> sensor state machine,
  and nobody else).
- **Driver/API quirks that invert the normal contract** belong in `@return`
  or `@note`, stated as the reason. Kept verbatim by the user (a transport
  send wrapper):
  ```
  @return number of bytes sent, -1 on error (the mx_wifi driver never
  reports a full TCP buffer as 0, so every non-positive return is an error)
  ```
  Mechanism explanations survive HERE - when they document a quirk of
  something you cannot change - and die when they restate your own code.

Drop attribution parentheticals. The user cut "mandatory (HAL requirement)"
to "mandatory": keep the constraint, drop the citation.

Do NOT document what reading the function reveals: idempotent behavior,
guard clauses, call ordering - if the body shows it, the comment duplicates
it. That is the self-documenting rule from the top.

## What stays undocumented

Do not comment things whose names already say them. The user *deleted* the
AI's per-value comments on a `IDLE / OPERATIONAL / RESERVED` state enum
(self-evident) but *kept* them on a `NONE / INIT / CONNECTED` socket-state
enum (a lifecycle where the INIT-vs-CONNECTED distinction is not obvious
from the names). Field-level `<*/` comments only where the name alone would
mislead.

Same rule in bodies: no narration of `if` statements, no restating
assignments.

## In-body comments - the four WHY shapes

The user's own surviving in-body comments fall into four shapes. Write these,
and only these:

1. **Why this branch, and not the obvious alternative** - a flag that is
   deliberately not cleared, because clearing it would make it
   unconsumable for another state after recovery.
2. **Who owns / who consumes** - policy-table rows explaining which thread
   owns a teardown, so no handler is needed for that path, and recovery
   re-runs the whole join.
3. **Vendor quirk / gotcha at the call site** - "a zero return here means
   the address macro is misconfigured"; "polling yield is necessary while
   using a bare-metal driver".
4. **Why the surprising choice is actually safe** - "an error supersedes any
   stale data message, so drain the queue first - the error record is then
   the only message the consumer can read".

## Verify before you write

Ownership and consumer claims ("only ever consumed by X", "owned by Y") must
be confirmed by searching the callers/consumers, never guessed. Read the
function's call sites and the consumers of what it produces before writing
its doc. If ownership cannot be established, document the weaker true fact
instead of inventing a strong one.

## Meaning over polish

Fix a typo in passing when editing that line anyway, but never let polish
inflate a comment. The review question is always "does it carry the WHY,
leanly" - not "is it well written".
