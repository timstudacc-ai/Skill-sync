# AGENT.md - User Custom Skills Repository

## Overview
This repository contains custom user-defined AI skills designed for on-demand execution by AI agents. These skills form an interconnected ecosystem spanning knowledge retrieval, execution planning, system memory management, automated report generation, and skill lifecycle management.

## Skill Ecosystem & Interconnections
- **`memory-bank`**: Defines the Markdown structure and updates for long-term project memory (`projectbrief`, `productContext`, `activeContext`, `systemPatterns`, `techContext`, `progress`).
- **`nlm-cli-ai-ref`**: Provides command reference guidelines and operational safety rules for the `nlm` CLI tool.
- **`nlm-skill`**: Executes a 5-phase retrieval and synthesis pipeline with Google NotebookLM. Connects to `memory-bank` (storing memory files in Google Drive sources) and hands off to `planning-skill`.
- **`notebooklm-sources`**: Validates YouTube videos and PDF documentation via scripts/subagents and pushes clean sources to NotebookLM.
- **`planning-skill`**: A 4-phase gated state machine for system architecture planning. Checks `nlm-skill` in Phase 0 for missing domain/hardware facts before drafting execution plans.
- **`session-report`**: Analyzes session usage data via node script and embeds it into interactive HTML reports.
- **`skill-creator`**: Meta-skill for authoring, evaluating (evals/baselines), benchmarking, and optimizing skills and triggering descriptions.
- **`socrat`**: Socratic tutoring protocol for interactive learning and concept mastery.
