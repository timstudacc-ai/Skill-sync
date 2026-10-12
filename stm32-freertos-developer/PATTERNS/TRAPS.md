# Common Pitfalls

This document describes common pitfalls in FreeRTOS development: priority inversion, stack overflow, deadlock and resource leaks.

---

## 3.1 Priority Inversion

### Problem description

```
High-priority task ────────────┐
                               │ waiting for the resource
Medium-priority task ────┐     │
                         │ holds the resource
Low-priority task ───────┘     │

Result: the high-priority task is blocked by the low-priority task,
and the medium-priority task cannot run either
```

### Hazards of priority inversion

1. The high-priority task waits for the low-priority task to release the resource
2. The medium-priority task preempts the CPU, so the low-priority task cannot run
3. The high-priority task is blocked indefinitely

### Solution: priority inheritance

```c
/* A mutex implements priority inheritance automatically */
SemaphoreHandle_t xMutex = xSemaphoreCreateMutex();

/* Use the mutex to protect the shared resource */
void vAccessResource(void)
{
    if (xSemaphoreTake(xMutex, pdMS_TO_TICKS(100)) == pdPASS)
    {
        /* Access the shared resource */
        // ...

        xSemaphoreGive(xMutex);
    }
}
```

### Complete example

```c
#include "main.h"
#include "FreeRTOS.h"
#include "semphr.h"

/* Task priority definitions */
#define PRIORITY_HIGH    3
#define PRIORITY_MEDIUM  2
#define PRIORITY_LOW     1

SemaphoreHandle_t g_resource_mutex;
uint32_t g_shared_resource = 0;

/* Low-priority task: holds the resource for a long time */
void vLowPriorityTask(void *pvParameters)
{
    while (1)
    {
        if (xSemaphoreTake(g_resource_mutex, portMAX_DELAY) == pdPASS)
        {
            g_shared_resource++;
            printf("Low-priority task: resource value = %lu\r\n", g_shared_resource);

            /* Simulate a long hold time */
            vTaskDelay(pdMS_TO_TICKS(2000));

            xSemaphoreGive(g_resource_mutex);
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

/* High-priority task: accesses the resource quickly */
void vHighPriorityTask(void *pvParameters)
{
    TickType_t start_time;

    while (1)
    {
        start_time = xTaskGetTickCount();

        if (xSemaphoreTake(g_resource_mutex, pdMS_TO_TICKS(500)) == pdPASS)
        {
            g_shared_resource++;
            printf("High-priority task: resource value = %lu\r\n", g_shared_resource);
            xSemaphoreGive(g_resource_mutex);
        }
        else
        {
            printf("High-priority task: wait timed out\r\n");
        }

        printf("High-priority task: wait time = %lu ms\r\n",
               pdTICKS_TO_MS(xTaskGetTickCount() - start_time));

        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

/* Fix the priority inversion problem */
void vPriorityInversionDemo(void)
{
    /* Use a mutex, which enables priority inheritance automatically */
    g_resource_mutex = xSemaphoreCreateMutex();

    /* Create the tasks */
    xTaskCreate(vLowPriorityTask, "Low", 128, NULL,
                PRIORITY_LOW, NULL);
    xTaskCreate(vHighPriorityTask, "High", 128, NULL,
                PRIORITY_HIGH, NULL);
}
```

### How priority inheritance works

```c
/* Internal implementation of xSemaphoreCreateMutex */
SemaphoreHandle_t xSemaphoreCreateMutex(void)
{
    SemaphoreHandle_t xSemaphore;

    /* Create a binary semaphore */
    xSemaphore = xSemaphoreCreateBinary();

    if (xSemaphore != NULL)
    {
        /* Set it to mutex mode, which enables priority inheritance */
        xSemaphore->ucType = queueQUEUE_TYPE_MUTEX;

        /* When a high-priority task waits for the mutex, raise the priority of the owning task */
        prvLockMutex(xSemaphore);
    }

    return xSemaphore;
}
```

---

## 3.2 Stack Overflow

### Detection method

```c
/* FreeRTOSConfig.h */
#define configCHECK_FOR_STACK_OVERFLOW 2  /* Method 2: check the stack pointer */

void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName)
{
    printf("Stack overflow! Task: %s\r\n", pcTaskName);

    /* Enter an infinite loop to ease debugging */
    while (1)
    {
        HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
```

### Comparison of detection methods

| Method | Description | Configuration |
|------|------|------|
| Method 1 | Checks whether the stack pointer has gone out of range | `configCHECK_FOR_STACK_OVERFLOW = 1` |
| Method 2 | Checks the stack pointer and the stack contents | `configCHECK_FOR_STACK_OVERFLOW = 2` |
| Method 3 | Checked during each task context switch | `configCHECK_FOR_STACK_OVERFLOW = 3` |

### Preventive measures

```c
/* 1. Set a reasonable stack size */
#define TASK_STACK_SIZE 256  /* 256 words = 1024 bytes */

/* 2. Avoid allocating large arrays on the stack */
#define LARGE_BUFFER_SIZE 1024

/* Wrong: allocating a large array on the stack */
void vBadTask(void *pvParameters)
{
    uint8_t large_buffer[1024];  /* May overflow */
    // ...
}

/* Correct: static allocation */
static uint8_t g_buffer[LARGE_BUFFER_SIZE];  /* Static */

void vGoodTask(void *pvParameters)
{
    /* Use the static buffer */
    memcpy(g_buffer, source, LARGE_BUFFER_SIZE);
}

/* 3. Check stack usage regularly */
void vStackMonitorTask(void *pvParameters)
{
    TaskHandle_t tasks[10];
    UBaseType_t count;

    while (1)
    {
        count = uxTaskGetSystemState(tasks, 10, NULL);

        for (UBaseType_t i = 0; i < count; i++)
        {
            UBaseType_t watermark = uxTaskGetStackHighWaterMark(tasks[i]);
            TaskStatus_t *status = pxTaskGetTaskStatus(tasks[i]);

            printf("Task %s: %lu words of stack remaining\r\n",
                   status->pcTaskName, watermark);

            /* Warning */
            if (watermark < 20)
            {
                printf("Warning: the stack of %s is almost exhausted!\r\n", status->pcTaskName);
            }
        }

        vTaskDelay(pdMS_TO_TICKS(5000));
    }
}
```

### Stack size estimation rules

```c
/* Task stack estimation (in words) */
#define TASK_STACK_DEPTH_BASE    128   /* Base requirement */
#define TASK_STACK_DEPTH_UART    256   /* UART handling task */
#define TASK_STACK_DEPTH_COM     512   /* Communication task */
#define TASK_STACK_DEPTH_LARGE   1024  /* Complex task */

/* Rules:
 * - Simple loop task: 128-256 words
 * - With string processing: +64-128 words
 * - With recursive calls: +256 words
 * - With a large local array: + the array size
 * - Using printf: +50-100 words
 */

/* Example: a complex task */
xTaskCreate(vComplexTask, "Complex", 512,  /* 512 word stack */
            NULL, osPriorityNormal, NULL);
```

---

## 3.3 Deadlock

### Problem description

Two or more tasks each wait for the other to release a resource, which results in permanent blocking.

### The four necessary conditions for deadlock

1. **Mutual exclusion**: a resource cannot be shared, it can only be held exclusively
2. **Hold and wait**: a task holds a resource while waiting for other resources
3. **No preemption**: a resource cannot be taken away by force
4. **Circular wait**: the tasks form a wait cycle

### Example

```c
/* Deadlock example */
void vDeadlockExample(void)
{
    SemaphoreHandle_t mutex_a = xSemaphoreCreateMutex();
    SemaphoreHandle_t mutex_b = xSemaphoreCreateMutex();

    /* Task 1: takes A first, then B */
    void vTask1(void *pvParameters)
    {
        while (1)
        {
            xSemaphoreTake(mutex_a, portMAX_DELAY);
            vTaskDelay(1);  /* Yield the CPU */
            xSemaphoreTake(mutex_b, portMAX_DELAY);  /* Wait for B */

            // Use the resources

            xSemaphoreGive(mutex_b);
            xSemaphoreGive(mutex_a);
        }
    }

    /* Task 2: takes B first, then A */
    void vTask2(void *pvParameters)
    {
        while (1)
        {
            xSemaphoreTake(mutex_b, portMAX_DELAY);
            vTaskDelay(1);  /* Yield the CPU */
            xSemaphoreTake(mutex_a, portMAX_DELAY);  /* Wait for A */

            // Use the resources

            xSemaphoreGive(mutex_a);
            xSemaphoreGive(mutex_b);
        }
    }

    /* A deadlock can occur:
     * 1. Task 1 takes A, task 2 takes B
     * 2. Task 1 tries to take B (held by task 2)
     * 3. Task 2 tries to take A (held by task 1)
     * 4. Both wait forever
     */
}
```

### Solutions

```c
/* Solution 1: a consistent acquisition order */
void vTask1Fixed(void *pvParameters)
{
    while (1)
    {
        /* Always take A first, then B */
        xSemaphoreTake(mutex_a, portMAX_DELAY);
        xSemaphoreTake(mutex_b, portMAX_DELAY);

        // Use the resources

        xSemaphoreGive(mutex_b);
        xSemaphoreGive(mutex_a);
    }
}

void vTask2Fixed(void *pvParameters)
{
    while (1)
    {
        /* Also take A first, then B */
        xSemaphoreTake(mutex_a, portMAX_DELAY);
        xSemaphoreTake(mutex_b, portMAX_DELAY);

        // Use the resources

        xSemaphoreGive(mutex_b);
        xSemaphoreGive(mutex_a);
    }
}

/* Solution 2: use a single mutex */
void vTaskWithSingleMutex(void *pvParameters)
{
    SemaphoreHandle_t resource_mutex = xSemaphoreCreateMutex();

    while (1)
    {
        /* Use only one mutex */
        if (xSemaphoreTake(resource_mutex, portMAX_DELAY) == pdPASS)
        {
            /* Access all of the shared resources */
            // access_resource_a();
            // access_resource_b();

            xSemaphoreGive(resource_mutex);
        }
    }
}

/* Solution 3: acquisition with a timeout */
void vTaskWithTimeout(void *pvParameters)
{
    while (1)
    {
        if (xSemaphoreTake(mutex_a, pdMS_TO_TICKS(100)) == pdPASS)
        {
            if (xSemaphoreTake(mutex_b, pdMS_TO_TICKS(100)) == pdPASS)
            {
                // Use the resources
                xSemaphoreGive(mutex_b);
            }
            else
            {
                /* Timed out, release the lock that was already taken */
                printf("Timed out taking mutex_b, releasing mutex_a\r\n");
                xSemaphoreGive(mutex_a);
            }
        }
        else
        {
            vTaskDelay(pdMS_TO_TICKS(50));
        }
    }
}
```

---

## 3.4 Resource Leaks

### Problem description

Resources (memory, semaphores, queues) are not released correctly, which exhausts the system resources.

### Memory leaks

```c
/* Memory leak example */
void vMemoryLeakTask(void *pvParameters)
{
    while (1)
    {
        /* Allocate memory on every iteration but never free it */
        char *buffer = pvPortMalloc(256);
        if (buffer != NULL)
        {
            process_data(buffer);
            /* Forgot vPortFree(buffer); */
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

/* Correct approach: allocate outside the task */
char *g_buffer = NULL;

void vNoLeakTask(void *pvParameters)
{
    g_buffer = pvPortMalloc(256);

    if (g_buffer != NULL)
    {
        while (1)
        {
            process_data(g_buffer);
            vTaskDelay(pdMS_TO_TICKS(100));
        }

        vPortFree(g_buffer);  /* Free it when the task is deleted */
    }
}
```

### Queue leaks

```c
/* Queue leak example */
void vQueueLeakTask(void *pvParameters)
{
    QueueHandle_t local_queue;

    while (1)
    {
        /* Create a new queue on every iteration */
        local_queue = xQueueCreate(10, sizeof(uint32_t));

        /* Send data */
        uint32_t data = HAL_GetTick();
        xQueueSend(local_queue, &data, 0);

        vTaskDelay(pdMS_TO_TICKS(1000));

        /* Forgot to delete the queue */
        /* vQueueDelete(local_queue); */
    }
}

/* Correct approach: use a global queue */
QueueHandle_t g_global_queue;

void vCorrectQueueTask(void *pvParameters)
{
    /* Create the queue during initialisation */
    g_global_queue = xQueueCreate(10, sizeof(uint32_t));

    while (1)
    {
        uint32_t data = HAL_GetTick();
        xQueueSend(g_global_queue, &data, 0);

        vTaskDelay(pdMS_TO_TICKS(1000));
    }

    /* No deletion is needed because the queue is global */
}

/* Or clean up when the task ends */
void vTaskWithCleanup(void *pvParameters)
{
    QueueHandle_t local_queue = xQueueCreate(10, sizeof(uint32_t));

    if (local_queue != NULL)
    {
        while (1)
        {
            /* Use the queue */
            if (should_exit())
            {
                break;
            }
        }

        /* Clean up before the task ends */
        vQueueDelete(local_queue);
    }

    vTaskDelete(NULL);  /* Delete itself */
}
```

### Semaphore leaks

```c
/* Semaphore leak example */
void vSemaphoreLeakTask(void *pvParameters)
{
    while (1)
    {
        SemaphoreHandle_t sem = xSemaphoreCreateBinary();

        /* Use the semaphore */
        xSemaphoreTake(sem, portMAX_DELAY);

        vTaskDelay(pdMS_TO_TICKS(1000));

        /* Forgot to delete it */
        /* vSemaphoreDelete(sem); */
    }
}

/* Correct approach: use a global semaphore */
SemaphoreHandle_t g_button_sem;

void vButtonTaskCorrect(void *pvParameters)
{
    /* Create it during initialisation */
    g_button_sem = xSemaphoreCreateBinary();

    while (1)
    {
        if (xSemaphoreTake(g_button_sem, portMAX_DELAY) == pdTRUE)
        {
            /* Handle the button event */
        }
    }
}

/* Cleanup function */
void vCleanup(void)
{
    if (g_button_sem != NULL)
    {
        vSemaphoreDelete(g_button_sem);
        g_button_sem = NULL;
    }
}
```

### Resource management best practices

```c
/* 1. Create resources during initialisation */
typedef struct {
    QueueHandle_t queue;
    SemaphoreHandle_t mutex;
    TaskHandle_t task;
} AppResources_t;

AppResources_t g_app_resources;

void vAppInit(void)
{
    /* Create all resources */
    g_app_resources.queue = xQueueCreate(10, sizeof(uint32_t));
    g_app_resources.mutex = xSemaphoreCreateMutex();
    xTaskCreate(vTask, "App", 256, NULL, 2, &g_app_resources.task);
}

/* 2. Release resources during cleanup */
void vAppCleanup(void)
{
    if (g_app_resources.task != NULL)
    {
        vTaskDelete(g_app_resources.task);
        g_app_resources.task = NULL;
    }

    if (g_app_resources.mutex != NULL)
    {
        vSemaphoreDelete(g_app_resources.mutex);
        g_app_resources.mutex = NULL;
    }

    if (g_app_resources.queue != NULL)
    {
        vQueueDelete(g_app_resources.queue);
        g_app_resources.queue = NULL;
    }
}
```
