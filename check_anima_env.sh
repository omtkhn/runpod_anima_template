#!/usr/bin/env bash
set -euo pipefail

echo "== GPU =="
nvidia-smi || true

echo
echo "== Python / Torch =="
python - <<'PY'
import torch
print("python ok")
print("torch", torch.__version__)
print("cuda available", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
PY

echo
echo "== sd-scripts Anima files =="
test -f /workspace/sd-scripts/anima_train_network.py
test -f /workspace/sd-scripts/networks/lora_anima.py
ls -lh /workspace/sd-scripts/anima_train_network.py /workspace/sd-scripts/networks/lora_anima.py

echo
echo "== Anima help smoke test =="
cd /workspace/sd-scripts
python anima_train_network.py --help >/tmp/anima_help.txt
head -40 /tmp/anima_help.txt

echo
echo "Environment looks ready."
