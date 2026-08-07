---
name: nlm-skill
description: Dynamic architecture guide, profile routing rules, AI interaction protocols, and complete CLI reference for Google NotebookLM (nlm) knowledge base. Use when user ask you to intract with nlm
---

The NotebookLM environment is partitioned across multiple Google Account profiles. The list of notebooks is updated dynamically. As well as notes, so for each qurry get the list of notebooks on demand 
### Account Profile Taxonomy
1. **`work` profile (`[EMAIL_ADDRESS]`):**
   * Reserved for embedded engineering, firmware development, hardware datasheets, RTOS principles, MCU architectures (STM32, ESP32, nRF54), and work projects.
2. **`personal` profile (`[EMAIL_ADDRESS]`):**
   * Reserved for non-embedded studies, prompt engineering, personal projects, fitness/training, and general notes.
### Dynamic Discovery Protocol
When asked to query or update NotebookLM:
1. Determine the domain (Embedded/Work vs General/Personal).
2. Switch profile if necessary: `nlm login switch work` or `nlm login switch personal`.
3. Discover active notebooks dynamically: `nlm notebook list --json` (or use the MCP `notebook_list` tool).
4. Match notebook titles or tags dynamically against the user's request.
--- 
### Agent Interaction & Synthesis Directives 
A. On-Demand RAG Retrieval 
Querry the nlm to gail aditional context about the user request, then use the retrieved content and current context to generate a response. 
B. Knowledge Ingestion & Note Conversion 
Require explicit user request before uploading notes.
Add note: nlm source add <notebook_id_or_title> --text "Content" --title "Title".
C.Convert studio note to source, when user ask to conver finished note into source, use the following command:
`mcp_notebooklm_source_add(notebook_id="<id>", source_type="text", text="<content>", title="<title>")`.
