#!/bin/bash
# Silent wrapper for claude_chat_answers_only.py
# Redirects MCP protocol stderr output to /dev/null

cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null
python -u claude_chat_answers_only.py 2>/dev/null
