#!/usr/bin/env bash
set -euo pipefail

TAG="${1:-ykc3}"
ZIP="/workspace/${TAG}_lora_package.zip"

if [[ ! -f "$ZIP" ]]; then
  echo "Missing package: $ZIP"
  echo "Upload ${TAG}_lora_package.zip to /workspace first."
  exit 1
fi

cd /workspace
rm -rf "${TAG}_lora"
unzip -o "$ZIP"
mv "${TAG}_lora_package" "${TAG}_lora"
mkdir -p "/workspace/${TAG}_lora/models"

for script in "/workspace/${TAG}_lora/scripts"/train_*_anima_lora.sh; do
  [[ -f "$script" ]] || continue
  python - "$script" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
text = text.replace(
    "source venv/bin/activate",
    "if [ -f venv/bin/activate ]; then\n  source venv/bin/activate\nfi",
)
path.write_text(text)
PY
done

chmod 755 "/workspace/${TAG}_lora"
chmod 755 "/workspace/${TAG}_lora/dataset"
chmod -R u+rwX,go+rX "/workspace/${TAG}_lora"

echo "Installed /workspace/${TAG}_lora"
echo "Patched training scripts to work with or without /workspace/sd-scripts/venv"
find "/workspace/${TAG}_lora/dataset/${TAG}" -maxdepth 1 -type f | sort
