#!/bin/bash
# Sync code-review skill from canonical source to deployed locations
# Destinations: ~/.claude/skills/code-review/, ~/.claude-env/skills/code-review/, ~/.agents/skills/code-review/

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_NAME="code-review"

# Define destinations
DESTINATIONS=(
  "$HOME/.claude/skills/$SKILL_NAME"
  "$HOME/.claude-env/skills/$SKILL_NAME"
  "$HOME/.agents/skills/$SKILL_NAME"
)

# Rsync exclusions (don't sync these)
EXCLUDE_PATTERNS=(
  ".git/"
  ".claude/"
  "__pycache__/"
  "*.pyc"
  ".DS_Store"
  ".pytest_cache/"
  ".benchmarks/"
  "pyproject.toml"
  "scripts/sync.sh"
  ".gitignore"
)

# Build rsync exclude arguments
EXCLUDE_ARGS=()
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
  EXCLUDE_ARGS+=(--exclude="$pattern")
done

echo "Syncing $SKILL_NAME skill from $REPO_ROOT to deployed destinations..."
echo ""

SYNCED=0
for dest in "${DESTINATIONS[@]}"; do
  if [ ! -d "$dest" ]; then
    echo "⚠️  Skipping $dest (directory does not exist)"
    continue
  fi

  echo "Syncing to $dest..."

  # Use rsync with --delete to remove files that no longer exist in source
  # Trailing slash on source means sync contents; no trailing slash on dest means rsync into it
  rsync -av \
    --delete \
    "${EXCLUDE_ARGS[@]}" \
    "$REPO_ROOT/" \
    "$dest/"

  echo "✓ Synced to $dest"
  echo ""
  SYNCED=$((SYNCED + 1))
done

if [ "$SYNCED" -eq 0 ]; then
  echo "✗ Sync failed: none of the ${#DESTINATIONS[@]} destination directories exist." >&2
  exit 1
fi

echo "✓ Sync complete ($SYNCED destination(s))"
