#!/usr/bin/env bash
set -euo pipefail

export FILE_MANAGER_ROOT="${FILE_MANAGER_ROOT:-/workspace}"
export FILE_MANAGER_PORT="${FILE_MANAGER_PORT:-2999}"

python /usr/local/bin/file_manager.py
