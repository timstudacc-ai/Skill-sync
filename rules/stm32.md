---
trigger: always_on
---

# STM32 / HAL Core Ruleset

Role: Autonomous Embedded C Developer (STM32, STM32CubeHAL, FreeRTOS, PlatformIO). Target: Zero compiler warnings (`-Wall -Wextra -Werror`), MISRA C compliance.

### 1. Memory & Concurrency
* **Zero Dynamic Allocation:** `malloc`, `calloc`, `realloc`, and `free` are strictly forbidden. Statically allocate all buffers, structures, and RTOS objects at compile time.
* **Non-Blocking Timing:** No `HAL_Delay()` outside initial hardware boot. Use non-blocking state machines driven by `HAL_GetTick()`, hardware timers, or RTOS primitives.
* **Shared Memory:** Qualify shared ISR/Task variables with `volatile`. Wrap critical section read-modify-write operations in interrupt masks (`__disable_irq()` / `__enable_irq()`) or RTOS mutexes. Avoid floating-point ops on non-FPU cores.

### 2. ISR Rules
* Keep ISR latency minimal: clear flags, set volatile state flags, or push/pop to lock-free ring buffers.
* No blocking HAL calls (`HAL_UART_Transmit`, `HAL_I2C_Master_Receive`) inside ISRs; use interrupt (`_IT`) or DMA (`_DMA`) variants.
* Defer heavy data parsing or math out of ISR context into the main super-loop or an unblocked RTOS task.

### 3. Architecture & Modularity
* **CubeMX Code Preservation:** Place all custom application code strictly inside `/* USER CODE BEGIN ... */` and `/* USER CODE END ... */` blocks.
* Separate business/math logic from STM32 HAL driver calls via Hardware Abstraction Layers (AL). Generate complete `.c`/`.h` pairs with header guards (`#ifndef`).
* Encapsulate module variables using `static`. Expose explicit getter/setter APIs only when necessary.

### 4. Error Handling
* Evaluate return codes for all STM32CubeHAL calls (`HAL_StatusTypeDef`).
* Handle runtime timeouts and communication errors gracefully; trap fatal unrecoverable errors in `Error_Handler()` (disable actuators, infinite loop awaiting TWDT reset).

### 5. MISRA C & Type Safety
* Use explicit-width integer types (`<stdint.h>`). No implicit pointer casts or `goto` statements.
* Initialize all local variables at declaration. Bound pointer arithmetic strictly to array bounds.