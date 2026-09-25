---
name: pr-review-rtos
description: Reviews pull requests, diffs, and changed code in this FreeRTOS/STM32 embedded project. Use when the user asks to review a PR, review a diff, check a branch before merge, or audit recent changes. Covers four mandatory passes - RTOS concurrency (thread safety, race conditions, ISR safety), error handling (return codes, asserts), memory management (use-after-free, NULL dereference, double free, leaks), and semantic correctness. Produces a severity-ranked findings report with file:line references and suggested fixes.
---

# PR Review - RTOS Embedded Code

You are reviewing firmware for an STM32U5 + FreeRTOS (CMSIS-RTOS v2) MQTT weather
station. Bugs here do not crash a process - they deadlock a field device no one can
reach. Review with that severity in mind.

## Workflow

1. **Scope the change.** Run `git --no-pager diff <base>...HEAD` (or the PR diff) to
   list changed files. Use `git --no-pager diff --stat` for an overview first.
   Ignore vendored/third-party code (HAL, Drivers/, coreMQTT sources) unless the
   diff itself touches it.
2. **Read full context, not just hunks.** Open every changed file completely with
   read_files. Concurrency and lifetime bugs are invisible in 3-line hunks - you
   must see all tasks/callbacks that touch a variable and all paths that free a
   pointer.
3. **Run the four review passes below in order.** Every pass is mandatory. Do not
   stop after finding problems in one category.
4. **Report** using the output format at the end.

## Pass A - RTOS Concurrency (thread safety, race conditions)

Check every piece of shared state in the diff and ask: *who else can touch this,
and can they touch it while this code is halfway through?*

- **Shared state without synchronization.** Any file-static or global variable,
  struct, or peripheral (I2C bus, UART, socket, EEPROM) accessed from more than one
  task or from both task and ISR context must be guarded by a mutex, queue,
  semaphore, or critical section. Flag bare reads/writes of shared state.
- **ISR-safe API usage.** Code reachable from an interrupt handler must use the
  `...FromISR` variants (`xQueueSendFromISR`, `portYIELD_FROM_ISR`) and must never
  block, printf, malloc, or take a mutex. Trace callbacks (HAL, Wi-Fi driver
  status callbacks) to their calling context and flag blocking calls inside them.
- **Driver context quirks.** The mx_wifi driver can run in bare mode where status
  callbacks execute inside `MX_WIFI_IO_YIELD()` in the *calling* task's context.
  A task that blocks waiting for such an event (e.g., a FreeRTOS task
  notification) removes the only pump that could produce it - flag
  wait-without-pump topologies and self-deadlocks (queue full push from inside
  its own pop callback).
- **Critical-section hygiene.** No blocking calls, logging, or long loops while
  holding a mutex or inside `taskENTER_CRITICAL()`. Flag inconsistent
  lock/unlock pairing and early returns that skip the unlock.
- **Priority & starvation.** Busy-wait/polling loops in high-priority tasks that
  starve lower tasks; unbounded spin loops without timeout.
- **Volatile & reentrancy.** Variables shared with ISR context need `volatile`.
  Non-reentrant library functions (`strtok`, static buffers, `printf`) must not
  be called concurrently from multiple tasks.
## Pass B - Error Handling

- **Every return code gets checked.** `HAL_StatusTypeDef`, `osStatus_t`,
  `MQTTStatus_t`/`MQTTAgentReturnCode_t`, socket `send/recv` results, `int32_t`
  from drivers. An ignored return value is a finding unless failure is provably
  impossible. Watch for checks that test only one of several failure values
  (e.g., socket code checking `ret < 0` but not `ret == 0`, or vice versa when
  both are possible).
- **Error propagation vs. swallowing.** A caught error must either be handled,
  propagated to the caller, or logged-and-continued deliberately. Silent
  `if (err) {}` or `// ignore` without a comment explaining why is a finding.
- **Impossible conditions get asserts.** Preconditions that should never happen
  (NULL for required handles, array indices out of range, state-machine entry
  in wrong state) must be covered with the project's `PRV_ASSERT` - not
  `configASSERT` (which in this project silently hangs) and not a silent early
  return. Conversely, flag asserts on *recoverable* conditions: a network
  timeout is recoverable, a bad pointer is not - do not assert the former.
- **Error-path resource cleanup.** Every early-return/`goto` on error must
  release what was acquired (mutexes, sockets, buffers, command pool entries).
  Missing cleanup on an error path counts in Pass C too.
- **Timeouts.** Any wait (`osDelay`, semaphore take, socket op) without a
  bounded timeout, or a retry loop without a retry limit/backoff, is a finding.
  Also flag `optval = 0`-style mistakes where a zero means "no timeout" rather
  than "no wait".

## Pass C - Memory Management

- **Lifetime.** For every pointer passed to an async API (coreMQTT-Agent
  operations, callbacks, queued messages), verify the pointee outlives the
  operation: static storage, heap-allocated-and-owned-by-recipient, or documented
  copy. Passing stack addresses or objects that may be freed before the async
  operation completes is a Critical finding.
- **Use-after-free / double free.** Track every `vPortFree`/`free`/pool-release
  in the diff: what still references the object afterwards? Is the pointer
  NULLed after free? Can two paths free the same object (error path + normal
  path, retry loops)?
- **Leaks.** Every allocation (`pvPortMalloc`, `malloc`, pool
  `Agent_GetCommand`) must have a matching release on *all* paths, including
  error paths and shutdown/reconnect paths. Flag allocations inside loops
  without a corresponding free.
- **NULL dereference.** Check pointers from: allocation functions (even
  "cannot fail" ones under heap exhaustion), `osXxx`/`xXxx` returns, `NULL`
  network-context members, and function-pointer tables before calling. A
  dereference without a preceding check or an assert documenting the invariant
  is a finding.
- **Buffer bounds.** `memcpy`/`strcpy`/`sprintf` with untrusted or
  size-mismatched lengths; missing `snprintf` bounds; struct copies into
  undersized buffers; queue item sizes matching what is actually queued.
- **Uninitialized reads.** Local structs/buffers used before all fields set
  (e.g., a config struct where one member assignment was forgotten).

## Pass D - Semantic Errors

- **Copy-paste defects.** Duplicated blocks where one line still names the
  *other* variable/option/field (e.g., an `MX_SO_RCVTIMEO` block that sets the
  send option). Compare sibling blocks character by character.
- **Off-by-one / bounds.** Loop bounds, ring-buffer head/tail arithmetic,
  `<=` vs `<`, inclusive/exclusive endpoint confusion, empty/full queue
  conditions.
- **Integer issues.** Signed/unsigned comparisons, `int` truncation of
  `size_t`, overflow in tick arithmetic (use `(now - last)` with unsigned
  wraparound, not `now > last` comparisons), implicit narrowing casts.
- **Units confusion.** `osDelay`/`vTaskDelay` take **ticks**, not milliseconds -
  every delay must either match the configured tick rate or go through
  `pdMS_TO_TICKS()`; `HAL_GetTick()` ms vs FreeRTOS ticks.
- **Logic.** Inverted conditions, operator precedence (`&&`/`||` with `!`),
  missing `break` in switch fallthrough, assignment `=` in condition, dead
  branches, state-machine transitions that skip or loop incorrectly.
- **API misuse.** Wrong enum constants, HAL macros with swapped arguments,
  CMSIS-RTOS v1 vs v2 API mixups (the project uses v2: `osThreadNew`, not
  `osThreadCreate`).

## Output Format

Start with a one-paragraph summary of what the change does and an overall
verdict. Then a findings table, ordered by severity:

| # | Severity | Category | Location (file:line) | Finding | Suggested fix |

Severity levels:
- **Critical** - deadlock, race on shared state, use-after-free, async lifetime
  bug, unbounded blocking. Blocks merge.
- **High** - unchecked return code on a realistic failure path, leak, NULL deref
  on a plausible path, missing assert on a documented invariant.
- **Medium** - cleanup missing on an unlikely error path, missing timeout,
  unit mismatch, minor integer issue.
- **Low / Nit** - style, dead code, overly defensive checks, assert on a
  recoverable condition.

Rules:
- Cite exact `file:line` for every finding, from the actual files, not the diff.
- Every Critical/High finding must include a concrete suggested fix or a
  question the author must answer.
- If you cannot decide whether something is safe (e.g., "is this variable also
  touched by the ISR?"), check the code until you can - an unresolved "maybe"
  must be listed as a question in a separate "Open questions" section, not
  silently dropped.
- Do not pad the report. If a pass finds nothing, say so in one line.
- End with the verdict: **Approve**, **Approve with comments**, or **Request
  changes** (any Critical, or three or more High findings).
