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
1. Initialization Protocol
Local Repository Setup:
Create the local directory structure: /project_dir/.agents/memory-bank
Generate the core foundational files locally:
  1. projectbrief.md
  2. productContext.md
  3.activeContext.md
  4.systemPatterns.md
  5.techContext.md
  6.progress.md
2. Context Retrieval Protocol (Working Memory Hydration)
  Trigger: Session start, "read memory bank", "load context", or "/load-mb".
  Execution (Strictly Local):
  Do NOT query NotebookLM or fetch from Google Drive.
  Read local markdown files directly from .agents/memory-bank/ using standard workspace file-read tools.
3. Local Update Protocol
Trigger: Explicit user request ("update memory bank").
Execution:
Inspect recent session changes and git status to identify affected topics:
Task Switch / State Change ➔ Update .agents/memory-bank/activeContext.md.
Bug Fix / Completed Feature ➔ Update .agents/memory-bank/progress.md (and log the solution).
Architectural Pattern / Bitmask Fix ➔ Update .agents/memory-bank/systemPatterns.md.
Toolchain / Kconfig / Dependency Change ➔ Update .agents/memory-bank/techContext.md.
Directly edit the local markdown files in the workspace.
Validate that updates maintain technical precision (keep exact hex masks, function names, and struct definitions).
4. Freshness Verification Protocol
Trigger: Major architectural planning, "verify memory bank", "check memory status", or "/check-mb".
Execution:
Read local systemPatterns.md, techContext.md, and activeContext.md.
Inspect the local codebase state using local tools:
git status -s && git log -n 5 --oneline
Compare the documented system patterns against actual implementation reality in source files (e.g., DTS bindings, Kconfig, CMakeLists, driver headers).
Identify architectural drift (untracked registers, modified APIs, new workqueues).
Present a concise markdown delta to the user and apply updates directly to local memory bank files.
5. Remote verification protocol (syncing)
Trigger: User ask to push memory bank to the remote or sync memory banl
  There is a folder on google drive for each project, If there is no one for current project - create.
  The update all the core documents, append all changes that are on local memory bank.
  The sync the sources nlm source sync <id> --confirm. (load nlm-cli-skill to see notebook id's)




REMEMBER: After every memory reset, I begin completely fresh. The Memory Bank is my
only link to previous work. It must be maintained with precision and clarity, as my
effectiveness depends entirely on its accuracy.