#!/usr/bin/env bash
set -euo pipefail

TAG="${1:-ykc3}"
MODEL_DIR="/workspace/${TAG}_lora/models"

mkdir -p "$MODEL_DIR"
cd "$MODEL_DIR"

if [[ -z "${CIVITAI_TOKEN:-}" ]]; then
  echo "Set CIVITAI_TOKEN in the RunPod terminal first."
  echo 'Example: export CIVITAI_TOKEN="your_token_here"'
  exit 1
fi

wget -c -O anyAnimaForLora_102.safetensors \
"https://civitai.com/api/download/models/3017846?fileId=2896767&token=${CIVITAI_TOKEN}"

rm -f anyAnimaForLora_101.safetensors
ln -s anyAnimaForLora_102.safetensors anyAnimaForLora_101.safetensors

wget -c -O qwen_3_06b_base.safetensors \
https://huggingface.co/circlestone-labs/Anima/resolve/main/split_files/text_encoders/qwen_3_06b_base.safetensors

wget -c -O qwen_image_vae.safetensors \
https://huggingface.co/circlestone-labs/Anima/resolve/main/split_files/vae/qwen_image_vae.safetensors

ls -lh "$MODEL_DIR"
