---
name: error-and-null-checks
description: Use this skill whenever the user wants error checks, error handling, NULL checks, null-pointer guards, argument/pointer validation, or defensive checks added to code. Trigger even when they don't name it explicitly — e.g. "add error checks", "guard the pointers", "check for errors", "make this crash-proof", "harden this function", "validate inputs", "add defensive checks". Applies whenever code calls functions that return error codes or when a function accepts pointer arguments that must not be NULL.
---

# Error Checks & NULL Guards

Apply error checks and NULL checks to the code the user provides. The goal is to catch failures early and fail loudly and predictably instead of letting an ignored error code or a NULL pointer crash the program.

Everywhere the user has code that could fail, guard it.

## Error-check pattern

Any call to a function that returns an error code must have its return value checked. Follow this template:

```c
int err;                 /* 1. declare the error variable */
err = func_call(...);   /* 2. capture the return code      */
if (err) {              /* 3. non-zero means it failed     */
  /* log error */       /* 4. log so the failure is visible */
  return err;           /* 5. propagate it to the caller    */
}
```

Notes:
- Prefer declaring at first use inline: `int err = func_call(...);`.
- Test only the truthiness of the error; don't compare against a "success" spelling unless the API documents success as that specific value.
- The negative-`errno` convention is standard in Zephyr/Linux code: propagate the value unchanged with `return err;`.

## NULL-check pattern

Any pointer the function receives may be NULL, so guard every pointer parameter against NULL before it is first used (dereferenced):

```c
int do_thing(struct device *dev, struct sample *s) {
  if (dev == NULL || s == NULL) {   /* guard all pointer args up front */
    LOG_ERR("do_thing: NULL argument");
    return -EINVAL;
  }
  /* ... safe to use dev and s now ... */
}
```

Guidance:
- Check **all** pointer parameters together in one guard near the top of the function, before any is dereferenced.
- Combine with other preconditions naturally: `if (!conn || handle == 0 || !rumble)`.
- Return a negative `errno` such as `-EINVAL` for a failed pointer check, not a bare `0`.
- Also guard function-callback pointers inside a struct before calling through them, e.g. `if (cb && cb->write_complete)`.
- Guard pointer values returned from other calls (allocation results, lookups) before using them too.

## Logging

Use the logging the surrounding codebase already uses — Zephyr `LOG_ERR` / `LOG_WRN`, `ESP_LOGE`, `printf`, etc. Include enough context to locate the failure: function name, the error value, or which argument/pointer was NULL.

## Task

Apply both patterns to the code the user gives you: add an error check for every call that can fail, add a NULL check for every pointer parameter before it is used, log meaningfully, and propagate errors using the project's established conventions.
