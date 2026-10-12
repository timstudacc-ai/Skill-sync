# Interrupt Best Practices

This document describes interrupt-related best practices such as the rules for using FromISR functions, the usage of portYIELD_FROM_ISR and NVIC priority configuration.

---

## 2.1 Rules for Using FromISR Functions

### Basic rules

| Rule | Description |
|------|------|
| **No blocking** | FromISR functions must not block; they may only return within a bounded time |
| **Use pdFALSE** | `xTicksToWait` should be set to 0 or `pdFALSE` |
| **Check the return value** | Check the return value to determine whether a context switch is required |
| **Call portYIELD_FROM_ISR** | Must be called if `*pxHigherPriorityTaskWoken` is pdTRUE |

### Correct usage

```c
void UART1_IRQHandler(void)
{
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;

    if (__HAL_UART_GET_FLAG(&huart1, UART_FLAG_RXNE) != RESET)
    {
        uint8_t data = (uint8_t)(huart1.Instance->DR & 0xFF);

        /* Send data to the queue from the ISR (non-blocking) */
        xQueueSendFromISR(g_uart_queue, &data, &xHigherPriorityTaskWoken);
    }

    /* If a higher-priority task was woken, perform a context switch */
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}
```

### Incorrect usage

```c
/* Wrong: blocking wait */
void vBadIsrExample(void)
{
    uint8_t data;
    xQueueReceiveFromISR(g_uart_queue, &data, portMAX_DELAY);  /* Wrong! */
}

/* Wrong: forgot to call portYIELD_FROM_ISR */
void vBadIsrExample2(void)
{
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    xQueueSendFromISR(g_uart_queue, &data, &xHigherPriorityTaskWoken);
    /* Forgot to call portYIELD_FROM_ISR(xHigherPriorityTaskWoken); */
}

/* Wrong: passing an incorrect timeout value */
void vBadIsrExample3(void)
{
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    xQueueSendFromISR(g_uart_queue, &data, &xHigherPriorityTaskWoken);
    /* A value other than pdFALSE was passed; FreeRTOS ignores it, but it is still not correct practice */
}
```

### List of FromISR functions

```c
/* Queue FromISR */
BaseType_t xQueueSendFromISR(QueueHandle_t xQueue,
                             const void *pvItemToQueue,
                             BaseType_t *pxHigherPriorityTaskWoken);

BaseType_t xQueueReceiveFromISR(QueueHandle_t xQueue,
                                void *pvBuffer,
                                BaseType_t *pxHigherPriorityTaskWoken);

/* Semaphore FromISR */
BaseType_t xSemaphoreGiveFromISR(SemaphoreHandle_t xSemaphore,
                                 BaseType_t *pxHigherPriorityTaskWoken);

/* Event group FromISR */
BaseType_t xEventGroupSetBitsFromISR(EventGroupHandle_t xEventGroup,
                                     const EventBits_t uxBitsToSet,
                                     BaseType_t *pxHigherPriorityTaskWoken);

/* Task notification FromISR */
BaseType_t xTaskNotifyFromISR(TaskHandle_t xTaskToNotify,
                              uint32_t ulValue,
                              eNotifyAction eAction,
                              BaseType_t *pxHigherPriorityTaskWoken);

void vTaskNotifyGiveFromISR(TaskHandle_t xTaskHandle,
                            BaseType_t *pxHigherPriorityTaskWoken);
```

---

## 2.2 Using portYIELD_FROM_ISR

### Syntax

```c
void portYIELD_FROM_ISR(BaseType_t xHigherPriorityTaskWoken);
```

### Purpose

When `xHigherPriorityTaskWoken` is `pdTRUE`, it triggers the PendSV interrupt to perform a context switch, waking the higher-priority task that is waiting for that signal.

### Complete example

```c
void DMA1_Stream5_IRQHandler(void)
{
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    uint32_t flag = DMA1->HISR;

    /* Clear the interrupt flag */
    DMA1->HIFCR = flag;

    if (flag & DMA_HISR_TCIF5)
    {
        /* DMA transfer complete */
        g_dma_complete = 1;

        /* Notify the task */
        vTaskNotifyGiveFromISR(g_dma_task_handle,
                               &xHigherPriorityTaskWoken);
    }

    /* Perform a context switch if necessary */
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}
```

### Simplified version (FreeRTOS v10+)

```c
/* Simplified macro supported by FreeRTOS v10.0+ */
portYIELD_FROM_ISR(xHigherPriorityTaskWoken);

/* Equivalent to: */
if (xHigherPriorityTaskWoken == pdTRUE)
{
    portYIELD();
}
```

### Complete interrupt handling flow

```c
void USART1_IRQHandler(void)
{
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;

    /* Handle the interrupt source */
    if (__HAL_UART_GET_FLAG(&huart1, UART_FLAG_RXNE) != RESET)
    {
        uint8_t data = huart1.Instance->DR;

        /* Send data to the queue (FromISR, non-blocking) */
        if (xQueueSendFromISR(g_uart_queue, &data, &xHigherPriorityTaskWoken) == pdTRUE)
        {
            /* Queued successfully; a higher-priority task may have been woken */
        }
    }

    /* Handle other interrupt sources... */

    /* Clear the interrupt flag */
    __HAL_UART_CLEAR_PEFLAG(&huart1);

    /* Perform a context switch if necessary */
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}
```

---

## 2.3 NVIC Priority Configuration

### Cortex-M priority grouping

```c
/* NVIC priority group configuration (STM32CubeMX default) */
NVIC_SetPriorityGrouping(NVIC_PRIORITYGROUP_4);  /* 4 bits of preemption priority, 0 bits of sub-priority */

/* The smaller the priority value, the higher the priority */

/* Priority range: 0 (highest) to 15 (lowest) */
```

### FreeRTOS priority requirements

```c
/* FreeRTOSConfig.h */

/* Kernel interrupt priority (PendSV, SysTick) */
#define configKERNEL_INTERRUPT_PRIORITY 255  /* (15 << 4) */

/* Maximum syscall priority (FromISR APIs cannot be called from a higher priority than this) */
#define configMAX_SYSCALL_INTERRUPT_PRIORITY 80  /* (5 << 4) */

/* Conclusion:
 * - Priorities 0-4: reserved for the kernel; no FreeRTOS API may be called
 * - Priorities 5-15: APIs ending in FromISR may be called
 * - Priority 15: the lowest (the PendSV and SysTick default)
 */
```

### Correct configuration example

```c
/* Timer interrupt (needs to trigger a task) → priority 5 */
HAL_NVIC_SetPriority(TIM6_DAC_IRQn, 5, 0);
HAL_NVIC_EnableIRQ(TIM6_DAC_IRQn);

/* UART interrupt (needs to send to a queue from an ISR) → priority 6 */
HAL_NVIC_SetPriority(USART1_IRQn, 6, 0);
HAL_NVIC_EnableIRQ(USART1_IRQn);

/* DMA interrupt (needs to notify a task from an ISR) → priority 7 */
HAL_NVIC_SetPriority(DMA1_Stream5_IRQn, 7, 0);
HAL_NVIC_EnableIRQ(DMA1_Stream5_IRQn);

/* External interrupt (button wake-up) → priority 10 */
HAL_NVIC_SetPriority(EXTI15_10_IRQn, 10, 0);
HAL_NVIC_EnableIRQ(EXTI15_10_IRQn);

/* Note: the smaller the value, the higher the priority */
```

### Incorrect configuration example

```c
/* Wrong: the peripheral interrupt priority is too low (higher than the kernel) */
HAL_NVIC_SetPriority(USART1_IRQn, 4, 0);  /* Wrong! It prevents the ISR from calling FreeRTOS APIs */

/* Correct: priority >= 5 */
HAL_NVIC_SetPriority(USART1_IRQn, 5, 0);  /* Correct */
```

### Relationship between the priority value and the effective priority

```c
/* The Cortex-M priority configuration register is 8 bits wide, but usually only the top 4 bits are used */

/* The priority value is shifted left by 4 bits before being written to the NVIC */
NVIC_SetPriority(IRQn, priority << 4);

/* Example */
NVIC_SetPriority(USART1_IRQn, 6 << 4);  /* Priority 6 */

/* Effective priority calculation */
#define PRIORITY_SHIFT  4
#define NVIC_EncodePriority(Group, PreemptPriority, SubPriority) \
    (((PreemptPriority) & 0x07) << PRIORITY_SHIFT) | \
    ((SubPriority) & 0x00)
```

### Best practice for interrupt priority configuration

```c
/* 1. Set the priority grouping first, then configure the individual interrupts */
void MX_NVIC_Init(void)
{
    /* Set the priority grouping: 4 bits of preemption priority, 0 bits of sub-priority */
    HAL_NVIC_SetPriorityGrouping(NVIC_PRIORITYGROUP_4);

    /* Configure the system exception priorities (must be done after grouping) */
    HAL_NVIC_SetPriority(MemoryManagement_IRQn, 0, 0);
    HAL_NVIC_SetPriority(BusFault_IRQn, 0, 0);
    HAL_NVIC_SetPriority(UsageFault_IRQn, 0, 0);
    HAL_NVIC_SetPriority(SVCall_IRQn, 0, 0);
    HAL_NVIC_SetPriority(PendSV_IRQn, 15, 0);  /* Lowest */
    HAL_NVIC_SetPriority(SysTick_IRQn, 15, 0); /* Lowest */

    /* Configure the peripheral interrupts */
    HAL_NVIC_SetPriority(USART1_IRQn, 6, 0);
    HAL_NVIC_SetPriority(DMA1_Stream5_IRQn, 7, 0);
    HAL_NVIC_SetPriority(EXTI15_10_IRQn, 10, 0);

    /* Enable the interrupts */
    HAL_NVIC_EnableIRQ(USART1_IRQn);
    HAL_NVIC_EnableIRQ(DMA1_Stream5_IRQn);
    HAL_NVIC_EnableIRQ(EXTI15_10_IRQn);
}
```

---

## Interrupt Design Best Practices

### 1. Minimise ISR execution time

```c
/* Bad: doing complex processing inside the ISR */
void vBadIsr(void)
{
    /* Complex data processing - time consuming */
    process_data_in_isr();

    /* Send to the queue */
    xQueueSendFromISR(g_queue, &data, &xHigherPriorityTaskWoken);
}

/* Good: only send the data in the ISR and do the complex processing in a task */
void vGoodIsr(void)
{
    /* Quickly read the data */
    uint8_t data = huart1.Instance->DR;

    /* Send it to the queue and let a task process it */
    xQueueSendFromISR(g_queue, &data, &xHigherPriorityTaskWoken);
}
```

### 2. Use task notifications instead of semaphores

```c
/* Using a semaphore */
void vBadIsr(void)
{
    xSemaphoreGiveFromISR(g_sem, &xHigherPriorityTaskWoken);
}

void vTask(void)
{
    while (1)
    {
        xSemaphoreTake(g_sem, portMAX_DELAY);
        /* Process */
    }
}

/* Using a task notification (more lightweight) */
void vGoodIsr(void)
{
    vTaskNotifyGiveFromISR(g_task_handle, &xHigherPriorityTaskWoken);
}

void vTask(void)
{
    while (1)
    {
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        /* Process */
    }
}
```

### 3. Avoid floating-point arithmetic in ISRs

```c
/* Avoid */
void vBadIsr(void)
{
    float result = complex_calculation();  /* Time consuming */
    xQueueSendFromISR(g_queue, &result, &xHigherPriorityTaskWoken);
}

/* Recommended */
void vGoodIsr(void)
{
    uint32_t raw_data = get_raw_data();
    xQueueSendFromISR(g_queue, &raw_data, &xHigherPriorityTaskWoken);
}

void vTask(void)
{
    while (1)
    {
        uint32_t data;
        xQueueReceive(g_queue, &data, portMAX_DELAY);

        /* Do the floating-point arithmetic in the task */
        float result = (float)data * 0.123f;
    }
}
```

### 4. Avoid using large amounts of memory in ISRs

```c
/* Avoid */
void vBadIsr(void)
{
    uint8_t buffer[1024];  /* Allocating a large array on the stack */
    /* Process */
}

/* Recommended */
static uint8_t g_isr_buffer[1024];  /* Static allocation */

void vGoodIsr(void)
{
    /* Use the static buffer */
    memcpy(g_isr_buffer, source, 1024);
    xQueueSendFromISR(g_queue, g_isr_buffer, &xHigherPriorityTaskWoken);
}
```
