---
name: nlm-skill
description: Dynamic profile routing, evidence-grounded RAG synthesis directive, and workflow protocols for Google NotebookLM (nlm).
---

# NotebookLM (`nlm`) Workflow & RAG Protocol

## 1. Profile Routing & Dynamic Discovery
Do **NOT** hardcode notebook IDs. Dynamically discover notebooks on demand.

* **`work` profile (`tymofij.frolov@alnicko.com`):** Embedded engineering, firmware (STM32, ESP32, nRF54), datasheets, RTOS.
* **`personal` profile (`timstudacc@gmail.com`):** Non-embedded research, prompting, personal projects, general notes.

**Discovery Workflow:**
1. Switch profile: `nlm login switch work` or `nlm login switch personal`.
2. List notebooks dynamically: `nlm notebook list --json` (or MCP `notebook_list`).

---

## 2. Agent Interaction & Synthesis Directives

### A. On-Demand RAG Retrieval
* **Trigger:** Query NotebookLM **only on-demand** when the user explicitly requests it (`check NLM`, `search notebook`, `query nlm`, `/nlm`).

### B. Evidence-Grounded Synthesis Directive (Anti-Parroting)
* 🛑 **NEVER copy-paste raw NotebookLM outputs or parrot retrieved blocks directly to the user.**
* ⚙️ **Synthesize & Adapt:** Treat retrieved NotebookLM content as **background domain facts and architectural rules**.
* 💡 **Grounding:** Write original, production-grade code and explanations in your own words, citing the retrieved principles as technical justification (e.g., *"Based on the thread-safety rules from the nRF54 notebook..."*).

### C. Knowledge Ingestion & Note Conversion
* Require explicit user confirmation (`save to NLM`, `/save-nlm`) before uploading notes.
* Add note: `nlm source add <notebook_id_or_title> --text "Content" --title "Title"`.
* Convert studio note to source: `mcp_notebooklm_source_add(notebook_id="<id>", source_type="text", text="<content>", title="<title>")`.
