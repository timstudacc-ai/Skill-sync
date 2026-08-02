---
name: nlm-skill
description: Complete command reference, knowledge base taxonomy, and operational workflow guide for interacting with NotebookLM knowledge bases via nlm CLI and MCP tools.
---

# NotebookLM (`nlm`) Master Skill Guide

This skill combines the complete command-line reference for the `nlm` toolset with your personal/work NotebookLM knowledge base taxonomy and AI agent interaction protocols.

---

## 1. Knowledge Base Structure & Domain Routing

The NotebookLM knowledge base is partitioned across two Google Account profiles:

### A. Work Profile (`work` / `tymofij.frolov@alnicko.com`)
Used exclusively for embedded engineering, firmware development, hardware datasheets, and RTOS principles.

| Notebook Title | Primary Content & Tags | Active Notebook ID |
| :--- | :--- | :--- |
| **`ESP32`** | ESP-IDF build fixes, flashing permissions, Wi-Fi driver refactoring | `bc4c6332-3689-4672-9238-851d2dd06291` |
| **`STM32`** | Meteostation architecture, RTC wakeup, I2C/SPI EEPROM, CubeMX Linux fixes | `4d3be3eb-621d-43f7-9434-5cd1a41b1343` |
| **`Nordic Semiconductor nRF54L15`** | Zephyr RTOS, nRF Connect SDK v3.x, ISR safety, concurrency rules | `16314b9f-2098-4519-8517-3951a9aaf331` |
| **`Miscellaneous` (Work)** | General embedded principles, FreeRTOS task lifecycle & memory pitfalls | `99d0c403-3a8a-4093-abc4-3eda84fa7d09` |

### B. Personal Profile (`personal` / `timstudacc@gmail.com`)
Used for non-embedded studies, prompt engineering guides, physical conditioning, and general notes.

| Notebook Title | Primary Content & Tags | Active Notebook ID |
| :--- | :--- | :--- |
| **`Prompting`** | Human-in-the-Loop Embedded Coding prompts, Socratic tutor guides | `e9d22f9a-a0e2-4096-bcf6-c800a230fbe9` |
| **`Swimming`** | Aerobic endurance training protocols, YouTube courses, PDFs | `17834c1d-4c87-4386-81df-eeb29b8fbd49` |
| **`Miscellaneous` (Personal)** | Focus tracking logs, general study notes | `292640c2-4ec8-4c0a-9b30-587c84daa772` |

---

## 2. AI Agent Interaction Protocol

### A. On-Demand RAG Retrieval Protocol
* **Trigger Condition:** The AI agent MUST NOT perform NotebookLM RAG retrieval automatically on simple prompts. Retrieval is performed **only on-demand** when the user explicitly includes trigger phrases such as: `check NLM`, `search notebook`, `query nlm`, `/nlm`, `look up in notebooklm`.
* **Execution Steps:**
  1. Identify the target domain and switch profile if necessary (`nlm login switch work` or `nlm login switch personal`).
  2. Locate the specific Notebook ID or execute `nlm cross query` across the target profile.
  3. Ground the final answer/code strictly in the retrieved facts and cite the source notebook title.

### B. Knowledge Ingestion & Save Protocol
* **Trigger Condition:** When a complex bug is fixed, a new prompt is designed, or a new best practice is established, the AI agent MUST NOT save data to NotebookLM automatically.
* **Execution Steps:**
  1. Ask the developer for explicit confirmation (or wait for commands like `save to NLM`, `/save-nlm`).
  2. Format the lesson into a concise Markdown summary note.
  3. Route and upload to the target notebook using `nlm source add <notebook_id> --text "Content" --title "Title"`.

---

## 3. Complete CLI & Command Reference

### Installation & Authentication
```bash
# Installation
pip install notebooklm-mcp-cli

# Profile Management
nlm login                         # Open browser & extract cookies
nlm login --profile work          # Login to specific profile
nlm login switch <profile>        # Switch default profile (updates MCP server)
nlm login profile list            # List all registered profiles
```

### Notebook Operations
```bash
nlm notebook list --json               # List notebooks in current profile
nlm notebook create "Title"            # Create new notebook
nlm notebook get <id> --json           # Inspect notebook metadata
nlm notebook query <id> "question"     # Query specific notebook
```

### Source Operations
```bash
nlm source list <notebook>                          # List sources
nlm source add <notebook> --url "https://..." --wait # Add URL
nlm source add <notebook> --file doc.pdf --wait     # Add file
nlm source add <notebook> --text "data" --title "T" # Add text note
nlm source get <source-id>                          # Read source content
nlm source delete <source-id> --confirm             # Delete source
```

### Cross-Notebook & Batch Queries
```bash
nlm cross query "Question" --all                    # Query all notebooks in profile
nlm cross query "Question" --notebooks "id1,id2"     # Target specific notebooks
nlm batch query "Summarize" --tags "embedded"       # Query by tag
```

### Studio Artifact Generation
```bash
nlm audio create <notebook> --format deep_dive --confirm  # Podcast generation
nlm report create <notebook> --format "Study Guide" --confirm # Report generation
```
