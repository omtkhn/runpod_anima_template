#!/usr/bin/env bash
set -euo pipefail

TAG="${1:-}"
PORT="${DOWNLOAD_PORT:-8001}"

if [[ -n "$TAG" ]]; then
  DOWNLOAD_DIR="/workspace/${TAG}_lora/output"
else
  DOWNLOAD_DIR="${DOWNLOAD_DIR:-/workspace}"
fi

if [[ ! -d "$DOWNLOAD_DIR" ]]; then
  echo "Missing download directory: $DOWNLOAD_DIR"
  echo "Usage: start_download_server ykc4"
  echo "Or: DOWNLOAD_DIR=/workspace/path DOWNLOAD_PORT=8001 start_download_server"
  exit 1
fi

cd "$DOWNLOAD_DIR"
echo "Serving downloads from $DOWNLOAD_DIR on port $PORT"
echo "Open the RunPod HTTP service for port $PORT."
python -m http.server "$PORT" --bind 0.0.0.0
