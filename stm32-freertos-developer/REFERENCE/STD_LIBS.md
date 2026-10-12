# Standard Library Integration

This document describes how to integrate stdio.h, string.h and stdlib.h with FreeRTOS.

---

## stdio.h (printf redirection)

### ITM_SendChar (SWO output)

```c
#include <stdio.h>

/* Redirect printf to ITM/SWO */
int __attribute__((weak)) _write(int file, char *ptr, int len)
{
    (void)file;
    int i;
    for (i = 0; i < len; i++)
    {
        ITM_SendChar(ptr[i]);  /* Output via SWO */
    }
    return len;
}

/* Usage example */
void vTaskITM(void *pvParameters)
{
    while (1)
    {
        printf("Stack remaining: %lu bytes\r\n",
               uxTaskGetStackHighWaterMark(NULL));
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
```

### UART Redirection

```c
#include <stdio.h>
#include "usart.h"

int __attribute__((weak)) _write(int file, char *ptr, int len)
{
    (void)file;
    HAL_UART_Transmit(&huart1, (uint8_t *)ptr, len, HAL_MAX_DELAY);
    return len;
}
```

### snprintf Safe Formatting

```c
#include <stdio.h>
#include <string.h>

void vTaskPrintStatus(void *pvParameters)
{
    char buffer[128];
    TaskStatus_t *pxTaskStatusArray;
    uint32_t ulTotalRunTime, ulStatsAsPercentage;

    /* Get task status */
    UBaseType_t uxArraySize = uxTaskGetNumberOfTasks();
    pxTaskStatusArray = pvPortMalloc(uxArraySize * sizeof(TaskStatus_t));

    if (pxTaskStatusArray != NULL)
    {
        uxTaskGetSystemState(pxTaskStatusArray, uxArraySize,
                             &ulTotalRunTime);

        /* Safe formatting (prevents buffer overflow) */
        snprintf(buffer, sizeof(buffer),
                 "Task count: %lu\r\n", uxArraySize);
        HAL_UART_Transmit(&huart1, (uint8_t *)buffer,
                          strlen(buffer), HAL_MAX_DELAY);

        vPortFree(pxTaskStatusArray);
    }
}
```

---

## string.h (memory operations with DMA)

### Using memcpy with DMA

```c
#include <string.h>
#include "dma.h"

#define RX_BUFFER_SIZE 256

uint8_t g_rx_buffer[RX_BUFFER_SIZE];
uint8_t g_rx_temp[RX_BUFFER_SIZE];

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        /* Copy the received data into the processing buffer */
        memcpy(g_rx_temp, g_rx_buffer, RX_BUFFER_SIZE);

        /* Notify the processing task */
        BaseType_t xHigherPriorityTaskWoken = pdFALSE;
        xQueueSendFromISR(g_uart_queue, g_rx_temp,
                          &xHigherPriorityTaskWoken);
        portYIELD_FROM_ISR(xHigherPriorityTaskWoken);

        /* Restart DMA reception */
        HAL_UART_Receive_IT(&huart1, g_rx_buffer, RX_BUFFER_SIZE);
    }
}
```

### memset to Initialise a Control Block

```c
#include <string.h>

StaticTask_t xTaskBuffer;
StackType_t xStack[128];

void vTaskCreateStaticExample(void)
{
    /* Clear the control block (recommended) */
    memset(&xTaskBuffer, 0, sizeof(StaticTask_t));

    /* Create a static task */
    xTaskCreateStatic(vTaskFunction, "StaticTask",
                      128, NULL, osPriorityNormal,
                      xStack, &xTaskBuffer);
}
```

---

## stdlib.h (dynamic memory considerations)

### Avoid Frequent malloc/free Inside a Task

```c
#include <stdlib.h>
#include "main.h"

/* Not recommended: allocate memory on every processing pass */
void vTaskBadExample(void *pvParameters)
{
    while (1)
    {
        char *p_data = pvPortMalloc(256);  /* Frequent allocation */
        if (p_data != NULL)
        {
            /* Process the data */
            process_data(p_data);
            vPortFree(p_data);  /* Free */
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

/* Recommended: use a static buffer pool */
#define BUFFER_POOL_SIZE 10
#define BUFFER_SIZE 256

static uint8_t g_buffer_pool[BUFFER_POOL_SIZE][BUFFER_SIZE];
static uint8_t g_buffer_used[BUFFER_POOL_SIZE];

void *pvAllocateBuffer(void)
{
    for (int i = 0; i < BUFFER_POOL_SIZE; i++)
    {
        if (g_buffer_used[i] == 0)
        {
            g_buffer_used[i] = 1;
            memset(g_buffer_pool[i], 0, BUFFER_SIZE);
            return g_buffer_pool[i];
        }
    }
    return NULL;  /* Pool is full */
}

void vFreeBuffer(void *p_buffer)
{
    for (int i = 0; i < BUFFER_POOL_SIZE; i++)
    {
        if (g_buffer_pool[i] == p_buffer)
        {
            g_buffer_used[i] = 0;
            break;
        }
    }
}
```

### pvPortMalloc vs malloc

```c
/* Use the FreeRTOS memory allocation functions */
void *pvPortMalloc(size_t xSize);    /* Allocate memory */
void vPortFree(void *pv);             /* Free memory */

/* Differences from the standard library:
 * - pvPortMalloc uses the FreeRTOS heap memory management
 * - It can be used together with functions such as xTaskCreate
 * - It supports static allocation strategies
 */
```

### Heap Memory Monitoring

```c
void vHeapStatsPrint(void)
{
    HeapStats_t heap_stats;

    xPortGetHeapStats(&heap_stats);

    printf("\r\nHeap statistics:\r\n");
    printf("  Smallest ever free: %lu bytes\r\n", heap_stats.xMinimumEverFreeBytesRemaining);
    printf("  Currently available: %lu bytes\r\n", heap_stats.xAvailableHeapSpaceInBytes);
    printf("  Number of blocks allocated: %lu\r\n", heap_stats.xNumberOfAllocations);
    printf("  Number of blocks freed: %lu\r\n", heap_stats.xNumberOfFrees);
    printf("  Largest free block: %lu bytes\r\n", heap_stats.xSizeOfLargestFreeBlockInBytes);
}
```
