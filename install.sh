#!/bin/sh
# Links the router command and the /route skill into place. Safe to run again.
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$HOME/.local/bin" "$HOME/.claude/skills" "$HOME/.codex/skills"
ln -sfn "$ROOT/bin/router" "$HOME/.local/bin/router"
ln -sfn "$ROOT/skills/route" "$HOME/.claude/skills/route"
ln -sfn "$ROOT/skills/route" "$HOME/.codex/skills/route"
echo "Installed. Make sure ~/.local/bin is on your PATH, then run: router start"
