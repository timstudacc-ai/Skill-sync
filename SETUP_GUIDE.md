# Cline Skills Setup Guide for Remote Devices

> **Purpose:** Set up all synced skills from this repository on a fresh Cline installation.

---

## 1. Does Cline Sync Skills Across Devices Automatically?

**No.** Based on the Cline documentation (https://docs.cline.bot/features/skills and https://docs.cline.bot/cli/cli-reference):

- **Cline account (ClinePass / Cline API)** handles *only* provider authentication and billing. It does **not** sync skills, rules, or any configuration data across devices.
- **Skills are stored locally on disk** — there is no built-in cloud sync mechanism.
- There is **no `cline skill install` or `cline skill sync` CLI command**.
- You **must manually install skills on each device**.

---

## 2. Where Skills Live on Disk

Cline reads skills from **three possible locations** (per the CLI Reference and the official [cline/skills](https://github.com/cline/skills) repository):

| Scope | Path | Use Case |
|---|---|---|
| **Global (Cline-native)** | `~/.cline/skills/` | Skills available to all Cline sessions on this machine |
| **Global (cross-tool)** | `~/.agents/skills/` | Skills shared across Cline, Claude Code, Cursor, Gemini, Codex, etc. |
| **Project-level** | `.cline/skills/` (in your workspace root) | Skills available only in that specific project |

**Recommendation:** Use `~/.agents/skills/` (cross-tool location) — this is what your current machine uses, and it keeps skills consistent if you use multiple AI coding agents.

---

## 3. Quick Setup (One Command)

Clone this repo and let the sync script create all skill links:

```bash
git clone git@github.com:timstudacc-ai/Skill-sync.git ~/skill-sync
~/skill-sync/sync_skills.sh ~/skill-sync
```

**That's it.** Restart Cline and all skills will be discovered automatically.

The script creates **directory-level symlinks** in `~/.agents/skills/` — one per
skill folder — so the *entire* skill content (`SKILL.md`, `scripts/`,
`references/`, `assets/`, ...) is available to the agent, not just the main
file. Edits made through the symlink land directly in the repo working tree.

---

## 4. Detailed Setup (Step by Step)

### Step 1 — Prerequisites

```bash
# Ensure Cline CLI is installed
npm list -g cline 2>/dev/null || npm i -g cline

# Authenticate with your provider (once per device)
cline auth
```

### Step 2 — Clone the Skill Sync Repository

```bash
git clone git@github.com:timstudacc-ai/Skill-sync.git /tmp/skill-sync
```

### Step 3 — Create the Skills Directory

```bash
mkdir -p ~/.agents/skills
```

### Step 4 — Sync Skills Into Place

```bash
~/skill-sync/sync_skills.sh ~/skill-sync
```

This creates one symlink per skill folder in `~/.agents/skills/`. The `--dry-run`
flag previews changes without touching the filesystem. Temp/build junk
(`__pycache__/`, `*.pyc`) is never treated as skill content, and skill folders
that exist in `~/.agents/skills/` as real directories are automatically
re-linked when their content matches the repo ("split-brain healing").

### Step 5 — Copy the Global Rules

```bash
cp /tmp/skill-sync/GEMINI.md ~/.agents/AGENTS.md
```

### Step 6 — Clean Up

```bash
rm -rf /tmp/skill-sync
```

### Step 7 — Verify

```bash
ls ~/.agents/skills/
# Expected: memory-bank  nlm-cli-ai-ref  nlm-skill  notebooklm-sources
#           planning-skill  session-report  skill-creator  socrat
#           (plus any other skills from the repo)
```

Restart Cline. All skills should now appear in the **Skills menu** (scale icon at the bottom of the Cline panel).

---

## 5. Skill Structure Reference

Each skill must be a directory containing a `SKILL.md` file with YAML frontmatter:

**Bundled resources** are optional, but when present they must use the standard folder names:

| Folder | Purpose |
|---|---|
| `scripts/` | Executable logic (Python, JS, Bash) that the skill runs |
| `assets/` | Static files used *in the output* (`.docx`/`.html` templates, icons, fonts) |
| `references/` | Documentation the agent reads on demand |
| `evals/` | Eval-case definitions (`evals/evals.json`) — part of the skill-creator eval schema, which is why its packager excludes this name |
| `agents/` | Subagent instruction files (skill-creator only) |

Names such as `template/`, `eval-viewer/`, or misspelled folders do **not** match this convention: bundled code belongs in `scripts/`, bundled output templates in `assets/`.

```
~/.agents/skills/
├── memory-bank/
│   └── SKILL.md
├── nlm-cli-ai-ref/
│   └── SKILL.md
├── nlm-skill/
│   └── SKILL.md
├── notebooklm-sources/
│   └── SKILL.md
├── planning-skill/
│   └── SKILL.md
├── session-report/
│   ├── SKILL.md
│   ├── analyze-sessions.mjs
│   └── template.html
├── skill-creator/
│   ├── SKILL.md
│   ├── LICENSE.txt
│   ├── agents/        (subagent instructions, read on demand)
│   ├── assets/        (output templates, e.g. viewer.html)
│   ├── references/    (docs read on demand, e.g. schemas.md)
│   └── scripts/       (executable code)
└── socrat/
    └── SKILL.md
```

Every `SKILL.md` **must** have this format:

```markdown
---
name: skill-name        # Must match the directory name exactly
description: Brief description of what this skill does and when to use it.
---

# Skill Name

Detailed instructions for Cline to follow when this skill is activated.
```

---

## 6. Keeping Skills Updated

To pull the latest skills from the remote repository:

```bash
cd ~/skill-sync && git pull
~/skill-sync/sync_skills.sh
```

The script also runs `git pull`/`git push` itself at the end of each default-mode
run, so a cron entry alone keeps skills current:

```bash
# Add to crontab (crontab -e):
0 8 * * * /home/<your-user>/skill-sync/sync_skills.sh
```

---

## 7. Two-Way Sync Reference

Skills are edited in two places: inside the repo, or "in place" by an agent
through the `~/.agents/skills/` symlink (which writes straight into the repo).
If a skill ever exists as a *real directory* in `~/.agents/skills/` instead of a
symlink, the two copies can drift apart ("split-brain"). The script handles this:

| Situation | What the script does |
|---|---|
| Agent entry is a symlink into the repo | Left alone — already the desired state |
| Agent entry is a real dir, content **identical** to repo | Automatically re-linked (healed) |
| Agent entry is a real dir, content **differs** | Drift is listed file-by-file; nothing is overwritten |
| Repo skill was deleted, agent symlink remains | Reported as dangling; `--prune` removes it |

Commands:

```bash
sync_skills.sh --dry-run            # preview all of the above, change nothing
sync_skills.sh --prune              # delete dangling repo-pointing symlinks
sync_skills.sh --force              # default mode: repo wins on drifted dirs

# Agent -> repo (after editing a skill outside the repo):
sync_skills.sh --reverse            # copy whole skill trees back into the repo
sync_skills.sh --reverse --force lab-report   # overwrite repo copy for one skill
```

In reverse mode a whole-tree diff (excluding `__pycache__`/`*.pyc`/`.git`) decides
whether the repo copy is stale; without `--force` differing content is skipped,
never overwritten. After a reverse run: `git add -A && git commit && git push`.

---

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| Skills not showing in the Skills menu | Restart Cline after copying files. Check that each skill dir has a valid `SKILL.md` with `---` frontmatter delimiters. |
| Skill description not loading | Ensure the `name:` field in the YAML frontmatter **exactly matches** the directory name. |
| Skills load but bundled files aren't found | Verify relative paths in `SKILL.md` match the actual file structure inside the skill directory. |
| Want to force a skill immediately | Type `/` in the chat input to see available skill commands and select one. |

---

## Sources

- [Cline Skills Documentation](https://docs.cline.bot/features/skills)
- [Cline CLI Reference](https://docs.cline.bot/cli/cli-reference)
- [Official Cline Skills Repository](https://github.com/cline/skills)
- [Cline Rules Documentation](https://docs.cline.bot/customization/cline-rules)
