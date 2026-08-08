#!/bin/sh
set -eu

REPO="${PR_SKILLS_REPO:-malone-c/pr-skills}"
REF="${PR_SKILLS_REF:-main}"
DEST="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"

for skill in pr-description respond-to-comments; do
  mkdir -p "$DEST/$skill"
  curl -fsSL "https://raw.githubusercontent.com/$REPO/$REF/skills/$skill/SKILL.md" \
    -o "$DEST/$skill/SKILL.md"
  echo "installed $skill"
done

echo
echo "Installed to $DEST"
echo "Restart Claude Code, then use /pr-description and /respond-to-comments."
