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

Clone this repo and copy all skills into the cross-tool global directory:

```bash
git clone git@github.com:timstudacc-ai/Skill-sync.git /tmp/skill-sync
mkdir -p ~/.agents/skills
rsync -a --delete /tmp/skill-sync/ ~/.agents/skills/
# Copy the global rules file too
mkdir -p ~/.agents
cp /tmp/skill-sync/GEMINI.md ~/.agents/AGENTS.md
rm -rf /tmp/skill-sync
```

**That's it.** Restart Cline and all skills will be discovered automatically.

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

### Step 4 — Copy Skills Into Place

```bash
rsync -a --delete /tmp/skill-sync/ ~/.agents/skills/
```

This copies **all** skill directories (each containing a `SKILL.md` file) and the `GEMINI.md` rules file. The `--delete` flag ensures the target matches the source exactly (removes stale skills, adds new ones).

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
│   ├── agents/
│   ├── assets/
│   ├── eval-viewer/
│   ├── references/
│   └── scripts/
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
git clone git@github.com:timstudacc-ai/Skill-sync.git /tmp/skill-sync
rsync -a --delete /tmp/skill-sync/ ~/.agents/skills/
rm -rf /tmp/skill-sync
```

**Or** set up the existing cron-based auto-sync (if this device has a cron daemon):

```bash
# Add to crontab (crontab -e):
0 8 * * * /home/<your-user>/skill-sync/sync_skills.sh
```

---

## 7. Troubleshooting

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
