# FreeRTOS API Reference

This document contains the complete reference for the native FreeRTOS API and the CMSIS-RTOS v2 API.

---

## 1.1 Native FreeRTOS API (v10+)

### Task Management

```c
/* Dynamic task creation */
BaseType_t xTaskCreate(
    TaskFunction_t pxTaskCode,      // Task function pointer
    const char * const pcName,      // Task name
    const uint16_t usStackDepth,    // Stack depth (in words)
    void * const pvParameters,      // Parameter passed to the task
    UBaseType_t uxPriority,         // Task priority
    TaskHandle_t * const pxCreatedTask  // Task handle (output)
);

/* Static task creation (you provide the memory yourself) */
TaskHandle_t xTaskCreateStatic(
    TaskFunction_t pxTaskCode,
    const char * const pcName,
    uint32_t ulStackDepth,
    void * const pvParameters,
    UBaseType_t uxPriority,
    StackType_t * const pxStackBuffer,
    StaticTask_t * const pxTaskBuffer
);

/* Delete a task */
void vTaskDelete(TaskHandle_t xTask);

/* Task delay */
void vTaskDelay(const TickType_t xTicksToDelay);           // Relative delay
void vTaskDelayUntil(TickType_t *pxPreviousWakeTime,      // Absolute delay
                     const TickType_t xTimeIncrement);

/* Task priority */
void vTaskPrioritySet(TaskHandle_t xTask, UBaseType_t uxNewPriority);
UBaseType_t uxTaskPriorityGet(TaskHandle_t xTask);

/* Stack overflow detection */
UBaseType_t uxTaskGetStackHighWaterMark(TaskHandle_t xTask);
```

### Queue

```c
/* Create a queue */
QueueHandle_t xQueueCreate(UBaseType_t uxQueueLength,   // Queue length
                           UBaseType_t uxItemSize);    // Size of a single item

/* Send data (from a task) */
BaseType_t xQueueSend(QueueHandle_t xQueue,
                      const void *pvItemToQueue,
                      TickType_t xTicksToWait);

/* Receive data (from a task) */
BaseType_t xQueueReceive(QueueHandle_t xQueue,
                         void *pvBuffer,
                         TickType_t xTicksToWait);

/* Send from an ISR (with priority inheritance) */
BaseType_t xQueueSendFromISR(QueueHandle_t xQueue,
                             const void *pvItemToQueue,
                             BaseType_t *pxHigherPriorityTaskWoken);

/* Receive from an ISR */
BaseType_t xQueueReceiveFromISR(QueueHandle_t xQueue,
                                void *pvBuffer,
                                BaseType_t *pxHigherPriorityTaskWoken);
```

### Semaphore

```c
/* Create a binary semaphore */
SemaphoreHandle_t xSemaphoreCreateBinary(void);

/* Create a counting semaphore */
SemaphoreHandle_t xSemaphoreCreateCounting(UBaseType_t uxMaxCount,
                                           UBaseType_t uxInitialCount);

/* Create a mutex (with priority inheritance) */
SemaphoreHandle_t xSemaphoreCreateMutex(void);

/* Create a recursive mutex */
SemaphoreHandle_t xSemaphoreCreateRecursiveMutex(void);

/* Take a semaphore */
BaseType_t xSemaphoreTake(SemaphoreHandle_t xSemaphore,
                          TickType_t xTicksToWait);

/* Give a semaphore */
BaseType_t xSemaphoreGive(SemaphoreHandle_t xSemaphore);

/* Give from an ISR */
BaseType_t xSemaphoreGiveFromISR(SemaphoreHandle_t xSemaphore,
                                 BaseType_t *pxHigherPriorityTaskWoken);
```

### Event Groups

```c
/* Create an event group */
EventGroupHandle_t xEventGroupCreate(void);

/* Set event bits */
EventBits_t xEventGroupSetBits(EventGroupHandle_t xEventGroup,
                               const EventBits_t uxBitsToSet);

/* Clear event bits */
EventBits_t xEventGroupClearBits(EventGroupHandle_t xEventGroup,
                                 const EventBits_t uxBitsToClear);

/* Wait for event bits (AND/OR logic) */
EventBits_t xEventGroupWaitBits(const EventGroupHandle_t xEventGroup,
                                const EventBits_t uxBitsToWaitFor,
                                const BaseType_t xClearOnExit,
                                const BaseType_t xWaitForAllBits,
                                TickType_t xTicksToWait);

/* Set event bits from an ISR */
BaseType_t xEventGroupSetBitsFromISR(EventGroupHandle_t xEventGroup,
                                     const EventBits_t uxBitsToSet,
                                     BaseType_t *pxHigherPriorityTaskWoken);
```

### Task Notifications

```c
/* Send a notification (wakes the task directly) */
BaseType_t xTaskNotify(TaskHandle_t xTaskToNotify,
                       uint32_t ulValue,
                       eNotifyAction eAction);

/* Send a notification (ISR version) */
BaseType_t xTaskNotifyFromISR(TaskHandle_t xTaskToNotify,
                              uint32_t ulValue,
                              eNotifyAction eAction,
                              BaseType_t *pxHigherPriorityTaskWoken);

/* Receive a notification */
BaseType_t xTaskNotifyWait(uint32_t ulBitsToClearOnEntry,
                           uint32_t ulBitsToClearOnExit,
                           uint32_t *pulNotificationValue,
                           TickType_t xTicksToWait);
```

---

## 1.2 CMSIS-RTOS v2 API Mapping

### Threads (Tasks)

```c
/* Create a thread */
osThreadId_t osThreadNew(osThreadFunc_t func, void *arg,
                         const osThreadAttr_t *attr);

/* Thread delay */
osStatus_t osDelay(uint32_t ticks);
osStatus_t osDelayUntil(uint32_t *ticks, uint32_t period);

/* Terminate a thread */
osStatus_t osThreadTerminate(osThreadId_t thread_id);

/* Exit a thread */
void osThreadExit(void);
```

### Queue

```c
/* Create a queue */
osMessageQueueId_t osMessageQueueNew(uint32_t msg_count,
                                     uint32_t msg_size,
                                     const osMessageQueueAttr_t *attr);

/* Send a message */
osStatus_t osMessageQueuePut(osMessageQueueId_t mq_id,
                             const void *msg_ptr,
                             uint8_t msg_prio,
                             uint32_t timeout);

/* Receive a message */
osStatus_t osMessageQueueGet(osMessageQueueId_t mq_id,
                             void *msg_ptr,
                             uint8_t *msg_prio,
                             uint32_t timeout);
```

### Semaphore

```c
/* Create a semaphore */
osSemaphoreId_t osSemaphoreNew(uint32_t max_count,
                               uint32_t initial_count,
                               const osSemaphoreAttr_t *attr);

/* Acquire a semaphore */
osStatus_t osSemaphoreAcquire(osSemaphoreId_t semaphore_id,
                               uint32_t timeout);

/* Release a semaphore */
osStatus_t osSemaphoreRelease(osSemaphoreId_t semaphore_id);
```

### Mutex

```c
/* Create a mutex */
osMutexId_t osMutexNew(const osMutexAttr_t *attr);

/* Acquire a mutex */
osStatus_t osMutexAcquire(osMutexId_t mutex_id, uint32_t timeout);

/* Release a mutex */
osStatus_t osMutexRelease(osMutexId_t mutex_id);
```

### Events

```c
/* Create an event */
osEventFlagsId_t osEventFlagsNew(const osEventFlagsAttr_t *attr);

/* Set events */
uint32_t osEventFlagsSet(osEventFlagsId_t ef_id, uint32_t flags);

/* Clear events */
uint32_t osEventFlagsClear(osEventFlagsId_t ef_id, uint32_t flags);

/* Wait for events */
uint32_t osEventFlagsWait(osEventFlagsId_t ef_id,
                          uint32_t flags,
                          uint32_t options,
                          uint32_t timeout);
```

---

## Memory Optimization

### Static vs Dynamic Allocation

```c
/* Static task control block and stack */
StaticTask_t xTask1_TCB;
StackType_t xTask1_Stack[128];  /* 128 * 4 = 512 bytes */

/* Static queue control block */
typedef struct {
    uint8_t buffer[10][32];  /* 10 elements of 32 bytes each */
    StaticQueue_t queue;
} StaticQueue_t;

void vCreateStaticObjects(void)
{
    /* Create the static task */
    xTaskCreateStatic(vTaskFunction, "StaticTask1",
                      128, NULL, osPriorityNormal,
                      xTask1_Stack, &xTask1_TCB);

    /* Create the static queue */
    QueueHandle_t queue = xQueueCreateStatic(10, 32,
                                             g_queue_buffer,
                                             &g_queue_cb);
}
```

### Stack Estimation Method

```c
void vTaskMonitorStack(TaskHandle_t xTask)
{
    UBaseType_t high_water_mark;

    if (xTask == NULL)
    {
        high_water_mark = uxTaskGetStackHighWaterMark(NULL);
    }
    else
    {
        high_water_mark = uxTaskGetStackHighWaterMark(xTask);
    }

    printf("Stack remaining: %lu words (%lu bytes)\r\n",
           high_water_mark, high_water_mark * 4);

    if (high_water_mark < 20)
    {
        printf("Warning: the stack is almost exhausted!\r\n");
    }
}
```

### Stack Overflow Configuration

```c
/* FreeRTOSConfig.h */
#define configCHECK_FOR_STACK_OVERFLOW 2  /* Method 2 */

void vApplicationStackOverflowHook(TaskHandle_t xTask,
                                   char *pcTaskName)
{
    printf("Stack overflow: %s\r\n", pcTaskName);
    while (1);
}
```

### Heap Fragmentation Avoidance

```c
#define MEMPOOL_ITEM_SIZE 64
#define MEMPOOL_ITEMS 20

typedef struct {
    uint8_t data[MEMPOOL_ITEM_SIZE];
} MemPoolItem_t;

typedef struct {
    MemPoolItem_t items[MEMPOOL_ITEMS];
    uint8_t used[MEMPOOL_ITEMS];
} MemPool_t;

void *pvMemPoolAlloc(MemPool_t *pool)
{
    for (int i = 0; i < MEMPOOL_ITEMS; i++)
    {
        if (pool->used[i] == 0)
        {
            pool->used[i] = 1;
            memset(pool->items[i].data, 0, MEMPOOL_ITEM_SIZE);
            return pool->items[i].data;
        }
    }
    return NULL;
}

void vMemPoolFree(MemPool_t *pool, void *p)
{
    for (int i = 0; i < MEMPOOL_ITEMS; i++)
    {
        if (pool->items[i].data == p)
        {
            pool->used[i] = 0;
            break;
        }
    }
}
```
