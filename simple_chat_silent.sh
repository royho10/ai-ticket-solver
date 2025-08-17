#!/bin/bash
# Silent wrapper for simple_chat.py
# Redirects MCP protocol stderr output to /dev/null for clean chat experience

cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null
python -u simple_chat.py 2>/dev/null
