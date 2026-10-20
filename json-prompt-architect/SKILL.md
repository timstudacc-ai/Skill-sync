---
name: json-prompt-architect
description: Converts raw, vague, or unstructured user requests into complete, execution-ready JSON schema prompts using an 11-field standard template without altering the user's core intent. Use when asked to convert, refine, or structure a prompt into the standard JSON prompt format.
version: 1.0.0
---
# JSON Prompt Architect

A specialized skill for decomposing unstructured, underspecified user queries and translating them into rigorous, execution-ready JSON prompts adhering to an 11-field schema.

## When to Use

* A user provides a brief or vague request and asks to formalize it into a structured prompt.
* A user explicitly requests to convert an instruction into the 11-field JSON prompt format.
* Preparing standardized machine-readable tasks for automated agent pipelines.

## Intent Preservation Principle

When expanding a prompt:
1. Never mutate the user's goal: Expanding details means making implicit requirements explicit, not introducing new functional desires.
2. Isolate additions to operational scaffolding: Elaboration belongs in `steps`, `constraints`, `acceptance_criteria`, and `role`, while `task` remains true to the original request.
3. Separate instructions from data: If the user supplies reference text, code, or context, route it into `inputs` or `context`, never into the `task` field.

## The 11-Field Translation Algorithm

Process any raw user request through these sequential transformation steps:

1. Identify Domain & Assign `role`: Determine the specific expert persona best suited to resolve the request.
2. Identify Tool Requirements for `skills_to_invoke`: Evaluate whether the task requires external tools. If none, populate with `["general_reasoning"]` or `[]`.
3. Extract Background State for `context`: Identify implicit background assumptions, environment state, or technological stacks.
4. Separate Artifacts for `inputs`: Isolate code snippets, raw data, logs, or reference documents provided. If none, specify what payload the agent should expect or mark as `"None provided; operate on task instructions"`.
5. Sharpen the `task`: State the singular, high-level deliverable clearly in one sentence. Preserve original intent without scope creep.
6. Deconstruct Execution into `steps`: Break down execution into an ordered, chronological array of procedural actions.
7. Demarcate Boundaries for `scope`: Declare `"In-scope: [...] | Out-of-scope: [...]"`.
8. Enforce Negative Limits in `constraints`: Extract or establish strict negative guardrails.
9. Establish Verification via `acceptance_criteria`: Formulate concrete, observable conditions that logically verify completion.
10. Select `fallback_behavior`: Choose `"ask_clarification"`, `"assume_and_document"`, or `"halt"`.
11. Define Deliverable Format in `expected_output`: Specify exact syntax, structure, and tone.

## Output Template Structure

Every transformed prompt must strictly match this JSON structure:

```json
{
  "role": "Expert Assistant",
  "skills_to_invoke": ["skill_name"],
  "context": "Background information, system state, prior decisions",
  "inputs": "Raw data, source code, or documents to process",
  "task": "Primary objective to accomplish",
  "steps": [
    "1. First action step",
    "2. Second action step"
  ],
  "scope": "In-scope: ... | Out-of-scope: ...",
  "constraints": [
    "Hard rule that must not be violated"
  ],
  "acceptance_criteria": [
    "Verification condition that confirms task completion"
  ],
  "fallback_behavior": "ask_clarification | halt | assume_and_document",
  "expected_output": "Format, structure, and style requirements"
}

```

## Reference Example: Embedded Systems HAL Driver

### Raw User Query

> "Write a C HAL driver for the ICM45686 IMU over SPI."

### Transformed JSON Schema Prompt

```json
{
  "role": "Senior Embedded Systems Engineer & Firmware Architect",
  "skills_to_invoke": ["general_reasoning"],
  "context": "Bare-metal or RTOS embedded C environment (ARM Cortex-M target) interfacing with a TDK InvenSense ICM-45686 6-axis MotionTracking IMU over a 4-wire SPI bus.",
  "inputs": "Datasheet register map for the ICM-45686 and target platform SPI read/write function pointer signatures.",
  "task": "Develop a modular, platform-agnostic C HAL driver (header and source) for the ICM-45686 IMU supporting initialization, configuration, and reading of 6-axis accelerometer and gyroscope data over SPI.",
  "steps": [
    "1. Define the register map, bitmasks, configuration enums (ODR, FSR, power modes), and driver instance structs in 'icm45686.h'.",
    "2. Implement a hardware bus interface abstraction using function pointers for platform-specific SPI transfers and CS pin assertion.",
    "3. Write the device initialization sequence: soft reset, WHO_AM_I validation, power management setup, and sensor bandwidth/range configuration.",
    "4. Implement burst-reading routines for 6-axis raw sensor data (accel + gyro + temperature) with proper register endianness conversion.",
    "5. Provide conversion utility functions to map raw ADC values into physical units (g and dps) based on the active FSR.",
    "6. Include status error codes (success, bus error, device not found, timeout) across all public API calls."
  ],
  "scope": "In-scope: C99-compliant driver (.h/.c), platform-independent SPI abstraction, WHO_AM_I verification, synchronous polling reads, unit conversion math | Out-of-scope: DMA transfer pipelines, complex FIFO buffer parsing, APEX hardware interrupt engines, sensor fusion algorithms (e.g., Madgwick/Mahony filters).",
  "constraints": [
    "No dynamic memory allocation (malloc/free); all state must reside in a caller-allocated driver handle struct.",
    "Strictly adhere to MISRA C / C99 using fixed-width integers from <stdint.h> and <stdbool.h>.",
    "Do not couple the driver to specific vendor SDKs (e.g., STM32 HAL, NXP MCUXpresso); use a function-pointer bus table.",
    "Preserve atomic register reads by bursting data registers in a single CS transaction."
  ],
  "acceptance_criteria": [
    "Public API exposes lifecycle functions: icm45686_init(), icm45686_set_odr_fsr(), icm45686_read_raw(), and icm45686_read_scaled().",
    "WHO_AM_I register check explicitly verifies against the factory default value before applying configuration registers.",
    "Raw-to-scaled conversion applies correct sensitivity divisors according to datasheet specs for selected ranges (e.g., ±2g to ±16g, ±250dps to ±2000dps).",
    "Code contains zero compiler warnings under -Wall -Wextra -Werror."
  ],
  "fallback_behavior": "assume_and_document",
  "expected_output": "Modular C source code consisting of: 1. Header file (icm45686.h) with complete enum declarations, structs, and API prototypes; 2. Source file (icm45686.c) with full driver implementation; 3. Minimal main.c integration example demonstrating platform hook binding."
}