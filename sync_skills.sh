#!/usr/bin/env bash
#
# sync_skills.sh — two-way skill sync between git repo and agent runtime.
#
# DEFAULT MODE (repo -> agent):
#   Creates symlinks in ~/.agents/skills/ pointing to real files in the repo.
#   Run after git pull to distribute skills to the agent.
#
# REVERSE MODE (agent -> repo):
#   Copies real files from ~/.agents/skills/ into the repo so they can be
#   committed and pushed. Run after creating/editing a skill locally.
#
#   Why copy instead of symlink?
#   A symlink pointing outside the repo (~/.agents/skills/) would break on
#   other machines. Copy ensures git tracks the actual content.
#
# The repository path is resolved from the first of:
#   1. a positional CLI argument
#   2. the $SKILLS env var
#   3. the local git work-tree root of the directory containing this script
#   4. $HOME/skills
#
# In reverse mode the agent skills directory is resolved from:
#   1. --source PATH flag
#   2. the $AGENT_SKILLS_DIR env var
#   3. $HOME/.agents/skills
#
# Usage:
#   sync_skills.sh [REPO_PATH] [--dry-run] [--force] [--reverse]
#                  [--source AGENT_DIR] [skill1 ...]
#
#   --dry-run      show what would change without touching the filesystem
#   --force        overwrite existing entries at the destination
#   --reverse      pull agent skill content into the repo (copy, not symlink)
#   --source PATH  agent skills directory (reverse mode only; default: ~/.agents/skills)
#
# In default mode the script also:
#   - runs `git pull origin main` and `git push origin main` on the repo.
#     On a merge conflict it does nothing and logs the conflict to sync.log
#     (created next to the repo if missing).
#   - syncs rules: creates symlinks in ~/.agents/rules/ pointing to entries
#     in /home/tim/Documents/Cline/Rules/ (override with $RULES_SRC and
#     $RULES_DEST).
#
# Examples:
#   sync_skills.sh                           # repo -> agent (default)
#   sync_skills.sh --reverse                 # agent -> repo
#   sync_skills.sh --reverse --force lab-report  # pull specific skill
#
set -euo pipefail

usage() {
  sed -n '2,44p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

# ---- flags -----------------------------------------------------------------
DRY_RUN=0
FORCE=0
REVERSE=0
AGENT_SOURCE=""
declare -a POSARGS=()
for a in "$@"; do
  case "$a" in
    --dry-run) DRY_RUN=1 ;;
    --force|--overwrite) FORCE=1 ;;
    --reverse) REVERSE=1 ;;
    --source)
      AGENT_SOURCE="__NEXT__"
      ;;
    -h|--help) usage ;;
    -*) echo "sync_skills: unknown flag '$a'" >&2; exit 2 ;;
    *) POSARGS+=("$a") ;;
  esac
done

# Handle --source consuming the next positional arg.
if [[ "$AGENT_SOURCE" == "__NEXT__" ]]; then
  if [[ "${#POSARGS[@]}" -gt 0 ]]; then
    AGENT_SOURCE="${POSARGS[0]}"
    POSARGS=("${POSARGS[@]:1}")
  else
    echo "sync_skills: --source requires a path argument" >&2
    exit 2
  fi
fi
# ---- resolve the repository path -------------------------------------------
RESOLVE_REPO=''
REPO_FROM_POSITIONAL=0
if [[ "${#POSARGS[@]}" -gt 0 ]]; then
  first="${POSARGS[0]}"
  # In reverse mode, a bare name (no slash) is a skill filter, not a repo
  # path — rely on auto-resolution instead.
  if [[ "$REVERSE" == 0 || "$first" == */* ]]; then
    RESOLVE_REPO="$first"
    REPO_FROM_POSITIONAL=1
  fi
fi

if [[ -z "$RESOLVE_REPO" && -n "${SKILLS:-}" ]]; then
  RESOLVE_REPO="$SKILLS"
fi

if [[ -z "$RESOLVE_REPO" ]]; then
  SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if GIT_ROOT="$(cd "$SELF_DIR" && git rev-parse --show-toplevel 2>/dev/null)"; then
    RESOLVE_REPO="$GIT_ROOT"
  fi
fi

if [[ -z "$RESOLVE_REPO" ]]; then
  RESOLVE_REPO="$HOME/skills"
fi

REPO="$(readlink -f "$RESOLVE_REPO" 2>/dev/null || echo "$RESOLVE_REPO")"
if [[ ! -d "$REPO" ]]; then
  echo "sync_skills: repository not found: '$REPO' (searched arg, \$SKILLS, script location, \$HOME/skills)" >&2
  exit 1
fi

# ---- resolve the agent skills directory ------------------------------------
AGENT_DIR="${AGENT_SOURCE:-${AGENT_SKILLS_DIR:-$HOME/.agents/skills}}"
AGENT_DIR="$(readlink -f "$AGENT_DIR" 2>/dev/null || echo "$AGENT_DIR")"

# ---- sync.log ----------------------------------------------------------------
# Timestamped log next to the repo; created on first use.
LOG_FILE="$REPO/sync.log"
touch "$LOG_FILE"
log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') sync_skills: $*" >> "$LOG_FILE"
}

# ---- git pull/push after local sync -----------------------------------------
# Runs after local syncing. If `git pull origin main` hits a merge conflict,
# nothing is pushed; the conflict is recorded in sync.log and left untouched.
git_sync() {
  echo "Running git pull origin main (in: $REPO)"
  if ! git -C "$REPO" pull origin main >> "$LOG_FILE" 2>&1; then
    # Distinguish a real merge conflict from other pull failures.
    if [[ -n "$(git -C "$REPO" diff --name-only --diff-filter=U 2>/dev/null)" ]]; then
      log "CONFLICT: git pull origin main resulted in merge conflicts; doing nothing, no push attempted."
      echo "  !  merge conflict during pull — nothing pushed, see $LOG_FILE" >&2
    else
      log "ERROR: git pull origin main failed; doing nothing, no push attempted."
      echo "  !  git pull failed — see $LOG_FILE" >&2
    fi
    return 1
  fi
  echo "Running git push origin main (in: $REPO)"
  if ! git -C "$REPO" push origin main >> "$LOG_FILE" 2>&1; then
    log "ERROR: git push origin main failed."
    echo "  !  git push failed — see $LOG_FILE" >&2
    return 1
  fi
  log "OK: git pull + push origin main completed."
  return 0
}

# ---- rules sync (repo of rules -> agent runtime) -----------------------------
# Creates symlinks in ~/.agents/rules/ pointing to each entry (file or
# subfolder) in RULES_SRC. Same safety rules as the skills loop: existing
# entries are only replaced with --force.
RULES_SRC="${RULES_SRC:-/home/tim/Documents/Cline/Rules}"
RULES_DEST="${RULES_DEST:-$HOME/.agents/rules}"

sync_rules() {
  if [[ ! -d "$RULES_SRC" ]]; then
    echo "sync_rules: rules source not found: '$RULES_SRC' — skipping (set \$RULES_SRC to override)" >&2
    log "SKIP: rules source '$RULES_SRC' not found."
    return 0
  fi
  mkdir -p "$RULES_DEST"

  echo "Syncing rules from: $RULES_SRC"
  echo "             into: $RULES_DEST"
  if [[ "$DRY_RUN" == 1 ]]; then echo "(dry-run — no changes will be made)"; fi

  local r_changed=0 r_skipped=0 r_failed=0
  local entry name rsrc rdst
  shopt -s nullglob dotglob
  for entry in "$RULES_SRC"/*; do
    name="$(basename "$entry")"
    # Skip helper files that belong to the repo, not the runtime.
    [[ "$name" == "sync.log" || "$name" == ".git" ]] && continue
    rsrc="$(readlink -f "$entry")"
    rdst="$RULES_DEST/$name"

    if [[ -e "$rdst" || -L "$rdst" ]]; then
      if [[ -L "$rdst" && "$(readlink "$rdst")" == "$rsrc" ]]; then
        echo "  =  $name  (already linked)"
        r_skipped=$((r_skipped+1))
        continue
      fi
      if [[ "$FORCE" == 1 ]]; then
        if [[ "$DRY_RUN" == 1 ]]; then
          echo "  ~  $name  (would replace existing entry)"
        else
          echo "  ~  $name  replacing existing entry"
          rm -rf "$rdst"
          ln -s "$rsrc" "$rdst"
        fi
        r_changed=$((r_changed+1))
        continue
      fi
      echo "  !  $name  existing entry is not a matching symlink; use --force to replace (skipped)" >&2
      log "CONFLICT: rules entry '$name' exists at $rdst and is not a matching symlink; skipped."
      r_failed=$((r_failed+1))
      continue
    fi

    if [[ "$DRY_RUN" == 1 ]]; then
      echo "  +  $name  (would create -> $rsrc)"
    else
      echo "  +  $name  -> $rsrc"
      ln -s "$rsrc" "$rdst"
    fi
    r_changed=$((r_changed+1))
  done

  echo "----"
  echo "rules created/updated: $r_changed | already ok: $r_skipped | conflicts skipped: $r_failed"
}


# ---- helper: check if agent entry is already a symlink into the repo --------
already_in_repo() {
  local entry="$1"
  if [[ ! -L "$entry" ]]; then
    return 1
  fi
  local target
  target="$(readlink "$entry")"
  if [[ "$target" != /* ]]; then
    target="$(cd "$AGENT_DIR" && cd "$(dirname "$target")" 2>/dev/null && pwd)/$(basename "$target")"
  fi
  target="$(readlink -f "$target" 2>/dev/null || echo "$target")"
  [[ "$target" == "$REPO/"* || "$target" == "$REPO" ]]
}
# ---- main: choose direction ------------------------------------------------
if [[ "$REVERSE" == 1 ]]; then

  # ═══════════════════════════════════════════════════════════════════════════
  # REVERSE MODE — agent -> repo (copy)
  # ═══════════════════════════════════════════════════════════════════════════
  if [[ ! -d "$AGENT_DIR" ]]; then
    echo "sync_skills: agent skills directory not found: '$AGENT_DIR'" >&2
    echo "  (searched: --source flag, \$AGENT_SKILLS_DIR, \$HOME/.agents/skills)" >&2
    exit 1
  fi

  echo "Pulling agent skills from: $AGENT_DIR"
  echo "                   into: $REPO"
  if [[ "$DRY_RUN" == 1 ]]; then echo "(dry-run — no changes will be made)"; fi

  # If the repo path came from a positional arg, shift it off so the
  # remaining positional args are skill-name filters.
  if [[ "$REPO_FROM_POSITIONAL" == 1 ]]; then
    POSARGS=("${POSARGS[@]:1}")
  fi
  if [[ "${#POSARGS[@]}" -gt 0 ]]; then
    echo "  (filter: only skills matching: ${POSARGS[*]})"
  fi

  CHANGED=0
  SKIPPED=0
  FAILED=0

  shopt -s nullglob
  for dir in "$AGENT_DIR"/*/; do
    name="$(basename "$dir")"

    # Optional name filter.
    if [[ "${#POSARGS[@]}" -gt 0 ]]; then
      match=0
      for filter in "${POSARGS[@]}"; do
        if [[ "$name" == "$filter" ]]; then match=1; break; fi
      done
      [[ "$match" == 1 ]] || continue
    fi

    skill_file="$dir/SKILL.md"
    [[ -f "$skill_file" ]] || continue

    # Skip if the agent entry is already a symlink to the repo.
    dir_no_slash="${dir%/}"
    if already_in_repo "$dir_no_slash"; then
      echo "  =  $name  (already in repo — agent points to repo)"
      SKIPPED=$((SKIPPED+1))
      continue
    fi

    src="$skill_file"
    dst_dir="$REPO/$name"
    dst="$dst_dir/SKILL.md"

    mkdir -p "$dst_dir"

    if [[ -f "$dst" || -L "$dst" ]]; then
      if [[ -f "$dst" && ! -L "$dst" ]]; then
        # Regular file — compare content.
        if cmp -s "$src" "$dst"; then
          echo "  =  $name  (content identical)"
          SKIPPED=$((SKIPPED+1))
          continue
        fi
        if [[ "$FORCE" == 1 ]]; then
          if [[ "$DRY_RUN" == 1 ]]; then
            echo "  ~  $name  (would update — content differs)"
          else
            echo "  ~  $name  updating (content differs)"
            cp "$src" "$dst"
          fi
          CHANGED=$((CHANGED+1))
          continue
        fi
        echo "  !  $name  content differs from repo; use --force to overwrite (skipped)" >&2
        FAILED=$((FAILED+1))
        continue
      fi

      # Symlink or other non-regular file at destination.
      if [[ "$FORCE" == 1 ]]; then
        if [[ "$DRY_RUN" == 1 ]]; then
          echo "  ~  $name  (would replace non-file entry)"
        else
          echo "  ~  $name  replacing non-file entry"
          rm -rf "$dst"
          cp "$src" "$dst"
        fi
        CHANGED=$((CHANGED+1))
        continue
      fi
      echo "  !  $name  destination is not a regular file; use --force to replace (skipped)" >&2
      FAILED=$((FAILED+1))
      continue
    fi

    if [[ "$DRY_RUN" == 1 ]]; then
      echo "  +  $name  (would copy -> $dst)"
    else
      echo "  +  $name  copying -> $dst"
      cp "$src" "$dst"
    fi
    CHANGED=$((CHANGED+1))
  done

  echo "----"
  echo "copied: $CHANGED | already ok: $SKIPPED | conflicts skipped: $FAILED"
  echo ""
  echo "Next steps after copy:"
  echo "  git add -A && git commit -m \"pull skill(s) from agent\" && git push"
  echo "  On other machines: git pull && sync_skills.sh"

else

  # ═══════════════════════════════════════════════════════════════════════════
  # DEFAULT MODE — repo -> agent (symlink)
  # ═══════════════════════════════════════════════════════════════════════════
  DEST="${SKILLS_DEST:-$HOME/.agents/skills}"
  mkdir -p "$DEST"

  echo "Syncing skills from: $REPO"
  echo "            into: $DEST"
  if [[ "$DRY_RUN" == 1 ]]; then echo "(dry-run — no changes will be made)"; fi

  CHANGED=0
  SKIPPED=0
  FAILED=0

  shopt -s nullglob
  for dir in "$REPO"/*/; do
    name="$(basename "$dir")"
    [[ -f "$dir/SKILL.md" ]] || continue

    src="$REPO/$name"
    dst="$DEST/$name"

    if [[ -e "$dst" || -L "$dst" ]]; then
      if [[ -L "$dst" && "$(readlink "$dst")" == "$src" ]]; then
        echo "  =  $name  (already linked)"
        SKIPPED=$((SKIPPED+1))
        continue
      fi

      if [[ "$FORCE" == 1 ]]; then
        if [[ "$DRY_RUN" == 1 ]]; then
          echo "  ~  $name  (would replace existing entry)"
        else
          echo "  ~  $name  replacing existing entry"
          rm -rf "$dst"
          ln -s "$src" "$dst"
        fi
        CHANGED=$((CHANGED+1))
        continue
      fi

      echo "  !  $name  existing entry is not a matching symlink; use --force to replace (skipped)" >&2
      FAILED=$((FAILED+1))
      continue
    fi

    if [[ "$DRY_RUN" == 1 ]]; then
      echo "  +  $name  (would create -> $src)"
    else
      echo "  +  $name  -> $src"
      ln -s "$src" "$dst"
    fi
    CHANGED=$((CHANGED+1))
  done

  echo "----"
  echo "created/updated: $CHANGED | already ok: $SKIPPED | conflicts skipped: $FAILED"
  if [[ "$FAILED" -gt 0 && "$DRY_RUN" == 0 ]]; then
    echo "Re-run with --force to overwrite conflicting entries." >&2
  fi

  # Rules symlinks (source of truth: $RULES_SRC -> ~/.agents/rules)
  echo ""
  sync_rules

  # git pull/push only after local syncing is done.
  echo ""
  if [[ "$DRY_RUN" == 1 ]]; then
    echo "(dry-run — skipping git pull/push)"
    log "DRY-RUN: git pull/push skipped."
  else
    git_sync || true
  fi
fi

exit 0
