---
name: memory-bank
description: This skill containg guildlines on writting memory bank - a bunch of markdown's documentation that Cline reads at the start of every task to understand the project and continue work effectively. Use when the user explicitly asks to update memory bank, or when you need to read memory bank files. Triggered by phrases like "update memory bank", "read memory bank", "memory bank".
---

## Memory Bank Structure
The Memory Bank consists of core files and optional context files, all in Markdown
format. Files build upon each other in a clear hierarchy:
### Core Files (Required)
1. `projectbrief.md`
- Foundation document that shapes all other files- Created at project start if it doesn't exist
- Defines core requirements and goals
- Source of truth for project scope
2. `productContext.md`
- Why this project exists
- Problems it solves
- How it should work
- User experience goals
3. `activeContext.md`
- Current work focus
- Recent changes
- Next steps
- Active decisions and considerations
- Important patterns and preferences
- Learnings and project insights
4. `systemPatterns.md`
- System architecture
- Key technical decisions
- Design patterns in use
- Component relationships
- Critical implementation paths
5. `techContext.md`
- Technologies used
- Development setup
- Technical constraints
- Dependencies
- Tool usage patterns
6. `progress.md`
- What works
- What's left to build
- Current status
- Known issues
- Evolution of project decisions
### Additional Context
Create additional files/folders within memory-bank/ when they help organize:
- Complex feature documentation
- Integration specifications
- API documentation
- Testing strategies
- Deployment procedures## Documentation Update
## Memory bank operations protocol
1. **Initialization**: At project start, create the memory bank. Each project has ONE notebook. Memory bank lives as **Google Docs** in a Drive folder, added as Drive sources — auto-synced, no manual delete/re-add. The structure of the memory bank itself is described in the memory-bank skill. To nitilize memory bank you should create a Drive folder for a project and create core files in it. The create a notebook for the project, and upload all drive files as a source to the notebook.(for detailed MCP refference - see nlm-skill)
2. **Update**: Inspect recent session changes and identify the affected documents:
- **Focus / Task Shift** ➔ Edit `activeContext.md`.
- **Feature Completion / Bug Fix** ➔ Edit `progress.md` and `problemsSolved.md`.
- **Architecture / Structural Pattern** ➔ Edit `systemPatterns.md`.
- **New Dependency / Tool Setup** ➔ Edit `techContext.md`.
Then  update the documents in the memory bank. After you update the memory bank, sync the notebooklm sources:
  - notebook_list - find notebook id for the project, if not exist yet - create a new notebook for the project
  - Run nlm source sync <nb-id> --confirm  to sync the sources (for detailed MCP refference - see nlm-skill)
  Memory Bank updates occur when user requests with **update memory bank** (MUST review ALL files)
  - Verify all Drive sources report 'fresh' or 'synced'
  nlm source list <notebook-id> --drive
3. Memory Bank Context Retrieval Protocol
  At session startup or when triggered by "read memory bank", "load context", or "/load-mb", resolve the project's target notebook using. 
  Find the relevant notebooks nlm list notebooks --json 
  Execute `nlm notebook query <notebook-id> "Provide a holistic project overview: 1) Core goals and scope (projectbrief & productContext), 2) System architecture, technical constraints, and key design patterns (systemPatterns & techContext), and 3) Current focus, active decisions, and progress (activeContext & progress)"` to hydrate working memory. 
4. Memory Bank Freshness Verification Protocol
  Before initiating major architectural planning or when triggered by "verify memory bank", "check memory status", or "/check-mb", retrieve documented system patterns and tech context from NotebookLM (`nlm notebook query <notebook-id> "Summarize systemPatterns, techContext, and activeContext"`). Next, inspect the local codebase (key source files, directory structure, git log, and build configs) and compare actual implementation reality against documented memory. Identify architectural drift—such as unrecorded design patterns, new module dependencies, modified interfaces, or completed tasks not reflected in documentation. Come back to a user with report, highlighting discrepancies and suggesting updates to the memory bank. If discrepancies are found, prompt user to update memory bank with "update memory bank" command.




REMEMBER: After every memory reset, I begin completely fresh. The Memory Bank is my
only link to previous work. It must be maintained with precision and clarity, as my
effectiveness depends entirely on its accuracy.