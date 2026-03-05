#!/usr/bin/env bash
# Run Gmail OAuth once — opens browser; then copy printed lines to .env
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  echo "Creating .venv and installing dependencies..."
  python3 -m venv .venv
  .venv/bin/pip install -q google-auth-oauthlib google-auth-httplib2
fi
.venv/bin/python gmail/auth.py
