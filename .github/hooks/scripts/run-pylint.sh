#!/bin/bash
# Post-tool-use hook: runs pylint on Python files after they are edited or created.
# This hook is triggered by the Copilot agent after using the "edit" or "create" tools.
# It reads the tool invocation context from stdin (JSON), extracts the file path,
# and runs pylint if the target is a .py file. For .ipynb files, it converts
# the notebook to a temporary Python script via nbconvert, lints that, and cleans up.

set -e

INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | jq -r '.toolName')

# Only act on edit or create tool invocations
if [ "$TOOL_NAME" != "edit" ] && [ "$TOOL_NAME" != "create" ]; then
  exit 0
fi

FILE_PATH=$(echo "$INPUT" | jq -r '.toolArgs' | jq -r '.path // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# ── Python files ──────────────────────────────────────────────
if [[ "$FILE_PATH" == *.py ]]; then
  if command -v pylint &> /dev/null; then
    pylint "$FILE_PATH" --output-format=text --score=yes 2>&1 || true
  else
    echo "pylint is not installed. Install it with: pip install pylint"
  fi
fi

# ── Jupyter notebooks ────────────────────────────────────────
if [[ "$FILE_PATH" == *.ipynb ]]; then
  if command -v jupyter &> /dev/null && command -v pylint &> /dev/null; then
    TMPFILE=$(mktemp -t pylint_nb_XXXXXX.py)
    jupyter nbconvert --to script "$FILE_PATH" --stdout > "$TMPFILE" 2>/dev/null
    pylint "$TMPFILE" --output-format=text --score=yes 2>&1 || true
    rm -f "$TMPFILE"
  else
    echo "pylint and/or jupyter are not installed. Install with: pip install pylint jupyter nbconvert"
  fi
fi
