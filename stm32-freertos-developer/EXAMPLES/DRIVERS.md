# Peripheral Driver Templates

This document contains complete template code for UART, ADC, I2C and printf redirection drivers.

---

## 2.1 UART DMA + Queue + IDLE Interrupt

### Header file (uart_driver.h)

```c
#ifndef UART_DRIVER_H
#define UART_DRIVER_H

#include "main.h"
#include "FreeRTOS.h"
#include "queue.h"

#define UART_RX_BUFFER_SIZE 256

typedef struct {
    uint8_t data[UART_RX_BUFFER_SIZE];
    uint16_t length;
} UartRxMessage_t;

extern QueueHandle_t g_uart_rx_queue;

void vUartDriverInit(void);
void vUartRxTask(void *pvParameters);

#endif /* UART_DRIVER_H */
```

### Implementation file (uart_driver.c)

```c
#include "uart_driver.h"
#include "string.h"
#include "stdio.h"

static uint8_t g_rx_buffer[UART_RX_BUFFER_SIZE];
static volatile uint16_t g_rx_index = 0;
static volatile uint8_t g_rx_complete = 0;

QueueHandle_t g_uart_rx_queue;

void vUartDriverInit(void)
{
    /* Enable the IDLE interrupt */
    __HAL_UART_ENABLE_IT(&huart1, UART_IT_IDLE);

    /* Start DMA reception */
    HAL_UART_Receive_DMA(&huart1, g_rx_buffer, UART_RX_BUFFER_SIZE);

    /* Create the queue */
    g_uart_rx_queue = xQueueCreate(20, sizeof(UartRxMessage_t));
}

void HAL_UART_IDLECallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        /* Calculate the received length */
        uint16_t dma_counter = __HAL_DMA_GET_COUNTER(&hdma_usart1_rx);
        g_rx_index = UART_RX_BUFFER_SIZE - dma_counter;
        g_rx_complete = 1;

        /* Stop DMA */
        HAL_UART_DMAStop(&huart1);
    }
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        g_rx_index = UART_RX_BUFFER_SIZE;
        g_rx_complete = 1;
        HAL_UART_DMAStop(&huart1);
    }
}

void vUartRxTask(void *pvParameters)
{
    UartRxMessage_t msg;

    while (1)
    {
        /* Wait until reception is complete */
        while (g_rx_complete == 0)
        {
            vTaskDelay(pdMS_TO_TICKS(10));
        }

        /* Copy the data */
        memcpy(msg.data, g_rx_buffer, g_rx_index);
        msg.length = g_rx_index;

        /* Send to the queue */
        if (xQueueSend(g_uart_rx_queue, &msg, 0) == pdTRUE)
        {
            /* Restart DMA */
            g_rx_complete = 0;
            HAL_UART_Receive_DMA(&huart1, g_rx_buffer,
                                 UART_RX_BUFFER_SIZE);
        }
        else
        {
            printf("Queue full, discarding data\r\n");
            g_rx_complete = 0;
            HAL_UART_Receive_DMA(&huart1, g_rx_buffer,
                                 UART_RX_BUFFER_SIZE);
        }
    }
}

/* Data processing task example */
void vDataProcessTask(void *pvParameters)
{
    UartRxMessage_t msg;

    while (1)
    {
        if (xQueueReceive(g_uart_rx_queue, &msg, portMAX_DELAY) == pdTRUE)
        {
            printf("Received %d bytes: ", msg.length);

            /* Echo the data */
            for (int i = 0; i < msg.length; i++)
            {
                printf("%02X ", msg.data[i]);
            }
            printf("\r\n");
        }
    }
}
```

---

## 2.2 ADC DMA + Task Notification

### Header file (adc_driver.h)

```c
#ifndef ADC_DRIVER_H
#define ADC_DRIVER_H

#include "main.h"
#include "FreeRTOS.h"
#include "task.h"

#define ADC_CHANNEL_COUNT 3

extern TaskHandle_t g_adc_task_handle;
extern uint32_t g_adc_values[ADC_CHANNEL_COUNT];

void MX_ADC1_Init(void);
void vAdcTask(void *pvParameters);

#endif /* ADC_DRIVER_H */
```

### Implementation file (adc_driver.c)

```c
#include "adc_driver.h"
#include "string.h"

#define ADC_BUFFER_SIZE ADC_CHANNEL_COUNT

static uint32_t g_adc_buffer[ADC_BUFFER_SIZE];
uint32_t g_adc_values[ADC_CHANNEL_COUNT];
TaskHandle_t g_adc_task_handle;

void MX_ADC1_Init(void)
{
    ADC_ChannelConfTypeDef sConfig = {0};

    /* Configure the ADC */
    hadc1.Instance = ADC1;
    hadc1.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV4;
    hadc1.Init.Resolution = ADC_RESOLUTION_12B;
    hadc1.Init.ScanConvMode = ENABLE;
    hadc1.Init.ContinuousConvMode = ENABLE;
    hadc1.Init.DiscontinuousConvMode = DISABLE;
    hadc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
    hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
    hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
    hadc1.Init.NbrOfConversion = ADC_CHANNEL_COUNT;
    hadc1.Init.DMAContinuousRequests = ENABLE;
    hadc1.Init.EOCSelection = ADC_EOC_SEQ_CONV;

    HAL_ADC_Init(&hadc1);

    /* Configure the channels */
    sConfig.Channel = ADC_CHANNEL_0;
    sConfig.Rank = 1;
    sConfig.SamplingTime = ADC_SAMPLETIME_480CYCLES;
    HAL_ADC_ConfigChannel(&hadc1, &sConfig);

    sConfig.Channel = ADC_CHANNEL_1;
    sConfig.Rank = 2;
    HAL_ADC_ConfigChannel(&hadc1, &sConfig);

    sConfig.Channel = ADC_CHANNEL_2;
    sConfig.Rank = 3;
    HAL_ADC_ConfigChannel(&hadc1, &sConfig);

    /* Start DMA */
    HAL_ADC_Start_DMA(&hadc1, g_adc_buffer, ADC_BUFFER_SIZE);
}

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *hadc)
{
    if (hadc->Instance == ADC1)
    {
        /* Copy the data */
        memcpy(g_adc_values, g_adc_buffer, sizeof(g_adc_values));

        /* Send a task notification */
        BaseType_t xHigherPriorityTaskWoken = pdFALSE;
        vTaskNotifyGiveFromISR(g_adc_task_handle,
                               &xHigherPriorityTaskWoken);
        portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
    }
}

void vAdcTask(void *pvParameters)
{
    uint32_t tick_count = 0;
    float voltage;

    while (1)
    {
        /* Wait for the ADC conversion to complete */
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

        tick_count++;

        /* Process the ADC data */
        printf("ADC sample #%lu:\r\n", tick_count);

        for (int i = 0; i < ADC_CHANNEL_COUNT; i++)
        {
            /* Convert to a voltage */
            voltage = (float)g_adc_values[i] * 3.3f / 4095.0f;
            printf("  CH%d: %.3f V (0x%04lX)\r\n",
                   i, voltage, g_adc_values[i]);
        }
        printf("\r\n");
    }
}
```

---

## 2.3 I2C Sensor Reading (BME280)

### Header file (bme280_driver.h)

```c
#ifndef BME280_DRIVER_H
#define BME280_DRIVER_H

#include "main.h"
#include "FreeRTOS.h"
#include "queue.h"

#define BME280_ADDR 0x76

typedef struct {
    float temperature;   /* Temperature */
    float humidity;      /* Humidity */
    float pressure;      /* Pressure */
} Bme280Data_t;

extern QueueHandle_t g_bme280_queue;

void vBme280Task(void *pvParameters);
HAL_StatusTypeDef BME280_Init(I2C_HandleTypeDef *hi2c);
HAL_StatusTypeDef BME280_Read(I2C_HandleTypeDef *hi2c, Bme280Data_t *data);

#endif /* BME280_DRIVER_H */
```

### Implementation file (bme280_driver.c)

```c
#include "bme280_driver.h"
#include "string.h"

#define BME280_REG_ID      0xD0
#define BME280_REG_RESET   0xE0
#define BME280_REG_CTRL_HUM 0xF2
#define BME280_REG_CTRL_MEAS 0xF4
#define BME280_REG_CONFIG  0xF5
#define BME280_REG_DATA   0xF7

static uint8_t g_tx_buffer[4];
static uint8_t g_rx_buffer[8];
static int32_t g_compensate_t;
static uint32_t g_compensate_p;
static uint32_t g_compensate_h;

QueueHandle_t g_bme280_queue;

HAL_StatusTypeDef BME280_Init(I2C_HandleTypeDef *hi2c)
{
    uint8_t id;

    /* Read the chip ID */
    g_tx_buffer[0] = BME280_REG_ID;
    HAL_I2C_Master_Transmit(hi2c, BME280_ADDR << 1,
                            g_tx_buffer, 1, 100);
    HAL_I2C_Master_Receive(hi2c, BME280_ADDR << 1,
                           &id, 1, 100);

    if (id != 0x60)
    {
        return HAL_ERROR;
    }

    /* Software reset */
    g_tx_buffer[0] = BME280_REG_RESET;
    g_tx_buffer[1] = 0xB6;
    HAL_I2C_Master_Transmit(hi2c, BME280_ADDR << 1,
                            g_tx_buffer, 2, 100);
    vTaskDelay(pdMS_TO_TICKS(10));

    /* Configure humidity sampling */
    g_tx_buffer[0] = BME280_REG_CTRL_HUM;
    g_tx_buffer[1] = 0x05;  /* 16x oversampling */
    HAL_I2C_Master_Transmit(hi2c, BME280_ADDR << 1,
                            g_tx_buffer, 2, 100);

    /* Configure the measurement */
    g_tx_buffer[0] = BME280_REG_CTRL_MEAS;
    g_tx_buffer[1] = 0xB7;  /* Temperature 16x + pressure 16x */
    HAL_I2C_Master_Transmit(hi2c, BME280_ADDR << 1,
                            g_tx_buffer, 2, 100);

    /* Configure the filter */
    g_tx_buffer[0] = BME280_REG_CONFIG;
    g_tx_buffer[1] = 0x00;  /* No filter */
    HAL_I2C_Master_Transmit(hi2c, BME280_ADDR << 1,
                            g_tx_buffer, 2, 100);

    return HAL_OK;
}

/* Simplified compensation calculation (use the official BME280 algorithm in practice) */
static void BME280_Compensate(int32_t adc_t, int32_t adc_p,
                              int32_t adc_h)
{
    g_compensate_t = adc_t / 100;
    g_compensate_p = adc_p / 256;
    g_compensate_h = adc_h / 1024;
}

HAL_StatusTypeDef BME280_Read(I2C_HandleTypeDef *hi2c, Bme280Data_t *data)
{
    /* Send the data register address */
    g_tx_buffer[0] = BME280_REG_DATA;
    HAL_I2C_Master_Transmit(hi2c, BME280_ADDR << 1,
                            g_tx_buffer, 1, 100);

    /* Read 8 bytes of data */
    HAL_I2C_Master_Receive(hi2c, BME280_ADDR << 1,
                           g_rx_buffer, 8, 100);

    /* Parse the data */
    int32_t adc_p = (g_rx_buffer[0] << 12) | (g_rx_buffer[1] << 4) |
                    (g_rx_buffer[2] >> 4);
    int32_t adc_t = (g_rx_buffer[3] << 12) | (g_rx_buffer[4] << 4) |
                    (g_rx_buffer[5] >> 4);
    int32_t adc_h = (g_rx_buffer[6] << 8) | g_rx_buffer[7];

    /* Compensation calculation */
    BME280_Compensate(adc_t, adc_p, adc_h);

    /* Fill in the results */
    data->temperature = (float)g_compensate_t / 100.0f;
    data->pressure = (float)g_compensate_p / 256.0f;
    data->humidity = (float)g_compensate_h / 1024.0f;

    return HAL_OK;
}

void vBme280Task(void *pvParameters)
{
    Bme280Data_t sensor_data;
    I2C_HandleTypeDef *hi2c1 = (I2C_HandleTypeDef *)pvParameters;

    /* Initialise the sensor */
    while (BME280_Init(hi2c1) != HAL_OK)
    {
        printf("BME280 initialisation failed, retrying...\r\n");
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
    printf("BME280 initialised successfully\r\n");

    /* Create the queue */
    g_bme280_queue = xQueueCreate(5, sizeof(Bme280Data_t));

    while (1)
    {
        /* Read the sensor */
        if (BME280_Read(hi2c1, &sensor_data) == HAL_OK)
        {
            printf("Temperature: %.1f°C, Humidity: %.1f%%, Pressure: %.1f hPa\r\n",
                   sensor_data.temperature,
                   sensor_data.humidity,
                   sensor_data.pressure);

            /* Send it to the queue */
            xQueueSend(g_bme280_queue, &sensor_data, 0);
        }
        else
        {
            printf("BME280 read failed\r\n");
        }

        vTaskDelay(pdMS_TO_TICKS(2000));  /* 0.5Hz sampling */
    }
}
```

---

## 2.4 printf Redirection (ITM_SendChar)

### Header file (retarget.h)

```c
#ifndef RETARGET_H
#define RETARGET_H

#include <stdio.h>

/* Redirection function declaration */
int __attribute__((weak)) _write(int file, char *ptr, int len);

/* ITM debug output macros */
#define ITM_Port8(n)    (*((volatile unsigned char *)(0xE0000000 + 4 * n)))
#define ITM_Port16(n)   (*((volatile unsigned short *)(0xE0000000 + 4 * n)))
#define ITM_Port32(n)   (*((volatile unsigned long *)(0xE0000000 + 4 * n)))
#define DEMCR           (*((volatile unsigned long *)(0xE000EDFC)))
#define TRCENA          0x01000000

#endif /* RETARGET_H */
```

### Implementation file (retarget.c)

```c
#include "retarget.h"
#include "core_cm4.h"

/* ITM debug output initialisation */
void ITM_Init(void)
{
    /* Enable TRACE debugging */
    DEMCR |= TRCENA;

    /* Configure the SWO pin (depends on the specific chip) */
    /* The GPIO configuration is omitted here; ST-Link configures SWO by default */

    /* Set up ITM port 0 */
    ITM->TCR = 0x00000009;  /* ITMENA | ATVALID */
    ITM->TER = 0x00000001;  /* Enable port 0 */
}

/* Redirect _write to ITM */
int __attribute__((weak)) _write(int file, char *ptr, int len)
{
    (void)file;

    for (int i = 0; i < len; i++)
    {
        /* Wait until the SWO port is ready */
        while (ITM->PORT[0].u32 == 0) {}
        ITM->PORT[0].u8 = (uint8_t)ptr[i];
    }

    return len;
}

/* Redirect _puts */
int __attribute__((weak)) _puts(const char *str)
{
    int i = 0;
    while (str[i])
    {
        if (str[i] == '\n')
        {
            ITM_Port8(0) = '\r';
            while (ITM_Port8(0) == 0) {}
        }
        ITM_Port8(0) = str[i];
        while (ITM_Port8(0) == 0) {}
        i++;
    }
    return i;
}

/* Usage example */
void vItmExampleTask(void *pvParameters)
{
    ITM_Init();

    while (1)
    {
        printf("Hello from ITM! Tick: %lu\r\n", HAL_GetTick());
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
```
