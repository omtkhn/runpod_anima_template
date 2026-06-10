#!/usr/bin/env bash
set -euo pipefail

export UPLOAD_DIR="${UPLOAD_DIR:-/workspace}"
export UPLOAD_PORT="${UPLOAD_PORT:-8000}"

python /usr/local/bin/upload_server.py
