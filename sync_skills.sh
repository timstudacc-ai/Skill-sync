#!/usr/bin/env bash
#
# sync_skills.sh — (re)establish symlinks in $HOME/.agents/skills that point
# to each skill living in the skills git repository.
#
# The repository path is intentionally NOT hardcoded. It is resolved from the
# first of these that succeeds:
#   1. a positional CLI argument
#   2. the $SKILLS env var
#   3. the local git work-tree root of the directory containing this script
#      (so you can drop this script anywhere inside the repo and it finds it)
#   4. $HOME/skills
#
# Usage:
#   sync_skills.sh [REPO_PATH] [--dry-run] [--force]
#
#   --dry-run   show what would change without touching the filesystem
#   --force     overwrite an existing symlink/real directory at the destination
#
# What counts as a "skill": a directory that contains a top-level SKILL.md.
# Directories without SKILL.md (docs, assets, non-skill tooling) are ignored.
set -euo pipefail

usage() {
  sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

# ---- flags -----------------------------------------------------------------
DRY_RUN=0
FORCE=0
declare -a POSARGS=()
for a in "$@"; do
  case "$a" in
    --dry-run) DRY_RUN=1 ;;
    --force|--overwrite) FORCE=1 ;;
    -h|--help) usage ;;
    -*) echo "sync_skills: unknown flag '$a'" >&2; exit 2 ;;
    *) POSARGS+=("$a") ;;
  esac
done

# ---- 2. resolve the skills repository path (not hardcoded) -----------------
RESOLVE_REPO=''
if [[ "${#POSARGS[@]}" -gt 0 ]]; then
  RESOLVE_REPO="${POSARGS[0]}"
fi

if [[ -z "$RESOLVE_REPO" && -n "${SKILLS:-}" ]]; then
  RESOLVE_REPO="$SKILLS"
fi

# Self-discovery: if we live inside a git work-tree, use that as the repo.
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

# ---- 3. symlink destination (may be hardcoded / defaulted) -----------------
DEST="${SKILLS_DEST:-$HOME/.agents/skills}"
mkdir -p "$DEST"

echo "Syncing skills from: $REPO"
echo "            into: $DEST"
if [[ "$DRY_RUN" == 1 ]]; then echo "(dry-run — no changes will be made)"; fi

# ---- 4. create/update symlinks ----------------------------------------------
CHANGED=0
SKIPPED=0
FAILED=0

shopt -s nullglob
for dir in "$REPO"/*/; do
  name="$(basename "$dir")"

  # Only directories that carry their own SKILL.md are skills.
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
exit 0