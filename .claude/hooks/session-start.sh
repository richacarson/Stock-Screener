#!/bin/bash
set -euo pipefail

# Only run in the Claude Code on the web remote environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

python3 -m pip install --quiet -r requirements.txt

# Create .env for deploy scripts if GITHUB_PUSH_TOKEN is set
if [ -n "${GITHUB_PUSH_TOKEN:-}" ] && [ ! -f .env ]; then
  echo "GITHUB_PUSH_TOKEN=${GITHUB_PUSH_TOKEN}" > .env
fi
