---
name: nlm-cli-ai-ref
description: Brief description of what this skill does
---

## Tips for AI Assistants

1. **Always run `nlm login` first** if any auth error occurs
2. **Use `--confirm` for all generation/delete commands** to avoid blocking prompts
3. **Capture IDs from create outputs** - you'll need them for subsequent operations
4. **Use aliases** for frequently-used notebooks to simplify commands
5. **Poll for long operations** - audio/video takes 1-5 minutes; use `nlm studio status` or `nlm status artifacts`
6. **Research needs a destination** - use `--notebook-id` for an existing notebook or `--title` to create one
7. **Re-authenticate only for stale/missing credentials** - `unverified` means the probe was inconclusive
8. **Use `--max-wait 0`** for single status poll instead of blocking
9. **⚠️ ALWAYS ask user before delete** - Before running ANY delete command, ask the user for explicit confirmation.Deletions are IRREVERSIBLE. Show what will be deleted and warn about permanent data loss.
10. **Check aliases before creating** - Run `nlm alias list` or `nlm list aliases` before creating a new alias to avoid conflicts with existing names.
11. **DO NOT launch REPL** - Never use `nlm chat start` - it opens an interactive REPL that AI tools cannot control. Use `nlm notebook query` or `nlm query notebook` for one-shot Q&A instead.
12. **Choose output format wisely** - Default output (no flags) is compact and token-efficient—use it for status checks. Use `--quiet` to capture IDs for piping. Only use `--json` when you need to parse specific fields programmatically.
13. **Verb-first vs Noun-first** - Both command styles work identically. Use whichever is more natural for the context. Noun-first groups by resource (notebook, source), verb-first groups by action (create, list, delete).
14. **Download workflow** - Always wait for artifact completion before downloading. Check status with `nlm studio status <notebook>`, get the artifact ID, then download with `nlm download <type> <notebook> <artifact-id>`.
15. **Artifact generation takes time** - Audio/video: 1-5 minutes. Reports/quizzes: 30-60 seconds. Always poll status before attempting download.
16. **Download output files** - If no `--output` specified, files are saved with default names (e.g., `audio_<id>.mp3`, `video_<id>.mp4`, `report_<id>.txt`). Use `--output` to specify custom filenames.
17. **Streaming downloads** - All downloads use efficient streaming to handle large files without memory issues. This is automatic.
18. **Drive source sync** - Use `nlm source stale <notebook>` or `nlm list stale-sources <notebook>` to check whichDrive sources need syncing before running sync commands.
19. **Use --wait for blocking source adds** - When adding sources before querying, use `nlm source add ... --wait` to block until processing completes. This ensures the source is ready for queries.
20. **Export to Google Docs/Sheets** - Reports can be exported to Google Docs, Data Tables to Google Sheets. Use `nlm export to-docs/to-sheets <notebook> <artifact-id>`.
21. **Batch with tags** - Tag notebooks first (`nlm tag add ... --tags "topic"`), then use `--tags` flag with batchcommands for targeted multi-notebook operations.
22. **Pipelines for automation** - Use `nlm pipeline list` to see available workflows, then `nlm pipeline run` for automated multi-step operations (ingest → generate).