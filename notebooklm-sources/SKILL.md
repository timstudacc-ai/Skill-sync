---
name: notebooklm-sources
description: Find YouTube playlists, long YouTube videos, and PDF documentation for any topic, strictly validate their accessibility, and push approved sources to Google NotebookLM via the MCP server.
---

# NotebookLM Source Collector Pipeline

When asked to collect study materials or sources for a topic to populate NotebookLM, follow this multi-phase pipeline.

## Phase 1: Research & Strict Validation
Invoke two parallel sub-agents (`invoke_subagent`):
1. **YouTube Content Researcher**
2. **Technical Documentation Researcher**

### CRITICAL: Sub-Agent Search & Validation Rules (Inline + API)
You MUST include the following instructions in the sub-agents' prompts:

**1. API-Driven Discovery (No Scraping):**
* **YouTube:** Do NOT use LLM web search/scraping to find videos. Use `run_command` with `yt-dlp "ytsearch5:<topic>"` to fetch clean, canonical links directly from the YouTube API.
* **PDFs:** Prefer querying open repositories directly via API or advanced search parameters rather than relying on standard web results that return wrappers.

**2. Inline Deterministic Validation:**
* Every single link found MUST be immediately validated before it is considered a success.
* Run the validation script on the link: `run_command` with `/home/tim/src_pipeline/link_validator.py "<URL>"`.
* The script automatically unwraps tracking URLs (e.g., Vertex AI), sanitizes HTML, and checks accessibility. 
* If the script outputs `INVALID`, the sub-agent MUST immediately discard the link and query for a replacement in the same step, enforcing a quota until a set number of `VALID` links is reached.

## Phase 2: User Validation & Ingestion
1. **User Review:** Create a Markdown artifact (`validation_list.md`) containing the verified links. Set `RequestFeedback: true` so the user can approve them. Ask the user for the target Notebook ID.
2. **Authentication Check:** Remind the user they can run `nlm login switch <profile>` via terminal if they need to switch accounts.
3. **Playlist Unpacking:** If the user approves a playlist, use `run_command` with `yt-dlp --flat-playlist --print id "<URL>"` to extract all individual video IDs.
4. **Ingestion:** Use `call_mcp_tool` -> `source_add` to add the verified URLs to the target notebook. Use the `urls` array parameter to submit bulk batches of up to 10 sources at a time to avoid rate limits.
