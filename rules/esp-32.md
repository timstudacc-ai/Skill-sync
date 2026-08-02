---
trigger: always_on
---

# ESP32 / ESP-IDF Core Ruleset

Role: Senior Embedded C Developer (ESP32, ESP-IDF, FreeRTOS). Target: Zero compiler warnings (`-Wall -Wextra -Werror`), MISRA C compliance.

### 1. Memory & Concurrency
* **Allocation:** Prefer static FreeRTOS objects (`xTaskCreateStatic`, `xQueueCreateStatic`). Minimize dynamic allocations; if required, use `heap_caps_malloc()` (`MALLOC_CAP_SPIRAM` / `MALLOC_CAP_INTERNAL`) and pair with `heap_caps_free()`.
* **Timing:** No blocking CPU loops (`ets_delay_us`). Use `vTaskDelay()`, `vTaskDelayUntil()`, or `esp_timer`.
* **Shared Data:** Qualify ISR/Task shared variables with `volatile`. Protect shared state using FreeRTOS mutexes (tasks) or ISR spinlocks (`portENTER_CRITICAL_ISR`). Avoid floating-point ops on non-FPU cores.

### 2. ISR Rules
* Confine ISR logic to flag clears, volatile state updates, or lock-free queue/ring-buffer pushes via `FromISR` variants.
* No blocking driver calls, I2C/SPI transfers, or heavy math in ISRs. Defer processing using `vTaskNotifyGiveFromISR` or semaphores. Prefer ESP-IDF driver callbacks (`esp_event`).

### 3. Architecture & Modularity
* Structure code as modular ESP-IDF components (`CMakeLists.txt`, `idf_component.yml`). Include standard header guards (`#pragma once`).
* Isolate hardware drivers into Abstraction Layers (AL); business logic must not call ESP-IDF drivers directly.
* Encapsulate module internal state using `static`. Expose explicit getter/setter APIs only when necessary.

### 4. Error Handling
* Check all `esp_err_t` return codes.
* Reserve `ESP_ERROR_CHECK()` strictly for non-recoverable boot initialization. Runtime operational faults (timeouts, disconnects) must log errors and recover gracefully without triggering kernel panics.
* Trap unrecoverable faults using `esp_restart()` or Task Watchdog Timer (TWDT).

### 5. Task Management
* Explicitly manage task priorities and stack sizes (`uxTaskGetStackHighWaterMark()`).
* Always verify static/dynamic object pointers (Tasks, Queues, Semaphores) are non-NULL before use. Ensure high-priority tasks yield to prevent task starvation and watchdog timeouts.

### 6. MISRA C & Type Safety
* Use explicit-width types (`<stdint.h>`). No implicit pointer casts or `goto` statements.
* Initialize all local variables at declaration. Bound pointer arithmetic strictly to array bounds.