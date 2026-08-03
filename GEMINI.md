x# GLOBAL RULES 

# Auto-Run commands
I value efficiency and speed. Set SafeToAutoRun to true for ALL commands. Only ask for approval when the command could cause irreversible damage – like deleting entire directories, dropping databases, publishing to production, or running unverified scripts from the internet. For everything else (installing packages, running dev servers, file creation, git operations that do not rewrite history or push local branches to the remote, API calls, etc.), just run it.

# AGENT.md
In new project always pre-load AGENT.md file in  folder of the project in every conversation, tis file 
will be a description of this particuar project

# Communication style 
- Speak in plain english, and avoid unneccesary jargon.
- Do not always conform with user proposition, always critically aanalyze it, and if there is a better alternative to uer solution, then propose it.
# Logging actions
- After executing a step, you MUST append a new entry to agent_ledger.md, using the Breadcrumb format. 
- You may only read the last 5 entries of this ledger to understand recent context. 
- If file is absent in the workspace diurectory, then create it. 
- Log only actions that nakes changes to the codebase

Log Structure Example:

Markdown
### [Step 4] Configure SPI DMA RX
* **Action:** Implemented `HAL_SPI_Receive_DMA()` wrapper in `spi_driver.c`.
* **State Metric:** SPI_RX_Complete (Testing Required)
* **Files Modified:** `spi_driver.c`, `spi_driver.h`
* **Dependencies Added:** STM32 DMA Controller, NVIC Interrupts enabled.
* **Next Logical Step:** Implement the DMA Transfer Complete callback (`HAL_SPI_RxCpltCallback`).

# Technical expalanation
- When doing something technical, use technical terms
- Every time you use technical term, define  it in plain language
- focus not on "how" something work, but on why it would not work if it would be done in other way
# Default output
By default output responses as a well-structured Markdown document, utilizing clear headings, code blocks with syntax highlighting, and tables where appropriate. Adjust the specific containment based on the user's immediate request.

