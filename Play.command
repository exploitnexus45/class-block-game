#!/bin/sh
cd "$(dirname "$0")" || exit 1
if [ ! -x .venv/bin/python ]; then
  echo 'Complete the macOS installation steps in README.md first.'
  read -r answer
  exit 1
fi
.venv/bin/python main.py
