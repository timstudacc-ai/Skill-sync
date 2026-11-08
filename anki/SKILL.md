---
name: anki
description: Create Anki flashcards from a video, transcript, document, or raw notes, save them as an Anki-ready .txt file, and upload the file to the user's Google Drive "Cards" folder. Use this skill whenever the user asks to make flashcards, Anki cards, or study cards from any material — even if they never say "Anki" — and whenever they want cards uploaded to Google Drive. The user MUST state a card-count limit before any card is generated; if it is missing, stop and ask for it first.
---

# Anki flashcard creator

You create Anki flashcards that help the user remember facts, concepts, and ideas.

## Step 1 — Card count gate (do this before anything else)

Before generating any card, the user must have explicitly stated how many cards to create (for example, "up to 10 cards").

- If no count was given: stop and ask the user for a card count. Do not guess, do not invent a default number, and do not start drafting cards.
- Once a count is given, treat it as a hard cap. Never exceed it. Producing fewer cards than requested is acceptable when the material does not support more; padding to reach the number is not.

## Step 2 — Create the cards

Work from the video link, transcript, document, or raw notes the user provided.

1. Identify the key high-level concepts and ideas presented, including relevant equations. If the material is math- or physics-heavy, focus on concepts. If the material is not heavy on concepts, focus on facts.
2. Use your own knowledge of the concepts, ideas, or facts to flesh out additional details (relevant facts, dates, and equations) so every flashcard is self-contained.
3. Make question–answer cards, keeping questions and answers roughly in the same order as they appear in the source material.
4. If a video is provided, include timestamps in `[ ]` brackets at the end of questions, pointing to the relevant segment.

### Output format

- Save the result as a `.txt` file in the current workspace (`~/anki-cards`) with a short descriptive name, and also show the content in a code block.
- Do NOT make the first row "Question" and "Answer" — no header row.
- Each flashcard occupies exactly one line. One card = one line; never break a card across lines; a blank line is not a card.
- Separate the question and answer with the pipe character `|` for non-math content, and with a semicolon `;` for math content. Never use the separator character for anything else inside a card.
- When writing math, wrap it with the `( ... )` tags [eg, `( a^2+b^2=c^2 )`]; this is inline math by default. For block math, use `[ ... ]`. Decide when formatting each card.
- When writing chemistry equations, use the format `( \ce{C6H12O6 + 6O2 -> 6H2O + 6CO2} )` where the `\ce` is required for MathJax chemistry.
- For bold text use `<b></b>`. For italic text use `<i></i>`.
- Do not use a new line for visual purposes in the answer or question — a newline is what marks the next flashcard. If you need to list something inside a field, write it on the same line using `\n`.
- The card count from Step 1 is the only size limit; stay within it and be as exhaustive within that budget as the material supports.

## Step 3 — Upload to Google Drive

After the file exists locally:

1. Check that the google-drive MCP tools are available — a quick call to `authGetStatus` is a fast health check.
2. Look for a Drive folder named `Cards`: search for it (e.g. the `search` tool, or `listFolder` with no folder id to check the root). If it does not exist, create it with `createFolder` (name `Cards`, parent = root).
3. Upload the `.txt` with `uploadFile`, using `localPath` = the saved file and `parentFolderId` = the Cards folder id or the path `/Cards`.
4. If the `Cards` folder cannot be found or created, upload to the Drive root instead (omit `parentFolderId`).
5. Tell the user exactly where the file was uploaded (folder name).

## Error handling

| Failure | What to do |
|---|---|
| User never gave a card count | Stop and ask. Create nothing until answered. |
| google-drive MCP tools missing, disabled, or failing auth | Halt the upload step and tell the user precisely what is missing or failing, then ask for help. Point out that the local `.txt` file still exists and is safe. |
| Cards folder unusable | Fall back to the Drive root (rule 3.4). |
| Upload fails (after fallback) | Halt and ask the user for help, quoting the exact error message. |
| Anything else blocking | State what happened and what state the work is in (file created? uploaded?), then ask the user how to proceed. |

Never silently skip an upload, and never claim the upload succeeded if it did not.
