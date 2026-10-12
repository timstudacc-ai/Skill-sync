# STM32 + FreeRTOS Skill User Guide

> **Important**: this document is intended for **you (the user) to read only**; the AI does not read it. It helps you understand the purpose of each file and how to make the AI read the right files to answer your questions.

---

## What is this skill?

This is a tool designed to help you use the **FreeRTOS real-time operating system** on **STM32 microcontrollers**. The AI can:

- **Write code for you**: create tasks, queues, semaphores and peripheral drivers
- **Review your code**: analyse problems, optimise performance and track down errors
- **Teach you the concepts**: explain scheduling mechanisms, communication methods and debugging approaches

---

## File structure overview

This skill is made up of the following files:

```
stm32-freertos/
├── SKILL.md              ← the only main file the AI reads automatically
├── USER_GUIDE.md         ← the file you are reading now (the AI does not read it)
├── REFERENCE/            ← API reference manuals (4 files)
│   ├── FREERTOS_API.md
│   ├── STD_LIBS.md
│   ├── HAL_DRIVERS.md
│   └── DEBUG_TOOLS.md
├── EXAMPLES/             ← code examples (3 files)
│   ├── BASIC.md
│   ├── DRIVERS.md
│   └── ADVANCED.md
├── PATTERNS/             ← design patterns and pitfalls (3 files)
│   ├── DESIGN.md
│   ├── INTERRUPT.md
│   └── TRAPS.md
└── scripts/
    └── freertos_config_check.py
```

---

## The REFERENCE/ directory: API reference manuals

This directory tells you how to use the FreeRTOS API and how the HAL library works together with FreeRTOS.

---

### REFERENCE/FREERTOS_API.md

**When should you read this?**

When you want to know how a particular function is used:

- "What parameters does `xTaskCreate` need?"
- "What is the difference between `xQueueSend` and `xQueueSendFromISR`?"
- "How does CMSIS-RTOS v2 differ from the native FreeRTOS API?"
- "How do I use task notifications?"

**What it contains:**

```
1. Native FreeRTOS API (v10+)
   ├── Task management
   │   ├── xTaskCreate - create a task dynamically
   │   ├── xTaskCreateStatic - create a task statically
   │   ├── vTaskDelete - delete a task
   │   ├── vTaskDelay - relative delay
   │   ├── vTaskDelayUntil - absolute delay
   │   ├── vTaskPrioritySet - set the priority
   │   └── uxTaskPriorityGet - get the priority
   │
   ├── Queue
   │   ├── xQueueCreate - create a queue
   │   ├── xQueueSend - send data
   │   ├── xQueueReceive - receive data
   │   └── xQueueSendFromISR - send from an interrupt
   │
   ├── Semaphore
   │   ├── xSemaphoreCreateBinary - binary semaphore
   │   ├── xSemaphoreCreateCounting - counting semaphore
   │   ├── xSemaphoreCreateMutex - mutex
   │   ├── xSemaphoreTake - take a semaphore
   │   └── xSemaphoreGive - give a semaphore
   │
   ├── Event groups
   │   ├── xEventGroupCreate - create an event group
   │   ├── xEventGroupSetBits - set event bits
   │   ├── xEventGroupWaitBits - wait for event bits
   │   └── xEventGroupSetBitsFromISR - set bits from an interrupt
   │
   └── Task notifications
       ├── xTaskNotify - send a notification
       ├── xTaskNotifyFromISR - send from an interrupt
       └── xTaskNotifyWait - wait for a notification

2. CMSIS-RTOS v2 API
   ├── osThreadNew - create a thread
   ├── osDelay - delay
   ├── osMessageQueueNew - create a message queue
   ├── osSemaphoreNew - create a semaphore
   ├── osMutexNew - create a mutex
   └── osEventFlagsNew - create event flags
```

**Typical question:** "How do I use the timeout parameter of `xQueueSend`?"

---

### REFERENCE/STD_LIBS.md

**When should you read this?**

When you want to use the standard library together with FreeRTOS:

- "How do I make `printf` output to the serial port?"
- "Can I use `memcpy` during a DMA transfer?"
- "Why should I avoid frequent `malloc/free` inside a task?"
- "How do I redirect printf to ITM/SWO?"

**What it contains:**

```
1. stdio.h - printf redirection
   ├── Redirect to ITM/SWO (output through the debugger)
   │   ├── ITM_SendChar implementation
   │   ├── __attribute__((weak)) _write override
   │   └── How to verify it
   │
   └── Redirect to UART (output through the serial port)
       ├── HAL_UART_Transmit override
       ├── Baud rate configuration
       └── Blocking vs non-blocking

2. string.h - memory operations
   ├── memcpy together with DMA
   │   ├── Usage in the DMA receive-complete callback
   │   ├── Buffer copying
   │   └── Points to note
   │
   └── memset initialisation
       ├── Clearing control blocks
       ├── Buffer initialisation
       └── Static vs dynamic

3. stdlib.h - memory management
   ├── pvPortMalloc / vPortFree (FreeRTOS memory allocation)
   │   ├── Differences from the standard malloc/free
   │   ├── Memory pools
   │   └── Avoiding fragmentation
   │
   └── Dynamic memory considerations
       ├── The problem with frequent allocation and freeing
       ├── Memory leak detection
       └── Prefer static allocation
```

**Typical question:** "How do I use printf on STM32?"

---

### REFERENCE/HAL_DRIVERS.md

**When should you read this?**

When you need to write code in which a peripheral works together with FreeRTOS:

- "How do I receive variable-length data over UART?"
- "How do I notify a task about continuous ADC acquisition?"
- "How do I combine an I2C sensor with FreeRTOS?"
- "How do I make a timer trigger a task?"

**What it contains:**

```
1. UART DMA + queue (variable-length data reception)
   ├── Using the IDLE interrupt to detect the end of reception
   ├── DMA configuration
   ├── Passing data through a queue
   ├── Header file structure
   └── Complete driver code

2. ADC DMA + task notification
   ├── Continuous conversion mode
   ├── DMA configuration
   ├── HAL_ADC_ConvCpltCallback
   ├── Task notification mechanism
   └── Code implementation

3. I2C sensor reading
   ├── Master mode: read sensor data
   │   ├── MPU6050 example
   │   ├── BME280 example
   │   └── Timeout handling
   │
   └── Slave mode: respond to master requests
       ├── I2C slave address configuration
       └── Callback handling

4. TIM timer + task triggering
   ├── Timer interrupt configuration
   ├── Task notification mechanism
   ├── Periodic task implementation
   └── PWM output
```

**Typical question:** "How do I use DMA to receive variable-length data over UART?"

---

### REFERENCE/DEBUG_TOOLS.md

**When should you read this?**

When you need to debug and analyse the system:

- "How do I use SystemView to look at task switches?"
- "How do I configure TRACEalyzer?"
- "How do I print the task run times?"
- "How do I configure ITM/SWO?"

**What it contains:**

```
1. SEGGER SystemView (Keil/IAR environment)
   ├── Purpose
   │   ├── Real-time system analysis
   │   ├── Visualisation of task switches
   │   ├── Interrupt duration statistics
   │   └── CPU usage analysis
   │
   ├── Configuration steps
   │   ├── Add the SystemView library
   │   ├── Initialise with SEGGER_SYSVIEW_Init()
   │   └── Configure ITM/SWO
   │
   └── How to use it
       ├── Start recording
       ├── Analyse task switches
       └── Find performance bottlenecks

2. Percep TRACEalyzer (FreeRTOS environment)
   ├── Purpose
   │   ├── Recording of trace events
   │   ├── Timing diagram visualisation
   │   ├── Task resource statistics
   │   └── Locating performance bottlenecks
   │
   ├── Configuration steps
   │   ├── Enable the trace facility
   │   ├── Add trcRecorder.c
   │   └── Configure trcConfig.h
   │
   └── How to use it
       ├── Export the .ptd file
       ├── Open it with TRACEalyzer
       └── Analyse the results

3. ITM/SWO configuration
   ├── ST-Link configuration
   │   ├── Enable SWO output
   │   ├── Configure the TPIU
   │   └── How to verify it
   │
   └── J-Link configuration
       ├── SWO initialisation
       └── Baud rate configuration

4. FreeRTOS statistics features
   ├── Task state statistics
   │   ├── How to use vTaskList
   │   ├── uxTaskGetStackHighWaterMark
   │   └── Printing task information
   │
   └── Run-time statistics
       ├── xTaskGetSystemState
       ├── CPU usage calculation
       └── Stack overflow detection
```

**Typical question:** "How do I use SystemView to analyse task switches?"

---

## The EXAMPLES/ directory: code examples

This directory gives you complete, ready-to-use code.

---

### EXAMPLES/BASIC.md

**When should you read this?**

When you need examples of the basic components:

- "How do I create my first task?"
- "How do I use a queue?"
- "How do semaphores synchronise tasks?"
- "How do I use a mutex to protect a shared resource?"
- "How do I use an event group for multi-condition triggering?"
- "How do I use task notifications?"

**What it contains:**

```
1. Dynamic task creation
   ├── Task function definition
   ├── Explanation of the xTaskCreate parameters
   ├── Task priority setting
   └── Complete runnable example

2. Static task creation
   ├── Static control blocks and stacks
   ├── How to use xTaskCreateStatic
   └── Advantages and suitable scenarios

3. Queue - producer-consumer
   ├── Queue creation
   ├── Producer task: produces data
   ├── Consumer task: processes data
   ├── Timeout handling
   └── Complete example code

4. Binary semaphore - task synchronisation
   ├── Semaphore creation
   ├── Giving the semaphore from an interrupt
   │   ├── HAL_GPIO_EXTI_Callback
   │   └── xSemaphoreGiveFromISR
   │
   └── Taking the semaphore in a task
       ├── xSemaphoreTake
       └── Button debouncing example

5. Mutex - shared resource protection
   ├── xSemaphoreCreateMutex
   ├── Priority inheritance
   ├── Exclusive UART access
   └── Complete example

6. Event group - multi-condition triggering
   ├── xEventGroupCreate
   ├── xEventGroupSetBits
   ├── xEventGroupWaitBits
   ├── AND/OR logic
   └── Complete example

7. Task notifications - lightweight communication
   ├── xTaskNotify to send
   ├── xTaskNotifyWait to receive
   ├── Notification from an interrupt
   └── Comparison with queues/semaphores
```

**Typical question:** "Give me a complete queue producer-consumer example"

---

### EXAMPLES/DRIVERS.md

**When should you read this?**

When you need peripheral driver templates:

- "Give me a UART DMA driver"
- "How do I do ADC DMA acquisition?"
- "How do I write an I2C sensor driver?"
- "How do I implement printf redirection?"

**What it contains:**

```
1. UART DMA + queue + IDLE interrupt (complete driver)
   ├── Header file structure (uart_driver.h)
   │   ├── Queue definition
   │   ├── Function declarations
   │   └── Macro definitions
   │
   ├── Implementation file (uart_driver.c)
   │   ├── MX_UART1_Init initialisation
   │   ├── HAL_UART_IDLECallback
   │   ├── HAL_UART_RxCpltCallback
   │   ├── vUartRxTask receive task
   │   └── Data processing task
   │
   └── How to use it
       ├── Initialisation call
       ├── Task creation
       └── Data retrieval

2. ADC DMA + task notification (complete driver)
   ├── Header file structure (adc_driver.h)
   ├── Implementation file (adc_driver.c)
   │   ├── MX_ADC1_Init
   │   ├── HAL_ADC_ConvCpltCallback
   │   └── vAdcTask data processing
   └── How to use it

3. I2C sensor reading (BME280/MPU6050)
   ├── BME280 driver
   │   ├── BME280_Init initialisation
   │   ├── BME280_Read data read
   │   └── Temperature, humidity and pressure calculation
   │
   ├── MPU6050 driver
   │   ├── MPU6050_Init initialisation
   │   ├── MPU6050_ReadAll read everything
   │   └── Accelerometer/gyroscope data
   │
   └── How to use it
       ├── Passing data through a queue
       └── Task scheduling

4. printf redirection
   ├── ITM_SendChar implementation
   │   ├── ITM initialisation
   │   ├── _write override
   │   └── How to verify it
   │
   └── UART redirection
       ├── _write override
       └── HAL_UART_Transmit
```

**Typical question:** "Give me the complete UART DMA driver code; I want to pass the data to a queue"

---

### EXAMPLES/ADVANCED.md

**When should you read this?**

When you need advanced application examples:

- "How do I do multi-task sensor fusion?"
- "How do I configure Tickless low-power mode?"
- "How do I make STM32CubeMX generate FreeRTOS code?"
- "What modifications does the code generated by CubeMX need?"

**What it contains:**

```
1. Multi-task sensor fusion
   ├── System architecture
   │   ├── Sensor collection task
   │   ├── Data processing task (filtering, fusion)
   │   └── Data sending task
   │
   ├── Inter-task communication
   │   ├── Raw data queue
   │   ├── Fused data queue
   │   └── I2C mutex
   │
   ├── Complementary filter algorithm
   │   ├── Accelerometer angle calculation
   │   ├── Gyroscope integration
   │   └── Fusion implementation
   │
   └── Complete code
       ├── Task definitions
       ├── Queue creation
       └── Starting the scheduler

2. Tickless low-power mode
   ├── FreeRTOSConfig.h configuration
   │   ├── configUSE_TICKLESS_IDLE
   │   ├── configPRE_SLEEP_PROCESSING
   │   └── configPOST_SLEEP_PROCESSING
   │
   ├── Low-power implementation
   │   ├── vPreSleepProcessing
   │   ├── vPostSleepProcessing
   │   ├── Clock restoration
   │   └── Entering STOP mode
   │
   └── Points to note when using it
       ├── Wake-up source configuration
       ├── Wake-up time
       └── Peripheral restoration

3. Notes on STM32CubeMX configuration
   ├── FreeRTOS middleware configuration
   │   ├── Middleware → FreeRTOS
   │   ├── Version selection
   │   └── Config Parameters
   │
   ├── NVIC configuration
   │   ├── Priority Group selection
   │   ├── PendSV/SysTick priority
   │   └── Peripheral interrupt priorities
   │
   ├── Peripheral + DMA configuration
   │   ├── UART DMA settings
   │   ├── ADC DMA settings
   │   └── Interrupt enabling
   │
   └── Modifications to the generated code
       ├── Removing MX_FREERTOS_Init
       ├── Position of HAL_Init
       ├── Task definitions
       └── Adjusting the stack sizes
```

**Typical question:** "How do I configure STM32CubeMX to generate FreeRTOS code?"

---

## The PATTERNS/ directory: design patterns and pitfalls

This directory gives you solutions to common problems.

---

### PATTERNS/DESIGN.md

**When should you read this?**

When you need a design pattern reference:

- "How do I implement the producer-consumer pattern?"
- "How do I do the publish-subscribe pattern?"
- "How do I implement a state machine?"
- "How do I manage a buffer pool?"

**What it contains:**

```
1. Producer-consumer pattern
   ├── Pattern description
   │   ├── Suitable scenarios
   │   └── Architecture diagram
   │
   ├── Single producer, single consumer
   │   ├── Queue implementation
   │   ├── Task definitions
   │   └── Complete example
   │
   ├── Multiple producers, multiple consumers
   │   ├── Several tasks sharing a queue
   │   ├── Distinguishing the data sources
   │   └── Complete example
   │
   └── Variants
       ├── Queues with priorities
       └── Reception with timeouts

2. Publish-subscribe pattern
   ├── Pattern description
   │   ├── Suitable scenarios
   │   └── Architecture diagram
   │
   ├── Event group implementation
   │   ├── xEventGroupCreate
   │   ├── xEventGroupSetBits
   │   └── xEventGroupWaitBits
   │
   ├── Multi-condition triggering
   │   ├── AND logic (wait for all bits)
   │   └── OR logic (wait for any bit)
   │
   └── Broadcast notification
       ├── Several tasks waiting for the same event
       └── Clearing events

3. State machine implementation
   ├── Pattern description
   │   ├── Finite state machine
   │   └── Suitable scenarios
   │
   ├── State definitions
   │   ├── enum defines the states
   │   ├── State variables
   │   └── State transition table
   │
   ├── Event definitions
   │   ├── enum defines the events
   │   └── Event queue
   │
   ├── State handler functions
   │   ├── State handler table
   │   ├── Action execution
   │   └── State transitions
   │
   └── Complete example
       ├── State machine control block
       ├── State handler functions
       └── Task implementation

4. Resource pool management
   ├── Pattern description
   │   ├── Fixed-size buffers
   │   └── Avoiding memory fragmentation
   │
   ├── Buffer pool implementation
   │   ├── Static array
   │   ├── Usage flags
   │   └── Allocation/free functions
   │
   └── Memory pool
       ├── pvPortMalloc replacement
       ├── Pre-allocated memory
       └── Fragmentation avoidance
```

**Typical question:** "How do I implement a producer-consumer pattern?"

---

### PATTERNS/INTERRUPT.md

**When should you read this?**

When you need to write interrupt code:

- "Can I call xQueueSend from an interrupt?"
- "When do I use portYIELD_FROM_ISR?"
- "How do I configure the NVIC priorities?"
- "How do FromISR functions differ from the normal ones?"

**What it contains:**

```
1. Rules for using FromISR functions
   ├── Why FromISR is needed
   │   ├── Normal functions cannot be used in an ISR
   │   ├── FromISR functions do not block
   │   └── They come with priority inheritance
   │
   ├── Which functions have a FromISR version
   │   ├── xQueueSendFromISR
   │   ├── xQueueReceiveFromISR
   │   ├── xSemaphoreGiveFromISR
   │   ├── xEventGroupSetBitsFromISR
   │   └── vTaskNotifyGiveFromISR
   │
   └── Correct usage
       ├── No blocking
       ├── The xHigherPriorityTaskWoken parameter
       └── Checking the return value

2. portYIELD_FROM_ISR explained
   ├── When it needs to be called
   │   ├── When a FromISR function returns pdTRUE
   │   └── When a high-priority task needs to be woken
   │
   ├── Complete examples
   │   ├── DMA transfer-complete interrupt
   │   ├── UART receive interrupt
   │   └── External interrupt
   │
   └── Common mistakes
       ├── Forgetting to call it
       ├── Wrong parameters
       └── Calling it several times

3. NVIC priority configuration
   ├── Cortex-M priority grouping
   │   ├── NVIC_PRIORITYGROUP_4
   │   └── Priority value range
   │
   ├── FreeRTOS priority requirements
   │   ├── configKERNEL_INTERRUPT_PRIORITY
   │   ├── configMAX_SYSCALL_INTERRUPT_PRIORITY
   │   └── Priority range
   │
   └── Setting peripheral interrupt priorities
       ├── Timer interrupt (5)
       ├── UART interrupt (6)
       ├── DMA interrupt (7)
       └── External interrupt (10)

4. Interrupt best practices
   ├── Minimise ISR execution time
   │   ├── Do only what is necessary
   │   ├── Leave the rest to tasks
   │   └── Pass data with notifications/queues
   │
   ├── Use task notifications instead of semaphores
   │   ├── More lightweight
   │   ├── Faster
   │   └── Fewer resources
   │
   └── Avoid complex processing in ISRs
       ├── Do not call functions that block
       ├── Do not do floating-point arithmetic
       └── Do not use large amounts of memory
```

**Typical question:** "Why does calling xQueueSend from my interrupt fail?"

---

### PATTERNS/TRAPS.md

**When should you read this?**

When your program shows strange behaviour:

- "Why is the high-priority task slow instead?"
- "The program crashes after running for a while"
- "It feels like there is a deadlock, how do I track it down?"
- "What do I do about a stack overflow?"

**What it contains:**

```
1. Priority inversion
   ├── Problem description
   │   ├── Diagram
   │   ├── Root cause
   │   └── Hazards
   │
   ├── Mutex priority inheritance
   │   ├── xSemaphoreCreateMutex
   │   └── Automatic priority elevation
   │
   ├── Solutions
   │   ├── Use a mutex
   │   ├── Avoid holding the lock for a long time
   │   └── Task priority design
   │
   └── Complete example
       ├── Code with priority inversion
       └── Code after the fix

2. Stack overflow
   ├── How to detect it
   │   ├── configCHECK_FOR_STACK_OVERFLOW
   │   ├── vApplicationStackOverflowHook
   │   └── uxTaskGetStackHighWaterMark
   │
   ├── How to prevent it
   │   ├── Set a sensible stack size
   │   ├── Avoid large arrays on the stack
   │   └── Check stack usage regularly
   │
   ├── Stack size estimation
   │   ├── Base requirement (128-256 words)
   │   ├── String processing (+64-128 words)
   │   ├── Recursive calls (+256 words)
   │   └── Large arrays (+ the array size)
   │
   └── Common causes
       ├── Infinite recursion
       ├── Large local variables
       └── Too deep a function call chain

3. Deadlock
   ├── Conditions for it to occur
   │   ├── Mutual exclusion
   │   ├── Hold and wait
   │   └── Circular wait
   │
   ├── Solution strategies
   │   ├── A consistent acquisition order
   │   ├── Using a single mutex
   │   └── Acquisition with a timeout
   │
   ├── Deadlock examples
   │   ├── Deadlock between two mutexes
   │   └── Deadlock between tasks
   │
   └── Deadlock detection
       ├── Inspecting the task states
       ├── Analysing who is waiting
       └── Preventive measures

4. Resource leaks
   ├── Memory leaks
   │   ├── pvPortMalloc never freed
   │   ├── How to detect it
   │   └── How to fix it
   │
   ├── Queue leaks
   │   ├── xQueueCreate never deleted
   │   └── How to fix it
   │
   ├── Semaphore leaks
   │   ├── xSemaphoreCreateBinary never deleted
   │   └── How to fix it
   │
   └── Cleanup methods
       ├── Clean up when the task ends
       ├── Use global resources
       └── Explicit delete functions
```

**Typical question:** "Why is the high-priority task blocked? Is there priority inversion in the program?"

---

## How to Make the AI Read the Right File

### Method 1: describe it in natural language (most recommended)

Just tell the AI what you want to do; the AI works out which files to read from the rules in SKILL.md.

**Example conversations:**

```
You: Help me write a UART DMA driver
AI: (automatically reads REFERENCE/HAL_DRIVERS.md and EXAMPLES/DRIVERS.md)
AI: Sure, here is the complete UART DMA driver code...
```

```
You: I get an error when I call xQueueSend from my interrupt
AI: (automatically reads PATTERNS/INTERRUPT.md)
AI: Inside an ISR you should use xQueueSendFromISR; let me fix the code for you...
```

```
You: My program has a priority inversion problem
AI: (automatically reads PATTERNS/TRAPS.md)
AI: The solution to priority inversion is to use a mutex...
```

---

### Method 2: specify the file explicitly

If you know which file you want, you can tell the AI explicitly.

**Example conversations:**

```
You: Please read EXAMPLES/DRIVERS.md and help me write a UART DMA driver
AI: (reads EXAMPLES/DRIVERS.md)
AI: Sure, based on the UART DMA example in DRIVERS.md, here is the complete code...
```

```
You: Please read PATTERNS/INTERRUPT.md and tell me how to use FromISR
AI: (reads INTERRUPT.md)
AI: The rules for using FromISR functions are as follows...
```

---

### Method 3: specify several files

**Example conversation:**

```
You: Please read REFERENCE/HAL_DRIVERS.md and PATTERNS/INTERRUPT.md,
   and help me write a UART driver that sends to a queue from an interrupt
AI: (reads both files)
AI: Based on the UART driver in HAL_DRIVERS.md and the interrupt rules in INTERRUPT.md...
```

---

## Quick Lookup Table

**I want to...** → **tell the AI to read this**

| Requirement | File |
|------|------|
| Create a task | EXAMPLES/BASIC.md |
| Pass data with a queue | EXAMPLES/BASIC.md |
| Synchronise with a semaphore | EXAMPLES/BASIC.md |
| Protect a resource with a mutex | EXAMPLES/BASIC.md |
| Coordinate several tasks | PATTERNS/DESIGN.md |
| UART DMA reception | EXAMPLES/DRIVERS.md |
| ADC DMA acquisition | EXAMPLES/DRIVERS.md |
| I2C sensor reading | EXAMPLES/DRIVERS.md |
| printf output to the serial port | REFERENCE/STD_LIBS.md |
| printf output to ITM | REFERENCE/STD_LIBS.md |
| Send to a queue from an interrupt | PATTERNS/INTERRUPT.md |
| Configure the NVIC priorities | PATTERNS/INTERRUPT.md |
| Configure SystemView | REFERENCE/DEBUG_TOOLS.md |
| Configure TRACEalyzer | REFERENCE/DEBUG_TOOLS.md |
| Print task statistics | REFERENCE/DEBUG_TOOLS.md |
| Fix a deadlock | PATTERNS/TRAPS.md |
| Fix a stack overflow | PATTERNS/TRAPS.md |
| Fix priority inversion | PATTERNS/TRAPS.md |
| Low-power mode | EXAMPLES/ADVANCED.md |
| CubeMX configuration | EXAMPLES/ADVANCED.md |
| Look up API parameters | REFERENCE/FREERTOS_API.md |

---

## Summary of the Directory Structure

```
stm32-freertos/
├── SKILL.md              ← the only main file the AI reads
├── USER_GUIDE.md         ← the file you are reading now
├── REFERENCE/            ← API reference
│   ├── FREERTOS_API.md   ← API syntax and parameters
│   ├── STD_LIBS.md       ← standard library integration
│   ├── HAL_DRIVERS.md    ← peripheral driver integration
│   └── DEBUG_TOOLS.md    ← debug tool configuration
├── EXAMPLES/             ← code examples
│   ├── BASIC.md          ← basic component examples
│   ├── DRIVERS.md        ← peripheral driver examples
│   └── ADVANCED.md       ← advanced application examples
├── PATTERNS/             ← design patterns
│   ├── DESIGN.md         ← producer-consumer and other patterns
│   ├── INTERRUPT.md      ← interrupt best practices
│   └── TRAPS.md          ← common pitfalls and solutions
└── scripts/
    └── freertos_config_check.py
```

---

## Getting Started

1. **Read this guide** to understand the purpose of each file
2. **When you have a requirement**, tell the AI in natural language what you want to do
3. **The AI reads the relevant documents automatically** to answer your question
4. **If the AI's answer is not accurate**, explicitly tell the AI to read a specific file

---

## Tips

- If you are not sure which file to read, just describe your problem; the AI works it out automatically from the rules in SKILL.md
- If you want the AI to read a specific file, say so explicitly: "Please read EXAMPLES/DRIVERS.md"
- Several files can be joined with "and": "Please read REFERENCE/HAL_DRIVERS.md and PATTERNS/INTERRUPT.md"
