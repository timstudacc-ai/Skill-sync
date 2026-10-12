# Advanced Applications

This document contains advanced application examples such as multi-task sensor fusion, Tickless low-power mode and STM32CubeMX configuration.

---

## 3.1 Multi-Task Sensor Fusion

### System architecture

```
+-------------------+     +-------------------+
|  Sensor collect   | --> |   Data process    |
|  task (I2C)       |     |  (filter, fuse)   |
+-------------------+     +-------------------+
                                   |
                                   v
                          +-------------------+
                          |   Data send task  |
                          |  (UART/BLE/USB)   |
                          +-------------------+
```

### Implementation code

```c
#include "main.h"
#include "FreeRTOS.h"
#include "queue.h"
#include "semphr.h"

#define QUEUE_SIZE 20

/* Data type definitions */
typedef struct {
    float acc_x, acc_y, acc_z;
    float gyro_x, gyro_y, gyro_z;
    uint32_t timestamp;
} SensorData_t;

typedef struct {
    float roll, pitch, yaw;
    uint32_t timestamp;
} FusionData_t;

/* Communication mechanisms */
QueueHandle_t g_sensor_queue;      /* Raw data queue */
QueueHandle_t g_fusion_queue;      /* Fused data queue */
SemaphoreHandle_t g_i2c_mutex;     /* I2C mutex */

/* Sensor collection task */
void vSensorCollectTask(void *pvParameters)
{
    SensorData_t data;
    I2C_HandleTypeDef *hi2c = (I2C_HandleTypeDef *)pvParameters;

    while (1)
    {
        /* Take the I2C mutex */
        if (xSemaphoreTake(g_i2c_mutex, pdMS_TO_TICKS(100)) == pdTRUE)
        {
            /* Read the sensor (simplified MPU6050) */
            if (MPU6050_ReadAll(hi2c, &data) == HAL_OK)
            {
                data.timestamp = HAL_GetTick();
                xQueueSend(g_sensor_queue, &data, 0);
            }

            xSemaphoreGive(g_i2c_mutex);
        }

        vTaskDelay(pdMS_TO_TICKS(10));  /* 100Hz sampling */
    }
}

/* Data processing task (complementary filter) */
void vDataProcessTask(void *pvParameters)
{
    SensorData_t raw_data;
    FusionData_t fused_data;
    static float gyro_x = 0, gyro_y = 0;
    static float acc_roll = 0, acc_pitch = 0;

    const float alpha = 0.98f;  /* Complementary filter coefficient */

    while (1)
    {
        /* Receive the raw data */
        if (xQueueReceive(g_sensor_queue, &raw_data, portMAX_DELAY) == pdTRUE)
        {
            /* Accelerometer angle calculation */
            acc_roll = atan2(raw_data.acc_y, raw_data.acc_z) * 180.0f / 3.14159f;
            acc_pitch = atan2(-raw_data.acc_x, raw_data.acc_z) * 180.0f / 3.14159f;

            /* Complementary filtering */
            gyro_x += raw_data.gyro_x * 0.01f;
            gyro_y += raw_data.gyro_y * 0.01f;

            fused_data.roll = alpha * gyro_x + (1 - alpha) * acc_roll;
            fused_data.pitch = alpha * gyro_y + (1 - alpha) * acc_pitch;
            fused_data.yaw += raw_data.gyro_z * 0.01f;
            fused_data.timestamp = raw_data.timestamp;

            /* Send to the fusion queue */
            xQueueSend(g_fusion_queue, &fused_data, 0);
        }
    }
}

/* Data sending task */
void vDataSendTask(void *pvParameters)
{
    FusionData_t fused_data;
    UART_HandleTypeDef *huart = (UART_HandleTypeDef *)pvParameters;

    while (1)
    {
        if (xQueueReceive(g_fusion_queue, &fused_data, portMAX_DELAY) == pdTRUE)
        {
            /* Formatted output */
            printf("Roll: %.2f, Pitch: %.2f, Yaw: %.2f\r\n",
                   fused_data.roll, fused_data.pitch, fused_data.yaw);
        }
    }
}

/* Main function */
int main(void)
{
    HAL_Init();
    SystemClock_Config();
    MX_I2C1_Init();
    MX_UART1_Init();

    /* Create the communication mechanisms */
    g_sensor_queue = xQueueCreate(QUEUE_SIZE, sizeof(SensorData_t));
    g_fusion_queue = xQueueCreate(QUEUE_SIZE, sizeof(FusionData_t));
    g_i2c_mutex = xSemaphoreCreateMutex();

    if (g_sensor_queue && g_fusion_queue && g_i2c_mutex)
    {
        /* Create the tasks */
        xTaskCreate(vSensorCollectTask, "SensorCollect", 256,
                    &hi2c1, 3, NULL);
        xTaskCreate(vDataProcessTask, "DataProcess", 256,
                    NULL, 2, NULL);
        xTaskCreate(vDataSendTask, "DataSend", 128,
                    &huart1, 1, NULL);

        vTaskStartScheduler();
    }

    while (1);
}
```

---

## 3.2 Tickless Low-Power Mode

### Configuration steps

#### 1. FreeRTOSConfig.h configuration

```c
/* FreeRTOSConfig.h */
#define configUSE_TICKLESS_IDLE    2       /* Enable Tickless */
#define configPRE_SLEEP_PROCESSING(x) vPreSleepProcessing(x)
#define configPOST_SLEEP_PROCESSING(x) vPostSleepProcessing(x)

/* External declarations */
extern void vPreSleepProcessing(uint32_t *expected_idle_time);
extern void vPostSleepProcessing(uint32_t *expected_idle_time);
```

#### 2. Tickless implementation code

```c
#include "main.h"
#include "FreeRTOS.h"

/* Low-power mode configuration */
#define STOP_MODE_TIMEOUT pdMS_TO_TICKS(100)  /* STOP mode timeout */

/* Processing before entering low power */
void vPreSleepProcessing(uint32_t *expected_idle_time)
{
    /* Lower the clock frequency */
    if (*expected_idle_time > STOP_MODE_TIMEOUT)
    {
        /* Configure for STOP mode */
        /* Configure here according to the specific chip */
        __HAL_RCC_PWR_CLK_ENABLE();

        /* Lower the core clock */
        __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE2);
    }
}

/* Processing after exiting low power */
void vPostSleepProcessing(uint32_t *expected_idle_time)
{
    (void)expected_idle_time;

    /* Restore the clock frequency */
    __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

    /* Reconfigure the clock */
    SystemClock_Config();
}

/* Idle task hook (called automatically by FreeRTOS) */
void vApplicationIdleHook(void)
{
    /* The lowest power mode can be entered here */
    __WFI();  /* Wait For Interrupt */
}
```

#### 3. STOP mode implementation

```c
#include "stm32l4xx_hal_pwr.h"
#include "stm32l4xx_ll_pwr.h"

void vEnterStopMode(uint32_t timeout_ms)
{
    /* Save the current clock */
    RCC_OscInitTypeDef RCC_OscInitStruct = {0};
    HAL_RCC_OscConfig(&RCC_OscInitStruct);

    /* Clear the wake-up flag */
    __HAL_PWR_CLEAR_FLAG(PWR_FLAG_WU);

    /* Enter STOP mode */
    HAL_PWR_EnterSTOPMode(PWR_LOWPOWERREGULATOR_ON,
                          PWR_STOPENTRY_WFI);
}

void vStopModeTask(void *pvParameters)
{
    while (1)
    {
        /* Run in normal mode */
        vTaskDelay(pdMS_TO_TICKS(100));

        /* Enter low-power mode */
        printf("Entering STOP mode\r\n");

        /* vPortSuppressTicksAndSleep() should be used here */
        /* FreeRTOS handles this automatically in practice */

        printf("Exiting STOP mode\r\n");
    }
}
```

---

## 3.3 Notes on STM32CubeMX Configuration

### FreeRTOS middleware configuration

```
STM32CubeMX → Middleware → FreeRTOS

Config Parameters:
├── VERSION: V10 (or CMSIS-R2)
├── TOTAL_HEAP_SIZE: 3072 (bytes)
├── USE_IDLE_HOOK: ✓
├── USE_TICK_HOOK: ✗
├── USE_MUTEXES: ✓
├── USE_RECURSIVE_MUTEXES: ✓
├── USE_COUNTING_SEMAPHORES: ✓
├── USE_TASK_NOTIFICATIONS: ✓
├── ENFORCE_SYSTEM_VIEWER: ✗ (default)
└── CHECK_FOR_STACK_OVERFLOW: 2 (Method 2)
```

### NVIC configuration

```
STM32CubeMX → Configuration → NVIC

┌──────────────────────────────────────────────────────────────────┐
│ NVIC                                                       [x]   │
├──────────────────────────────────────────────────────────────────┤
│ NVIC_Priority_Group: NVIC_PRIORITYGROUP_4                        │
├──────────────────────────────────────────────────────────────────┤
│ Priority table:                                                  │
│                                                                  │
│  System            │ Priority │ Sub-prio │ Preempt │             │
│ ───────────────────┼──────────┼──────────┼─────────┼─────────────┤
│  NonMaskableInt    │    0     │    0     │    -    │             │
│  HardFault         │    0     │    0     │    -    │             │
│  MemoryManagement  │    0     │    0     │    -    │             │
│  BusFault          │    0     │    0     │    -    │             │
│  UsageFault        │    0     │    0     │    -    │             │
│  SVCall            │    0     │    0     │    -    │             │
│  DebugMonitor      │    0     │    0     │    -    │             │
│  PendSV            │   15     │    0     │    -    │  FreeRTOS   │
│  SysTick           │   15     │    0     │    -    │  FreeRTOS   │
│  USART1            │    5     │    0     │    ✓    │  Peripheral │
│  DMA1_Channel1     │    6     │    0     │    ✓    │  Peripheral │
│  ...               │  ...     │   ...    │   ...   │  ...        │
└──────────────────────────────────────────────────────────────────┘

Key points:
1. PendSV and SysTick must be set to the lowest priority (15)
2. The FreeRTOS kernel interrupt priority is 5 (configKERNEL_INTERRUPT_PRIORITY)
3. Peripheral interrupt priorities should be above the kernel (5-15)
```

### Peripheral + DMA configuration

```
UART1 configuration:
├── Mode: Asynchronous
├── Baud Rate: 115200
├── Data Bits: 8
├── Parity: None
├── Stop Bits: 1
├── DMA Settings: ✓
│   ├── USART1_TX: DMA1 Channel 4
│   └── USART1_RX: DMA1 Channel 5
└── NVIC Settings:
    ├── USART1 global interrupt: ✓ (Priority 5)
    └── DMA1 channel global interrupt: ✓ (Priority 6)

ADC1 configuration:
├── Mode: Scan Continuous Conversion
├── Enable Regular Conversions: ✓
├── Number of Conversion: 3
├── DMA Continuos Requests: ✓
├── DMA Settings: ✓
│   └── ADC1: DMA1 Channel 1
└── NVIC Settings:
    └── DMA1 channel 1/2/3 interrupt: ✓ (Priority 6)
```

### Modifications to the generated code

```c
/* The generated main.c needs to be modified */

/* 1. Put the HAL initialisation before FreeRTOS */
int main(void)
{
    HAL_Init();
    SystemClock_Config();

    /* MX initialisation (excluding FreeRTOS) */
    MX_GPIO_Init();
    MX_DMA_Init();
    MX_USART1_UART_Init();

    /* Create the tasks */
    StartDefaultTask();
    vTaskStartScheduler();  /* Start the scheduler here */
}

/* 2. Remove the MX_FREERTOS_Init() generated by default */

/* 3. Place the task functions before main or in a separate file */

/* 4. Adjust the task stack sizes as required */
```
