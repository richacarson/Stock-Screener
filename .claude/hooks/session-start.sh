#!/bin/bash
set -euo pipefail

# Only run in the Claude Code on the web remote environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

python3 -m pip install --quiet -r requirements.txt
