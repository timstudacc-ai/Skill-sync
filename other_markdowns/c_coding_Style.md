Portable Embedded C (C23) Guidelines
Language: C

1. Commenting & Documentation
Do not add long code comments (more than two lines).

Do not add comments inside functions; the code should be self-documenting.

Only add short @brief Doxygen documentation above functions you create.

Never add inline comments unless specifically requested.

Doxygen Template:

C
in my_header.h file
/**
 * @brief 
 * @param 
 * @return 
 * @note (if needed)
 */
err_t my_func(void);
Inline Comment Example:

WRONG:

C
/*
 * Thousands of lines of redundant comments bla bla bla
 */
one_func_call();
RIGHT:

C
one_func_call();
2. Standard & Memory Allocation
Language Standard: ISO C23 (-std=c23).

Memory: 100% static or caller-allocated. malloc, calloc, realloc, and free are prohibited.

3. Types
Use only <stdint.h> fixed-width types (uint8_t, int32_t, etc.).

Use <stdbool.h> (bool, true, false).

Do NOT use int, short, long, or unsigned.

4. Naming Conventions
Variables and arguments: snake_case

Functions: module_verb_noun()

Types and structs: snake_case_t

Constants and macros: UPPER_SNAKE_CASE

5. Pointer Null Checks
Valid: if (ptr)

Null: if (!ptr)

Prohibited: Do NOT use == NULL or != NULL.

6. Error Handling
Status return type: err_t (0 = OK, non-zero = error).

Early Return Pattern:

C
err_t ret = OK;
ret = sub_function();
if (ret) {
    return ret;
}