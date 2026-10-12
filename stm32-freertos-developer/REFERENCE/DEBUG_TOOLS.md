# Debug Tool Configuration

This document describes how to configure debugging tools such as SEGGER SystemView, Percep TRACEalyzer and ITM/SWO.

---

## SEGGER SystemView (Keil/IAR environment)

### Purpose
- Real-time system analysis
- Visualisation of task switches
- Interrupt duration statistics
- CPU usage analysis
- Event trace recording

### Configuration Steps

#### 1. Add the SystemView library
- Download the SEGGER SystemView firmware library
- Add `SEGGER_SYSVIEW.c` to the project
- Add `SEGGER_SYSVIEW_FreeRTOS.c` (the FreeRTOS interface)

#### 2. Initialise SystemView

```c
#include "SEGGER_SYSVIEW.h"

void vSystemView_Init(void)
{
    /* Initialise J-Link (ST-Link does not support SystemView) */
    SEGGER_SYSVIEW_Init(SYSTEM_VIEW_TIMESTAMP_FREQ,
                        CPU_CORE_CLOCK,
                        &SYSVIEW_X_OS_Config,
                        &SEGGER_SYSVIEW_Conf);

    /* Start recording */
    SEGGER_SYSVIEW_Start();
}
```

#### 3. Configure ITM/SWO

```c
/* Enable the ITM port */
CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
ITM->TCR |= ITM_TCR_ITMENA_Msk;
ITM->TPR |= ITM_TPR_PRIVMASK_Msk;

/* SWO pin configuration (refer to the chip datasheet) */
GPIOB->MODER &= ~GPIO_MODER_MODE3_Msk;
GPIOB->MODER |= GPIO_MODER_MODE3_0;  /* AF */
GPIOB->AFR[0] &= ~GPIO_AFRH_AFRH3_Msk;
GPIOB->AFR[0] |= 0x0 << 12;          /* AF0 (SWO) */
```

#### 4. Task tracing

```c
#include "SEGGER_SYSVIEW.h"

void vTaskExample(void *pvParameters)
{
    SEGGER_SYSVIEW_Print("Task started");

    while (1)
    {
        SEGGER_SYSVIEW_RecordEnterTask();
        /* Task code */
        SEGGER_SYSVIEW_RecordExitTask();

        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
```

---

## Percep TRACEalyzer (FreeRTOS environment)

### Purpose
- Recording and analysis of trace events
- Timing diagram visualisation
- Statistics on task resource usage
- Locating performance bottlenecks
- Memory usage tracking

### Configuration Steps

#### 1. Enable the trace facility

In `FreeRTOSConfig.h`:

```c
#define configUSE_TRACE_FACILITY     1
#define configUSE_STATS_FORMATTING_FUNCTIONS 1
#define configRECORD_STACK_HIGH_ADDRESS 1
```

#### 2. Add trcRecorder.c

- Obtain `trcRecorder.c` from FreeRTOS+Trace or Percep TRACEalyzer
- Add it to the project
- Configure `trcConfig.h`:

```c
#define TRC_CFG_TRACE_CONTROLLER_SUPPORTS_64_BIT_EVENTS 0
#define TRC_CFG_HARDWARE_PORT Cortex-M
#define TRC_CFG_FREERTOS_VERSION FREERTOS_VERSION
#define TRC_CFG_RECORDER_MODE TRC_RECORDER_MODE_STREAMING
```

#### 3. Initialise the recorder

```c
#include "trcRecorder.h"

void vTrace_Init(void)
{
    vTraceEnable(TRC_START);  /* Start recording */
}

void vTrace_Stop(void)
{
    vTraceDisable();  /* Stop recording */
}
```

#### 4. Export the trace data

```c
void vExportTrace(void)
{
    traceHandle trace_file;

    /* Open the file */
    trace_file = xTraceOpenWrite("w", "trace.ptd");
    if (trace_file != TRC_NULL)
    {
        /* Write the data */
        xTraceWrite(trace_file, NULL, 0);
        xTraceClose(trace_file);
    }
}
```

#### 5. Analyse with TRACEalyzer

1. Export the `.ptd` file through J-Link/ST-Link
2. Open it with Percep TRACEalyzer
3. Inspect the timing diagram, task statistics and resource usage

---

## ITM/SWO Configuration Steps

### ST-Link Configuration

```c
/* Enable SWO output (ST-Link) */
volatile uint32_t *DBGMCU_CR = (volatile uint32_t *)0xE0042004;
*DBGMCU_CR |= 0x27;  /* TRACE_IOEN | TRACE_MODE_0 | TRACE_MODE_1 */

/* Configure the TPIU (Trace Port Interface Unit) */
TPI->ACPR = 0;  /* 1:1 prescaler */
TPI->SPPR = 2;  /* SWO NRZ encoding */
TPI->FFCR = 0;  /* Disable the FIFO */

/* Enable ITM port 0 */
ITM->TCR = 0x10009;  /* ITMENA | SyncFieldsEnable */
ITM->TER = 1;        /* Enable port 0 */
```

### J-Link Configuration

```c
/* J-Link SWO initialisation (provided by SEGGER) */
void SEGGER_SWO_Init(void)
{
    /* Configure the SWO pin */
    GPIOA->MODER &= ~(GPIO_MODER_MODE9_Msk);
    GPIOA->MODER |= GPIO_MODER_MODE9_1;  /* AF */
    GPIOA->AFR[1] &= ~GPIO_AFRH_AFRH1_Msk;
    GPIOA->AFR[1] |= 0x0 << 4;  /* AF0 */

    /* Initialise the SWO baud rate */
    SEGGER_SYSVIEW_SetSWOBaud(1000000);
}
```

---

## FreeRTOS Statistics Features

### Task State Statistics

```c
#include "task.h"

void vTaskStatsPrint(void)
{
    TaskStatus_t *pxTaskStatusArray;
    UBaseType_t uxArraySize;
    uint32_t ulTotalRunTime;
    char buffer[512];

    /* Get the number of tasks */
    uxArraySize = uxTaskGetNumberOfTasks();

    /* Allocate memory */
    pxTaskStatusArray = pvPortMalloc(uxArraySize * sizeof(TaskStatus_t));
    if (pxTaskStatusArray == NULL)
    {
        printf("Memory allocation failed\r\n");
        return;
    }

    /* Get the statistics */
    uxTaskGetSystemState(pxTaskStatusArray, uxArraySize,
                         &ulTotalRunTime);

    /* Print the statistics */
    snprintf(buffer, sizeof(buffer), "\r\nTask statistics:\r\n");
    printf(buffer);

    for (UBaseType_t i = 0; i < uxArraySize; i++)
    {
        TaskStatus_t *pxTask = &pxTaskStatusArray[i];

        /* Calculate the CPU usage */
        uint32_t ulStatsAsPercentage =
            (pxTask->ulRunTimeCounter * 100UL) / ulTotalRunTime;

        snprintf(buffer, sizeof(buffer),
                 "%-16s Priority: %2lu State: %c CPU: %2lu%% Stack: %lu\r\n",
                 pxTask->pcTaskName,
                 (unsigned long)pxTask->uxCurrentPriority,
                 (pxTask->eCurrentState == eRunning) ? 'R' :
                 (pxTask->eCurrentState == eReady) ? 'r' :
                 (pxTask->eCurrentState == eBlocked) ? 'B' :
                 (pxTask->eCurrentState == eSuspended) ? 'S' : '?',
                 (unsigned long)ulStatsAsPercentage,
                 (unsigned long)pxTask->usStackHighWaterMark);
        printf(buffer);
    }

    /* Free the memory */
    vPortFree(pxTaskStatusArray);
}
```

### Run-Time Statistics

```c
void vTaskRunTimeStats(void)
{
    TaskStatus_t *pxTaskStatusArray;
    UBaseType_t uxArraySize;
    uint32_t ulTotalRunTime;
    char buffer[256];

    uxArraySize = uxTaskGetNumberOfTasks();
    pxTaskStatusArray = pvPortMalloc(uxArraySize * sizeof(TaskStatus_t));

    if (pxTaskStatusArray != NULL)
    {
        uxTaskGetSystemState(pxTaskStatusArray, uxArraySize,
                             &ulTotalRunTime);

        printf("\r\nRun-time statistics:\r\n");
        printf("Name            Runtime(%)     Cycles\r\n");
        printf("----------------------------------------\r\n");

        for (UBaseType_t i = 0; i < uxArraySize; i++)
        {
            TaskStatus_t *pxTask = &pxTaskStatusArray[i];
            uint32_t ulStatsAsPercentage =
                (pxTask->ulRunTimeCounter * 100UL) / ulTotalRunTime;

            snprintf(buffer, sizeof(buffer),
                     "%-16s %2lu.%02lu%%       %lu\r\n",
                     pxTask->pcTaskName,
                     (unsigned long)ulStatsAsPercentage,
                     (unsigned long)(ulStatsAsPercentage * 100) % 100,
                     (unsigned long)pxTask->ulRunTimeCounter);
            printf(buffer);
        }

        vPortFree(pxTaskStatusArray);
    }
}
```

### Stack Overflow Detection

```c
/* FreeRTOSConfig.h */
#define configCHECK_FOR_STACK_OVERFLOW 2

void vApplicationStackOverflowHook(TaskHandle_t xTask,
                                   char *pcTaskName)
{
    printf("Stack overflow: %s\r\n", pcTaskName);
    while (1);  /* Enter an infinite loop to ease debugging */
}
```
