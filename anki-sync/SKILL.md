---
name: anki-sync
description: Synchronize Anki cards with Google Drive — download new card .txt files from the Drive "Cards" folder, import them into Anki via AnkiConnect (with a local manual-import fallback if AnkiConnect fails), delete processed files from Drive, and log every run to ~/anki-card/sync_log.log. Use this skill for any request to sync, pull, or import Anki cards from Google Drive, to check sync status or the sync log, or when correcting sync failures — it is also the skill the scheduled cron sync run invokes. Trigger on "sync anki cards", "pull cards from drive", "import pending anki cards", "anki sync status", "did my cards sync", "clean up drive cards".
---

# Anki card syncer (Drive → Anki)

You run the synchronization between the user's Google Drive "Cards" folder and their local Anki. You run in two contexts and must behave differently:

- **Scheduled cron run (headless, no user is present):** never ask questions and never wait for input. On any blocking failure, log it per the logging rules and end the run.
- **Interactive run (the user asked to sync):** on blocking failures you may explain the situation and ask the user.

## Folders and state

- Drive: a folder named `Cards` (fallback source: Drive root).
- Local state directory: `~/anki-card/`. At run start, ensure `inbox/` and `processed/` exist there (`mkdir -p`).
- Log file: `~/anki-card/sync_log.log`. Every run appends here, whether it succeeds or fails.

## Step 0 — Preflight

1. Drive: verify the google-drive MCP tools are available and authenticated — call `authGetStatus`. If the tools are missing, disabled, or auth is not active, this is a preflight failure.
2. AnkiConnect: probe `http://127.0.0.1:8765` with bash curl, e.g. `curl -sS -m 5 -X POST http://127.0.0.1:8765 -d '{"action":"version","version":6}'`.
   - If unreachable, attempt to launch Anki once in the background (`anki >/dev/null 2>&1 &` — only when a desktop session appears available, e.g. `$DISPLAY` is set), then re-probe a few times over about 30 seconds.
   - If it stays unreachable: do NOT fail the whole run — switch the import step to the fallback path (Step 2b) and note this in the log.
3. Log the preflight outcome.

## Step 1 — Find and download new cards

1. Locate the `Cards` folder (search Drive). If the folder does not exist, list the root folder instead. If neither contains `.txt` card files → log `OK | no new cards`, end the run.
2. For each `.txt` file there, in name order:
   - A file with the same name already exists in `~/anki-card/processed/` → handled by an earlier run; skip it, do not re-download.
   - It already exists in `~/anki-card/inbox/` → keep the local copy (a previous run downloaded it but the import did not finish); do not re-download.
   - Otherwise → `downloadFile` it into `~/anki-card/inbox/`.
3. Any download failure → log `FAIL | download | <file> | <reason>` and end the run. No deletions ever follow a failure — see the ordering rule.

## Step 2 — Import into Anki (primary path: AnkiConnect)

For each file in `inbox/`:

1. Parse it: one card per line. If a line contains `;`, the semicolon separates fields (math card); otherwise `|` does (non-math card). The first segment is the question (Front); all remaining segments joined with `\n\n` form the answer (Back). Keep field text verbatim — never reformat math, HTML tags, or timestamps.
2. Create a deck named after the file (the file name without extension) if it does not exist (`createDeck`).
3. Add the notes in one `addNotes` call: `modelName: "Basic"`, fields Front/Back, tags `["auto-sync", "<file name>"]`, options `{"allowDuplicate": false}` so a retried file can never produce duplicate notes.
4. Verify: the number of successfully added notes must equal the number of parsed cards.
   - All succeeded → the file is imported; `mv` it to `~/anki-card/processed/`.
   - Anything failed or skipped (including duplicate rejections) → log the per-file details, leave the file in `inbox/`, and do NOT delete that file from Drive.
5. If AnkiConnect is entirely unreachable (fallback path from Step 0): stage instead of import. Leave the files in `inbox/`, and append a log line telling the user the manual-import path: open Anki → File → Import → select the file in `~/anki-card/inbox/`, field separator `|` or `;` as described above. No Drive deletion happens until a successful AnkiConnect import.

### Step 2b — Why the fallback keeps files

When AnkiConnect is down, the cards are not yet in Anki, so deleting them from Drive would destroy the only pending copy. The files stay in Drive and in `inbox/` until a later run imports them properly. If the user imports manually, tell them they can let you know so the file can be moved to `processed/` — AnkiConnect's duplicate guard still protects the next automatic run.

## Step 3 — Cleanup (only imported files)

For each file moved to `processed/`: delete it on Drive with `deleteItem` (file id from the download step). Note in the log: this moves the file to Drive trash — recoverable for 30 days, trash auto-empties afterward. If `deleteItem` fails → log `WARN | drive delete | <file> | <reason>`, do not keep retrying within the run; the local `processed/` marker already prevents any future duplicate import.

## Step 4 — Logging

Append to `~/anki-card/sync_log.log` (create it if missing). One line per event, semicolon-light pipe-separated fields:

```
2026-11-08T18:00:04 | RUN | start
2026-11-08T18:00:05 | OK | preflight | drive ok; ankiconnect ok (v6)
2026-11-08T18:00:07 | OK | imported 12 notes from "capacitor cards.txt" -> deck "capacitor cards"; file moved to processed
2026-11-08T18:00:08 | OK | deleted from Drive (trash): "capacitor cards.txt"
2026-11-08T18:00:08 | RUN | end | imported 12; failed 0
```

Failure lines:

```
2026-11-08T18:00:04 | RUN | start
2026-11-08T18:00:05 | FAIL | preflight | drive | authGetStatus: no active account | halted
2026-11-08T18:00:05 | RUN | end | imported 0; failed 1
```

Always include: timestamp, level (`OK` / `FAIL` / `WARN`), step, and a concrete reason. A run with nothing to do is `OK | no new cards`, not a failure.

## Ordering rule (and why it exists)

Never delete a file from Drive unless its cards were verified inside Anki in the same run. If Drive is cleaned before or during an import that then fails, the cards are gone forever with no local backup. Drive is the only durable copy of pending cards until the import succeeds — that is why cleanup is strictly last and file-scoped.

## Interactive requests

- "sync now" / "pull cards" → run the full workflow.
- "anki sync status" → read the last ~20 lines of `sync_log.log` and summarize the latest runs.
- "retry failed" → run the full workflow; files left in `inbox/` are retried automatically by design.
