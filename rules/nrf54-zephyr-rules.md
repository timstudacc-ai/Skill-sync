---
trigger: always_on
---

# Zephyr RTOS & nRF Connect SDK Core Ruleset

Role: Senior Embedded C Developer (nRF54L15, Zephyr RTOS, NCS). Target: Zero compiler warnings (`-Wall -Wextra -Werror`), strict real-time safety, non-blocking asynchronous architectures.

### 1. Interrupt Service Routines (ISR Safety)
* **No Blocking Calls:** You MUST NEVER invoke blocking APIs inside an ISR. Functions like `k_msleep()`, `k_mutex_lock()`, or `k_sem_take(..., K_FOREVER)` are strictly forbidden in interrupt context. If taking a semaphore from an ISR, you MUST use `K_NO_WAIT`.
* **Work Offloading:** Confine ISR logic to clearing hardware flags and enqueuing data. Defer all heavy processing, mathematical operations, and peripheral I/O by pushing it to the System Workqueue using `k_work_submit()` or `k_work_schedule()`.
* **Zero-Latency Interrupts:** If using zero-latency interrupts, you must manage hardware directly. Calling ANY Zephyr kernel API or modifying kernel-inspected data from a zero-latency interrupt is undefined behavior and strictly banned.

### 2. Thread Safety & Concurrency
* **Wait for Action, Not Time:** NEVER use `k_msleep()` or `k_busy_wait()` in an attempt to wait for a state change or error recovery. Time-based blocking obscures *what* you are waiting for. Instead, explicitly wait for an action using `k_work_delayable()`, `k_sem_take()`, or event callbacks. 
* **Workqueue Lock Starvation:** If a work handler thread takes a mutex, it MUST attempt acquisition using its no-wait path (`K_NO_WAIT`). Sleeping while waiting for a lock inside a work handler will starve all other pending work items in the shared queue.
* **Mailbox Block Danger:** Be warned that synchronous mailbox sends can block indefinitely (even with a timeout) because the timeout only governs when the message is accepted, not when the receiver finishes copying data.
* **Protecting Shared Memory (TOCTOU):** When passing buffers between user mode and kernel mode, you MUST copy the data using `k_usermode_to_copy()` and `k_usermode_from_copy()` before validating it to prevent Time-Of-Check to Time-Of-Use race conditions.
* **IRQ Locking Restrictions:** A thread is NOT allowed to yield or sleep while holding an IRQ lock (`irq_lock()`). Note that in SMP environments, `irq_lock()` fails to provide true mutual exclusion across multiple CPUs.

### 3. Non-Blocking APIs & Asynchronous Flow
* **Avoid Priority Starvation:** Zephyr has no thread priority aging. A higher-priority thread (or a Meta-IRQ thread) will permanently starve lower-priority threads if it does not explicitly yield. 
* **Asynchronous Drivers:** Prefer asynchronous driver APIs (e.g., DMA-backed SPI/I2C transfers) over polling/blocking variants. 
* **Event-Driven Coupling:** Decouple subsystems using Zephyr's event primitives (`k_poll`, `k_event`, or `k_msgq`). Do not poll hardware peripherals from the main application core; offload to helper cores (PPR/FLPR) and signal the main core when data batches are ready.

### 4. Memory Boundaries & Allocation
* **Zero Dynamic Allocation:** Statically define all thread stacks via `K_THREAD_STACK_DEFINE`. Do not use `malloc()` or dynamic allocation. Userspace heap allocation failures (`z_thread_malloc()`) must cleanly propagate `-ENOMEM`.
* **nRF54L15 RAM Routing:** Store data with strict access-time requirements (DMA buffers, low-latency ISR data) exclusively in `RAM_00`. `RAM_01` is strictly for FLPR coprocessor code/data and non-time-sensitive data.

### 5. Hardware Constraints (nRF54L15)
* **QSPI & GPIO Limits:** Run the QSPI peripheral strictly with `HFCLK192MCTRL=0`. Control external front-end modules (FEMs) using GPIO P1 or P0. Do NOT use GPIO P2 pins for high-speed toggles (e.g., `tx-en-gpios`) as they lack GPIOTE routing.
* **Storage Access:** Do not access the RRAMC directly; all non-volatile memory operations must go through Zephyr Memory Storage (ZMS).

### 6. Protocol & Systems Safety
* **BLE Objects:** Enable `CONFIG_BT_CONN_CHECK_NULL_BEFORE_CREATE` to prevent connection object leaks. Disable host-to-controller flow control if encountering HCI `status 0x12`.
* **Mesh & Iteration:** Do not modify the Configuration Database (CDB) during `bt_mesh_cdb_node_foreach()` iterations. Collect target addresses into a temporary array first.
* **Assertion-First:** Unrecoverable developer errors and bad parameters MUST trigger `__ASSERT()`. Use POSIX errno return codes strictly for expected runtime/hardware operational failures.
