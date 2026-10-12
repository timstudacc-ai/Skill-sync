# Basic Examples

This document contains complete example code for the basic FreeRTOS components.

---

## 1.1 Dynamic Task Creation

```c
#include "main.h"
#include "FreeRTOS.h"
#include "task.h"

/* Task function */
void vTask1(void *pvParameters)
{
    while (1)
    {
        /* Task code */
        HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);
        printf("Task1 running\r\n");

        /* Delay 500ms */
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

void vTask2(void *pvParameters)
{
    while (1)
    {
        /* Task code */
        HAL_GPIO_TogglePin(LED2_GPIO_Port, LED2_Pin);
        printf("Task2 running\r\n");

        /* Delay 1000ms */
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    MX_GPIO_Init();

    /* Create the tasks */
    BaseType_t ret1 = xTaskCreate(vTask1, "Task1",
                                  128,  /* Stack depth (words) */
                                  NULL, /* Parameter */
                                  2,    /* Priority */
                                  NULL);/* Handle */

    BaseType_t ret2 = xTaskCreate(vTask2, "Task2",
                                  128,
                                  NULL,
                                  2,
                                  NULL);

    if (ret1 == pdPASS && ret2 == pdPASS)
    {
        printf("Tasks created successfully, starting the scheduler\r\n");
        vTaskStartScheduler();
    }
    else
    {
        printf("Task creation failed\r\n");
    }

    while (1);
}
```

---

## 1.2 Static Task Creation

```c
#include "main.h"
#include "FreeRTOS.h"
#include "task.h"

/* Static task control blocks and stacks (global variables) */
static StaticTask_t xTask1_TCB;
static StackType_t xTask1_Stack[128];

static StaticTask_t xTask2_TCB;
static StackType_t xTask2_Stack[256];

/* Task function */
void vTask1(void *pvParameters)
{
    while (1)
    {
        printf("Static task 1 running\r\n");
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

void vTask2(void *pvParameters)
{
    while (1)
    {
        printf("Static task 2 running\r\n");
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    MX_GPIO_Init();

    /* Create the static tasks */
    TaskHandle_t handle1 = xTaskCreateStatic(vTask1, "Task1",
                                             128,  /* Stack depth (words) */
                                             NULL, /* Parameter */
                                             2,    /* Priority */
                                             xTask1_Stack,
                                             &xTask1_TCB);

    TaskHandle_t handle2 = xTaskCreateStatic(vTask2, "Task2",
                                             256,
                                             NULL,
                                             2,
                                             xTask2_Stack,
                                             &xTask2_TCB);

    if (handle1 != NULL && handle2 != NULL)
    {
        printf("Static tasks created successfully, starting the scheduler\r\n");
        vTaskStartScheduler();
    }
    else
    {
        printf("Static task creation failed\r\n");
    }

    while (1);
}
```

---

## 1.3 Queue (Producer-Consumer)

```c
#include "main.h"
#include "FreeRTOS.h"
#include "queue.h"

/* Data frame definition */
typedef struct {
    uint32_t id;
    float value;
    uint32_t timestamp;
} DataFrame_t;

/* Global queue */
QueueHandle_t g_data_queue;

/* Producer task */
void vProducerTask(void *pvParameters)
{
    DataFrame_t frame;
    uint32_t count = 0;

    while (1)
    {
        /* Produce the data */
        frame.id = count;
        frame.value = (float)(count * 0.1f);
        frame.timestamp = HAL_GetTick();

        /* Send it to the queue */
        if (xQueueSend(g_data_queue, &frame, 0) == pdTRUE)
        {
            printf("Producer: sent data #%lu\r\n", count);
        }
        else
        {
            printf("Producer: queue full, discarding data\r\n");
        }

        count++;
        vTaskDelay(pdMS_TO_TICKS(200));
    }
}

/* Consumer task */
void vConsumerTask(void *pvParameters)
{
    DataFrame_t frame;

    while (1)
    {
        /* Receive data from the queue (wait forever) */
        if (xQueueReceive(g_data_queue, &frame, portMAX_DELAY) == pdTRUE)
        {
            printf("Consumer: received data #%lu, value=%.2f, time=%lu\r\n",
                   frame.id, frame.value, frame.timestamp);
        }
    }
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();

    /* Create the queue: 10 elements, each sizeof(DataFrame_t) bytes */
    g_data_queue = xQueueCreate(10, sizeof(DataFrame_t));

    if (g_data_queue != NULL)
    {
        /* Create the tasks */
        xTaskCreate(vProducerTask, "Producer", 128, NULL, 2, NULL);
        xTaskCreate(vConsumerTask, "Consumer", 128, NULL, 2, NULL);

        vTaskStartScheduler();
    }
    else
    {
        printf("Queue creation failed\r\n");
    }

    while (1);
}
```

---

## 1.4 Binary Semaphore (Task Synchronisation)

```c
#include "main.h"
#include "FreeRTOS.h"
#include "semphr.h"

/* Binary semaphore */
SemaphoreHandle_t g_button_sem;

/* Button interrupt callback */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if (GPIO_Pin == BUTTON_Pin)
    {
        BaseType_t xHigherPriorityTaskWoken = pdFALSE;

        /* Give the semaphore (from the ISR) */
        xSemaphoreGiveFromISR(g_button_sem, &xHigherPriorityTaskWoken);

        /* If a higher-priority task was woken, perform a context switch */
        portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
    }
}

/* Button handling task */
void vButtonTask(void *pvParameters)
{
    while (1)
    {
        /* Wait for the semaphore (blocking) */
        if (xSemaphoreTake(g_button_sem, portMAX_DELAY) == pdTRUE)
        {
            printf("Button pressed!\r\n");

            /* Execute the button handling logic */
            HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);
        }
    }
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    MX_GPIO_Init();

    /* Create the binary semaphore */
    g_button_sem = xSemaphoreCreateBinary();

    if (g_button_sem != NULL)
    {
        xTaskCreate(vButtonTask, "ButtonTask", 128, NULL, 2, NULL);
        vTaskStartScheduler();
    }

    while (1);
}
```

---

## 1.5 Mutex (Shared Resource Protection)

```c
#include "main.h"
#include "FreeRTOS.h"
#include "semphr.h"

/* Mutex */
SemaphoreHandle_t g_uart_mutex;

/* Shared resource: UART */
UART_HandleTypeDef huart1;

/* Thread-safe print function */
void thread_safe_print(char *str)
{
    /* Take the mutex */
    if (xSemaphoreTake(g_uart_mutex, pdMS_TO_TICKS(100)) == pdTRUE)
    {
        /* Access the shared resource */
        printf("%s", str);

        /* Give the mutex */
        xSemaphoreGive(g_uart_mutex);
    }
}

/* Task 1: uses the UART */
void vTaskUart1(void *pvParameters)
{
    while (1)
    {
        thread_safe_print("Task1 is using the UART\r\n");
        vTaskDelay(pdMS_TO_TICKS(300));
    }
}

/* Task 2: uses the UART */
void vTaskUart2(void *pvParameters)
{
    while (1)
    {
        thread_safe_print("Task2 is using the UART\r\n");
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();

    /* Create the mutex (with priority inheritance) */
    g_uart_mutex = xSemaphoreCreateMutex();

    if (g_uart_mutex != NULL)
    {
        xTaskCreate(vTaskUart1, "UartTask1", 128, NULL, 2, NULL);
        xTaskCreate(vTaskUart2, "UartTask2", 128, NULL, 2, NULL);

        vTaskStartScheduler();
    }

    while (1);
}
```

---

## 1.6 Event Group

```c
#include "main.h"
#include "FreeRTOS.h"
#include "event_groups.h"

/* Event bit definitions */
#define EVENT_BIT_0      (1 << 0)  /* 0x01 */
#define EVENT_BIT_1      (1 << 1)  /* 0x02 */
#define EVENT_BIT_2      (1 << 2)  /* 0x04 */
#define EVENT_ALL_BITS   (EVENT_BIT_0 | EVENT_BIT_1 | EVENT_BIT_2)

/* Event group */
EventGroupHandle_t g_event_group;

/* Task 1: sets EVENT_BIT_0 */
void vTask1(void *pvParameters)
{
    while (1)
    {
        vTaskDelay(pdMS_TO_TICKS(1000));
        xEventGroupSetBits(g_event_group, EVENT_BIT_0);
        printf("Task1 set EVENT_BIT_0\r\n");
    }
}

/* Task 2: sets EVENT_BIT_1 */
void vTask2(void *pvParameters)
{
    while (1)
    {
        vTaskDelay(pdMS_TO_TICKS(1500));
        xEventGroupSetBits(g_event_group, EVENT_BIT_1);
        printf("Task2 set EVENT_BIT_1\r\n");
    }
}

/* Task 3: waits for all event bits */
void vTask3(void *pvParameters)
{
    EventBits_t bits;

    while (1)
    {
        /* Wait for all bits (AND logic) */
        bits = xEventGroupWaitBits(g_event_group,
                                   EVENT_ALL_BITS,
                                   pdTRUE,   /* Clear the bits on exit */
                                   pdTRUE,   /* Wait for all bits (AND) */
                                   portMAX_DELAY);

        if ((bits & EVENT_ALL_BITS) == EVENT_ALL_BITS)
        {
            printf("Task3: all events received! bits=0x%02X\r\n", (unsigned int)bits);
        }
    }
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();

    /* Create the event group */
    g_event_group = xEventGroupCreate();

    if (g_event_group != NULL)
    {
        xTaskCreate(vTask1, "Task1", 128, NULL, 2, NULL);
        xTaskCreate(vTask2, "Task2", 128, NULL, 2, NULL);
        xTaskCreate(vTask3, "Task3", 128, NULL, 3, NULL);  /* High priority */

        vTaskStartScheduler();
    }

    while (1);
}
```

---

## 1.7 Task Notifications

```c
#include "main.h"
#include "FreeRTOS.h"
#include "task.h"

/* Task notification handle */
TaskHandle_t g_notify_task_handle;

/* The task that sends the notifications */
void vSenderTask(void *pvParameters)
{
    uint32_t count = 0;

    while (1)
    {
        vTaskDelay(pdMS_TO_TICKS(500));

        /* Send a notification (with an incrementing value) */
        xTaskNotify(g_notify_task_handle, count, eSetValueWithOverwrite);

        printf("Sent notification: %lu\r\n", count);
        count++;
    }
}

/* The task that receives the notifications */
void vReceiverTask(void *pvParameters)
{
    uint32_t notification_value;

    while (1)
    {
        /* Wait for a notification (blocking) */
        if (xTaskNotifyWait(0, 0xFFFFFFFF, &notification_value,
                            portMAX_DELAY) == pdTRUE)
        {
            printf("Received notification: %lu\r\n", notification_value);
        }
    }
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();

    /* Create the receiver task and keep its handle */
    xTaskCreate(vReceiverTask, "Receiver", 128, NULL, 2,
                &g_notify_task_handle);

    xTaskCreate(vSenderTask, "Sender", 128, NULL, 2, NULL);

    vTaskStartScheduler();

    while (1);
}
```
