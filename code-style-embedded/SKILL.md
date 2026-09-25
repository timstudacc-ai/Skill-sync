---
name: code-style-embedded
description: Enforces this project's C coding style when writing, editing, restyling, or checking user-written firmware code (Src/, Inc/, Src/prv_* modules). Use when creating new source/header files, writing new functions, restyling existing files, or verifying naming and formatting conventions. Core rules - snake_case identifiers, banner section comments, prv_ prefix for private items - plus a mandatory step to ask the user about additional styling preferences before applying conventions not covered here. Never reformats HAL/CMSIS/coreMQTT vendor code.
---

# Code Style - prv_ Module Conventions

These rules apply ONLY to user-written code: everything under `Src/`, `Inc/`,
and especially the private modules (`Src/prv_*/`, `Inc/prv_*/`). NEVER apply
these rules - and never "fix" formatting - in vendor code (`Drivers/`,
`Middlewares/`, `Drivers/coreMQTT-AGENT/` sources). Vendor files keep their
own house style.

## Step 0 - Ask before assuming

Before styling any file or writing new code that involves a convention NOT
covered below (comment style for functions, magic-number policy, line-length
limits, `const` placement, include ordering, etc.), ASK THE USER how they
want it done. Do not invent a rule silently. Once the user answers, follow
it for the rest of the session and suggest adding it to this skill file so
it becomes permanent.

When the user says "make it look like the rest of the project" without
naming a rule, default to what the existing prv_ modules actually do
(observed conventions listed below), not generic C style.

## Rule 1 - snake_case everywhere (user-written identifiers)

- **Functions, variables, struct/typedef names, file names:** `snake_case`
  (`prv_logger_init`, `mqtt_buf`, `prv_mqtt.c`). No camelCase, no PascalCase
  for anything the user writes. Flag and rename on sight.
- **Macros and constant #defines:** `ALL_CAPS` with underscores
  (`PRV_MQTT_RX_BUF_SIZE`, `MQTT_BUFFER_SIZE`). Align macro value columns
  within a block using spaces, as done in `prv_mqtt.h`.
- **Type definitions:** end in `_t` (`msg_queue_ctx_t`, `prv_mqtt_ctx_t`).
- **Privilege prefixes (project convention):**
  - `prv_` prefix for file-private items: `static` functions, file-static
    variables, and a module's private helpers (`prv_uart_mutex`,
    `prv_mqtt_init`).
  - No prefix needed for genuinely public API functions exposed through a
    header (`get_mqtt_ctx`).
  - Private module files: `prv_<module>.c/.h`.
- **Exceptions - do not rename:** HAL, CMSIS, FreeRTOS and library
  types/functions keep their own names (`huart1`, `xSemaphoreTake`,
  `HAL_UART_Transmit`). The project must still call them as-is; a camelCase
  name in vendor code is not a style violation.

## Rule 2 - Banner section comments

Every user-written `.c` file is organized into sections separated by this
exact banner format (74 `=` characters between `/* ` and ` */`):

```c
/* ========================================================================= */
/* PRIVATE VARIABLES*/
/* ========================================================================= */
static SemaphoreHandle_t prv_uart_mutex = NULL;
static StaticSemaphore_t prv_uart_mutex_buf;

/* ========================================================================= */
/* PUBLIC FUNCTIONS*/
/* ========================================================================= */
```

- The title line has NO space before `*/`: `/* PUBLIC FUNCTIONS*/`, not
  `/* PUBLIC FUNCTIONS */`.
- One blank line between the closing banner and the first item, and one
  blank line after the last item of a section before the next banner.
- Canonical section order in a `.c` file (include only sections the file
  actually has, in this order):
  1. `INCLUDES` - all #include directives.
  2. `PRIVATE MACROS AND CONSTANTS` - file-local #define blocks.
  3. `PRIVATE TYPEDEFS` - private structs/enums/typedefs.
  4. `PRIVATE VARIABLES` - file-static variables.
  5. `PRIVATE FUNCTION PROTOTYPES` - forward declarations for static
     functions.
  6. `PUBLIC FUNCTIONS` - externally visible functions.
  7. `PRIVATE FUNCTIONS` - static helpers, after the public ones.
- In headers, use the same banners for the sections that make sense
  (`INCLUDES`, `MACROS`, `TYPEDEFS`, `PUBLIC FUNCTIONS` prototypes).

## Observed conventions (defaults when the user does not specify)

Derived from the existing user modules (`Src/prv_logs/prv_logs.c`,
`Src/prv_mqtt/prv_mqtt.c/.h`) - match them unless the user says otherwise:

- **File header block** at the top of every user file:

  ```c
  /*
   * prv_mqtt.h
   *
   *  Created on: Sep 18, 2026
   *      Author: user
   */
  ```

- **Braces:** function bodies open the brace on its own line (Allman);
  control-flow statements keep the brace on the same line:
  `if (...) {` ... `}`.
- **Indentation:** 4 spaces, no tabs.
- **Include guards** in headers: `#ifndef PRV_MQTT_H_` / `#define PRV_MQTT_H_`
  derived from the file name (upper snake, `_H_` suffix), with the matching
  `#endif /* PRV_MQTT_H_ */` comment.
- **Includes:** system headers first, then project/vendor headers, each in
  its own `#include` line; optional `/* Group comment. */` lines between
  groups (`/* Kernel includes. */`, `/* MQTT agent include. */`).
- **Struct member alignment:** align member names in a column within a
  typedef (spaces), as in `prv_mqtt_ctx_t`.
- **Comments:** `/* ... */` style, placed on the line above the code, or
  trailing for short notes (`/* Give semaphore in case of failure*/`).
- **NULL initialization:** file-static pointers initialized to `NULL` at
  declaration (`static SemaphoreHandle_t prv_uart_mutex = NULL;`).

## Applying the skill

- **New files:** build them from the layout above from the start (header
  block, banners, guard, section order).
- **Existing files:** follow the style already used in that file; if it
  deviates from this skill and the user asks for a styling pass, restructure
  it into the banner sections and rename to snake_case, but do not change
  any code behavior while styling.
- **Styling reports:** when asked to *check* style, list violations as
  a table (file:line, rule, current, suggested) - do not silently edit.
- **Scope guard:** if the file is vendor code, stop and say so instead of
  restyling it.
