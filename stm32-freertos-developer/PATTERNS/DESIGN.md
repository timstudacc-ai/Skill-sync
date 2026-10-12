# Design Patterns

This document describes how to implement design patterns such as producer-consumer, publish-subscribe, state machine and resource pool.

---

## 1.1 Producer-Consumer

### Pattern description

The producer-consumer pattern is one of the most commonly used patterns in embedded systems. It is suitable for:
- Separating data acquisition from data processing
- Buffering sensor data
- Receiving and parsing serial port data

### Implementation architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Producer   │ ---> │    Queue    │ ---> │  Consumer   │
│    task     │      │   buffers   │      │    task     │
│collect data │      │    data     │      │process data │
└─────────────┘      └─────────────┘      └─────────────┘
```

### Complete implementation

```c
#include "main.h"
#include "FreeRTOS.h"
#include "queue.h"
#include "semphr.h"

#define QUEUE_LENGTH 20
#define QUEUE_ITEM_SIZE sizeof(uint32_t)

typedef struct {
    uint32_t sensor_id;
    uint32_t value;
    uint32_t timestamp;
} SensorMessage_t;

/* Queue and semaphore */
QueueHandle_t g_sensor_queue;
SemaphoreHandle_t g_data_ready_sem;

/* Producer task: simulates sensor acquisition */
void vSensorTask(void *pvParameters)
{
    SensorMessage_t msg;
    uint32_t count = 0;

    while (1)
    {
        /* Acquire the sensor data */
        msg.sensor_id = 1;
        msg.value = HAL_ADC_GetValue(&hadc1);  /* Assume the ADC is configured */
        msg.timestamp = HAL_GetTick();

        /* Send the data to the queue */
        if (xQueueSend(g_sensor_queue, &msg, 0) == pdTRUE)
        {
            /* Signal that the data is ready */
            xSemaphoreGive(g_data_ready_sem);
        }

        count++;
        vTaskDelay(pdMS_TO_TICKS(100));  /* 10Hz sampling */
    }
}

/* Consumer task: processes the data */
void vProcessTask(void *pvParameters)
{
    SensorMessage_t msg;

    while (1)
    {
        /* Wait for the data-ready signal */
        if (xSemaphoreTake(g_data_ready_sem, portMAX_DELAY) == pdTRUE)
        {
            /* Get the data from the queue */
            while (xQueueReceive(g_sensor_queue, &msg, 0) == pdTRUE)
            {
                /* Process the data */
                printf("Sensor #%lu: %lu (time: %lu)\r\n",
                       msg.sensor_id, msg.value, msg.timestamp);
            }
        }
    }
}

void vProducerConsumerDemo(void)
{
    /* Create the queue */
    g_sensor_queue = xQueueCreate(QUEUE_LENGTH, QUEUE_ITEM_SIZE);

    /* Create the binary semaphore */
    g_data_ready_sem = xSemaphoreCreateBinary();

    /* Create the tasks */
    xTaskCreate(vSensorTask, "Sensor", 128, NULL, 2, NULL);
    xTaskCreate(vProcessTask, "Process", 128, NULL, 2, NULL);
}
```

### Variant: multiple producers and multiple consumers

```c
/* Several producers share the queue */
void vSensorTask1(void *pvParameters)
{
    SensorMessage_t msg;
    msg.sensor_id = 1;
    while (1) {
        msg.value = read_sensor1();
        xQueueSend(g_sensor_queue, &msg, 0);
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

void vSensorTask2(void *pvParameters)
{
    SensorMessage_t msg;
    msg.sensor_id = 2;
    while (1) {
        msg.value = read_sensor2();
        xQueueSend(g_sensor_queue, &msg, 0);
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

/* The consumer distinguishes the data source by sensor_id */
void vProcessTaskMulti(void *pvParameters)
{
    SensorMessage_t msg;
    while (1) {
        xQueueReceive(g_sensor_queue, &msg, portMAX_DELAY);

        switch (msg.sensor_id) {
            case 1:
                process_sensor1_data(msg.value);
                break;
            case 2:
                process_sensor2_data(msg.value);
                break;
        }
    }
}
```

---

## 1.2 Publish-Subscribe

### Pattern description

The publish-subscribe pattern is implemented with event groups. It is suitable for:
- Triggering on multiple conditions
- Broadcast notification
- State machine events

### Implementation code

```c
#include "main.h"
#include "FreeRTOS.h"
#include "event_groups.h"

/* Event bit definitions */
#define EVENT_BUTTON_PRESS   (1 << 0)
#define EVENT_SENSOR_ALARM   (1 << 1)
#define EVENT_TIMEOUT        (1 << 2)
#define EVENT_ALL            (EVENT_BUTTON_PRESS | EVENT_SENSOR_ALARM | EVENT_TIMEOUT)

/* Event group */
EventGroupHandle_t g_event_group;

/* Subscriber task */
void vAlarmTask(void *pvParameters)
{
    EventBits_t bits;

    while (1)
    {
        /* Subscribe to all events */
        bits = xEventGroupWaitBits(g_event_group,
                                   EVENT_ALL,
                                   pdTRUE,   /* Clear the bits */
                                   pdFALSE,  /* Any event (OR) */
                                   portMAX_DELAY);

        if (bits & EVENT_BUTTON_PRESS)
        {
            printf("Alarm task: button event received\r\n");
        }

        if (bits & EVENT_SENSOR_ALARM)
        {
            printf("Alarm task: sensor alarm received\r\n");
            /* Trigger the alarm action */
        }
    }
}

/* Publisher task */
void vButtonTask(void *pvParameters)
{
    while (1)
    {
        if (HAL_GPIO_ReadPin(BUTTON_GPIO_Port, BUTTON_Pin) == GPIO_PIN_RESET)
        {
            /* Debounce delay */
            vTaskDelay(pdMS_TO_TICKS(50));
            if (HAL_GPIO_ReadPin(BUTTON_GPIO_Port, BUTTON_Pin) == GPIO_PIN_RESET)
            {
                /* Publish the button event */
                xEventGroupSetBits(g_event_group, EVENT_BUTTON_PRESS);
                printf("Button task: publishing the button event\r\n");
            }

            /* Wait for release */
            while (HAL_GPIO_ReadPin(BUTTON_GPIO_Port, BUTTON_Pin) == GPIO_PIN_RESET)
            {
                vTaskDelay(pdMS_TO_TICKS(10));
            }
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

void vPublishSubscribeDemo(void)
{
    g_event_group = xEventGroupCreate();

    xTaskCreate(vAlarmTask, "Alarm", 128, NULL, 2, NULL);
    xTaskCreate(vButtonTask, "Button", 128, NULL, 2, NULL);
}
```

---

## 1.3 State Machine

### Pattern description

The state machine pattern is suitable for:
- Protocol parsing
- Business process control
- Mode switching

### Implementation code

```c
#include "main.h"
#include "FreeRTOS.h"

/* State machine state definitions */
typedef enum {
    STATE_IDLE = 0,
    STATE_INIT,
    STATE_CONNECTING,
    STATE_CONNECTED,
    STATE_DISCONNECTED,
    STATE_ERROR
} AppState_t;

/* Event definitions */
typedef enum {
    EVENT_NONE = 0,
    EVENT_START,
    EVENT_CONNECT,
    EVENT_DISCONNECT,
    EVENT_TIMEOUT,
    EVENT_ERROR
} AppEvent_t;

/* State machine control block */
typedef struct {
    AppState_t current_state;
    AppState_t next_state;
    AppEvent_t pending_event;
    TickType_t last_state_time;
} StateMachine_t;

/* State machine instance */
static StateMachine_t g_sm;

/* State handler functions */
static void handle_idle(AppEvent_t event)
{
    switch (event) {
        case EVENT_START:
            printf("State machine: switching from IDLE to INIT\r\n");
            g_sm.next_state = STATE_INIT;
            break;
        default:
            break;
    }
}

static void handle_init(AppEvent_t event)
{
    switch (event) {
        case EVENT_CONNECT:
            printf("State machine: initialisation complete, starting to connect\r\n");
            g_sm.next_state = STATE_CONNECTING;
            break;
        case EVENT_ERROR:
            printf("State machine: initialisation failed, entering the error state\r\n");
            g_sm.next_state = STATE_ERROR;
            break;
        default:
            break;
    }
}

static void handle_connecting(AppEvent_t event)
{
    switch (event) {
        case EVENT_TIMEOUT:
            printf("State machine: connection timed out, retrying\r\n");
            /* Reconnection logic */
            g_sm.next_state = STATE_CONNECTING;
            break;
        case EVENT_CONNECT:
            printf("State machine: connected successfully\r\n");
            g_sm.next_state = STATE_CONNECTED;
            break;
        default:
            break;
    }
}

static void handle_connected(AppEvent_t event)
{
    switch (event) {
        case EVENT_DISCONNECT:
            printf("State machine: disconnecting\r\n");
            g_sm.next_state = STATE_DISCONNECTED;
            break;
        case EVENT_ERROR:
            printf("State machine: connection error\r\n");
            g_sm.next_state = STATE_ERROR;
            break;
        default:
            break;
    }
}

/* State machine handler function */
void vStateMachineTask(void *pvParameters)
{
    /* Initialise the state machine */
    g_sm.current_state = STATE_IDLE;
    g_sm.next_state = STATE_IDLE;
    g_sm.pending_event = EVENT_NONE;

    while (1)
    {
        /* Handle the current state */
        switch (g_sm.current_state) {
            case STATE_IDLE:
                handle_idle(g_sm.pending_event);
                break;
            case STATE_INIT:
                handle_init(g_sm.pending_event);
                break;
            case STATE_CONNECTING:
                handle_connecting(g_sm.pending_event);
                break;
            case STATE_CONNECTED:
                handle_connected(g_sm.pending_event);
                break;
            default:
                break;
        }

        /* State transition */
        if (g_sm.next_state != g_sm.current_state)
        {
            printf("State transition: %d -> %d\r\n",
                   g_sm.current_state, g_sm.next_state);
            g_sm.current_state = g_sm.next_state;
            g_sm.last_state_time = xTaskGetTickCount();
        }

        /* Clear the event */
        g_sm.pending_event = EVENT_NONE;

        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

/* Event submission interface */
void StateMachine_SendEvent(AppEvent_t event)
{
    g_sm.pending_event = event;
}
```

---

## 1.4 Resource Pool Management

### Pattern description

The resource pool pattern is suitable for:
- Managing fixed-size buffers
- Reusing dynamic objects
- Avoiding memory fragmentation

### Implementation code

```c
#include "main.h"
#include "FreeRTOS.h"
#include "semphr.h"

#define BUFFER_POOL_SIZE 10
#define BUFFER_SIZE 128

/* Buffer item */
typedef struct {
    uint8_t data[BUFFER_SIZE];
    uint32_t length;
    uint32_t timestamp;
} BufferItem_t;

/* Buffer pool */
typedef struct {
    BufferItem_t items[BUFFER_POOL_SIZE];
    uint8_t used[BUFFER_POOL_SIZE];
    SemaphoreHandle_t mutex;
    SemaphoreHandle_t free_count;
} BufferPool_t;

/* Global buffer pool */
static BufferPool_t g_buffer_pool;

/* Initialise the buffer pool */
void BufferPool_Init(void)
{
    memset(&g_buffer_pool, 0, sizeof(g_buffer_pool));
    g_buffer_pool.mutex = xSemaphoreCreateMutex();
    g_buffer_pool.free_count = xSemaphoreCreateCounting(BUFFER_POOL_SIZE,
                                                        BUFFER_POOL_SIZE);

    /* All buffers are available initially */
    for (int i = 0; i < BUFFER_POOL_SIZE; i++)
    {
        xSemaphoreGive(g_buffer_pool.free_count);
    }
}

/* Take a buffer from the pool */
BufferItem_t *BufferPool_Alloc(void)
{
    BufferItem_t *item = NULL;

    /* Wait for a free buffer */
    if (xSemaphoreTake(g_buffer_pool.free_count, pdMS_TO_TICKS(100)) == pdFALSE)
    {
        return NULL;  /* Timed out, no buffer available */
    }

    /* Take the mutex */
    if (xSemaphoreTake(g_buffer_pool.mutex, pdMS_TO_TICKS(50)) == pdFALSE)
    {
        /* Give the semaphore back */
        xSemaphoreGive(g_buffer_pool.free_count);
        return NULL;
    }

    /* Find a free buffer */
    for (int i = 0; i < BUFFER_POOL_SIZE; i++)
    {
        if (g_buffer_pool.used[i] == 0)
        {
            g_buffer_pool.used[i] = 1;
            item = &g_buffer_pool.items[i];
            break;
        }
    }

    xSemaphoreGive(g_buffer_pool.mutex);

    return item;
}

/* Return the buffer to the pool */
void BufferPool_Free(BufferItem_t *item)
{
    if (item == NULL) return;

    xSemaphoreTake(g_buffer_pool.mutex, portMAX_DELAY);

    for (int i = 0; i < BUFFER_POOL_SIZE; i++)
    {
        if (&g_buffer_pool.items[i] == item)
        {
            g_buffer_pool.used[i] = 0;
            memset(item, 0, sizeof(BufferItem_t));
            break;
        }
    }

    xSemaphoreGive(g_buffer_pool.mutex);
    xSemaphoreGive(g_buffer_pool.free_count);
}

/* Get the pool status */
void BufferPool_GetStats(uint32_t *total, uint32_t *used)
{
    xSemaphoreTake(g_buffer_pool.mutex, portMAX_DELAY);

    *total = BUFFER_POOL_SIZE;
    *used = 0;
    for (int i = 0; i < BUFFER_POOL_SIZE; i++)
    {
        if (g_buffer_pool.used[i]) (*used)++;
    }

    xSemaphoreGive(g_buffer_pool.mutex);
}

/* Usage example */
void vBufferPoolDemoTask(void *pvParameters)
{
    BufferItem_t *buf;
    uint32_t total, used;

    BufferPool_Init();

    while (1)
    {
        /* Allocate a buffer */
        buf = BufferPool_Alloc();
        if (buf != NULL)
        {
            /* Use the buffer */
            buf->length = sprintf((char *)buf->data,
                                  "Message #%lu", HAL_GetTick());
            buf->timestamp = HAL_GetTick();

            printf("Allocated buffer #%lu, remaining: ", HAL_GetTick());
            BufferPool_GetStats(&total, &used);
            printf("%lu/%lu\r\n", total - used, total);

            /* Simulate processing */
            vTaskDelay(pdMS_TO_TICKS(500));

            /* Return the buffer */
            BufferPool_Free(buf);
        }
        else
        {
            printf("Buffer pool is full, waiting...\r\n");
            vTaskDelay(pdMS_TO_TICKS(100));
        }
    }
}
```
