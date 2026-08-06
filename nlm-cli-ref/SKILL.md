---
name: nlm-cli-ref
description: Complete command reference guide for the nlm CLI and MCP tools. Use when executing or constructing nlm terminal commands.
---

# NotebookLM (`nlm`) CLI Reference Manual

## Installation & Setup
```bash
pip install notebooklm-mcp-cli
```

## Profile & Auth Management
```bash
nlm login                         # Login & extract cookies
nlm login --profile work          # Login to specific profile
nlm login switch <profile>        # Switch default profile
nlm login profile list            # List registered profiles
nlm login profile rename <old> <new> # Rename profile
nlm login profile delete <name>   # Delete profile
```

## Notebook Operations
```bash
nlm notebook list                      # List notebooks (table)
nlm notebook list --json               # List notebooks (JSON)
nlm notebook create "Title"            # Create notebook
nlm notebook get <id> --json           # Get notebook details
nlm notebook describe <id>             # AI summary of notebook
nlm notebook rename <id> "New Title"   # Rename notebook
nlm notebook delete <id> --confirm     # Delete notebook
nlm notebook query <id> "question"     # Query specific notebook
```

## Source Operations
```bash
nlm source list <notebook>                          # List sources
nlm source add <notebook> --url "https://..." --wait # Add URL
nlm source add <notebook> --file doc.pdf --wait     # Upload file
nlm source add <notebook> --text "data" --title "T" # Add text note
nlm source add <notebook> --youtube "https://..."   # Add YouTube
nlm source get <source-id>                          # Read content
nlm source describe <source-id>                     # AI summary of source
nlm source delete <source-id> --confirm             # Delete source
```

## Cross-Notebook & Batch Queries
```bash
nlm cross query "Question" --all                    # Query all notebooks
nlm cross query "Question" --notebooks "id1,id2"     # Target specific IDs
nlm batch query "Summarize" --tags "tag1"           # Query by tag
```

## Studio Artifacts & Downloads
```bash
nlm audio create <notebook> --format deep_dive --confirm
nlm video create <notebook> --format explainer --confirm
nlm report create <notebook> --format "Briefing Doc" --confirm
nlm download audio <notebook> <artifact-id> --output podcast.mp3
nlm download all <notebook> --output-dir ./exports
```
