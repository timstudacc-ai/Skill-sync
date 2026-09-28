---
name: stm32-freertos-developer
description: STM32 + FreeRTOS embedded development expert. Supports the full Cortex-M family, native FreeRTOS v10+ and the CMSIS-RTOS v2 API. Used for creating tasks/queues/semaphores, integrating the standard library + HAL peripherals, memory optimization, low-power Tickless mode, STM32CubeMX configuration, and debug analysis (SEGGER SystemView / Percep TRACEalyzer).
---

# STM32 + FreeRTOS Embedded Development Expert

## Rules for AI Usage

When the user makes a request, **selectively read** documents according to the rules below. Do not read all documents at once; read only the files relevant to the user's request.

### Code Generation Requests

| The user says... | Read file |
|-----------|----------|
| "create a task" / "create a queue" / "semaphore" / "mutex" / "event group" / "task notification" | EXAMPLES/BASIC.md |
| "UART driver" / "ADC driver" / "I2C driver" / "TIM driver" | REFERENCE/HAL_DRIVERS.md + EXAMPLES/DRIVERS.md |
| "printf redirect" / "printf output" / "ITM" | REFERENCE/STD_LIBS.md |
| "DMA receive" / "variable-length data" | REFERENCE/HAL_DRIVERS.md + EXAMPLES/DRIVERS.md |

### Code Review / Troubleshooting Requests

| The user says... | Read file |
|-----------|----------|
| "interrupt" / "FromISR" / "portYIELD_FROM_ISR" / "priority configuration" | PATTERNS/INTERRUPT.md |
| "deadlock" / "priority inversion" / "stack overflow" / "resource leak" | PATTERNS/TRAPS.md |
| "producer-consumer" / "state machine" / "resource pool" / "publish-subscribe" | PATTERNS/DESIGN.md |

### Debug Requests

| The user says... | Read file |
|-----------|----------|
| "SystemView" / "TRACEalyzer" / "trace analysis" | REFERENCE/DEBUG_TOOLS.md |
| "task statistics" / "stack monitoring" / "CPU usage" | REFERENCE/DEBUG_TOOLS.md |

### Advanced Application Requests

| The user says... | Read file |
|-----------|----------|
| "low power" / "Tickless" / "STOP mode" | EXAMPLES/ADVANCED.md |
| "CubeMX configuration" / "STM32CubeMX" | EXAMPLES/ADVANCED.md |
| "sensor fusion" / "multitasking" | EXAMPLES/ADVANCED.md |

### API Lookup Requests

| The user says... | Read file |
|-----------|----------|
| "xTaskCreate parameters" / "API syntax" / "function description" | REFERENCE/FREERTOS_API.md |

### How to Use

If the user's request is not clear enough to decide which file to read:
1. Read SKILL.md and REFERENCE/FREERTOS_API.md first
2. Ask the user about the specific requirement
3. Read the correct file based on the answer

**Do not read all files at once! Read only the files relevant to the user's request.**

---

## Skill Overview

This skill is designed for embedded development using the **FreeRTOS real-time operating system** on **STM32 microcontrollers**. The AI acts as an "embedded systems architect" and helps you write safe, efficient and maintainable C code.

**Applicable scenarios:**
- Projects generated with STM32CubeMX
- The full ARM Cortex-M family (F0/F1/F3/F4/F7/H7/G0/L0/L4/L5, etc.)
- FreeRTOS v10+ versions
- Native FreeRTOS API or CMSIS-RTOS v2 API

---

## Use Cases

### Code Generation
- Create tasks, queues, semaphores, mutexes
- Write peripheral driver templates (UART DMA, ADC DMA, I2C, etc.)
- Configure low-power Tickless mode
- Implement printf redirection (ITM_SendChar / UART)

### Code Review
- Analyze whether the task priority configuration is reasonable
- Check the correctness of interrupt-to-task interaction
- Troubleshoot deadlocks, priority inversion, resource leaks
- Validate the FreeRTOSConfig.h configuration

### Teaching and Tutoring
- Explain core FreeRTOS concepts (task scheduling, context switching)
- Demonstrate design patterns such as producer-consumer and publish-subscribe
- Guide the use of debugging tools (SEGGER SystemView, TRACEalyzer)

---

## Core Capability Modules

### Task Management
- Create static/dynamic tasks (`xTaskCreate`, `xTaskCreateStatic`)
- Set priority, stack size, task name
- Task state monitoring (`uxTaskGetStackHighWaterMark`)

### Inter-Task Communication
- **Queue**: producer-consumer model
- **Semaphore**: binary/counting
- **Mutex**: avoid race conditions, includes priority inheritance
- **Event Groups**: waiting for multiple conditions
- **Task Notifications**: lightweight alternative

### Interrupt and Task Interaction
- Use `xQueueSendFromISR` / `vTaskNotifyGiveFromISR` in HAL callbacks
- Never block in an ISR, only send notifications
- Usage of `portYIELD_FROM_ISR(xHigherPriorityTaskWoken)`

### Peripheral Integration
- **UART DMA + queue**: variable-length data reception (IDLE interrupt)
- **ADC DMA + task notification**: continuous sampling
- **I2C master/slave mode**: sensor communication
- **TIM timer/PWM**: periodic tasks

### Memory and Performance Optimization
- Static allocation is recommended (avoids heap fragmentation)
- Estimate stack size reasonably
- Enable `configASSERT()` and `configCHECK_FOR_STACK_OVERFLOW`
- Use `configUSE_PREEMPTION = 1` to improve real-time behaviour

### Debugging and Diagnostics
- Generate task list printing code (`vTaskList`)
- SEGGER SystemView (Keil/IAR environment)
- Percep TRACEalyzer (FreeRTOS environment)
- ITM/SWO configuration and printf debugging

---

## File Index

| Type | File | Description |
|------|------|------|
| Main file | SKILL.md | The only file the AI reads automatically |
| User guide | USER_GUIDE.md | For the user only, not read |
| API reference | REFERENCE/FREERTOS_API.md | FreeRTOS API syntax |
| API reference | REFERENCE/STD_LIBS.md | Standard library integration |
| API reference | REFERENCE/HAL_DRIVERS.md | HAL peripheral drivers |
| API reference | REFERENCE/DEBUG_TOOLS.md | Debug tool configuration |
| Code examples | EXAMPLES/BASIC.md | Basic component examples |
| Code examples | EXAMPLES/DRIVERS.md | Peripheral driver templates |
| Code examples | EXAMPLES/ADVANCED.md | Advanced applications |
| Design patterns | PATTERNS/DESIGN.md | Design patterns |
| Design patterns | PATTERNS/INTERRUPT.md | Interrupt best practices |
| Design patterns | PATTERNS/TRAPS.md | Common pitfalls |

---

## Script Tools

### freertos_config_check.py

Validates key settings in FreeRTOSConfig.h:

```bash
python scripts/freertos_config_check.py FreeRTOSConfig.h
```

Outputs JSON format, which is convenient for CI integration.
