FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/workspace/.cache/huggingface
ENV XDG_CACHE_HOME=/workspace/.cache

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    git \
    libgl1 \
    libglib2.0-0 \
    openssh-client \
    rsync \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/kohya-ss/sd-scripts.git /workspace/sd-scripts

WORKDIR /workspace/sd-scripts

RUN python -m pip install -U pip setuptools wheel \
    && pip install -r requirements.txt \
    && pip install bitsandbytes accelerate safetensors \
    && python - <<'PY'
from pathlib import Path
required = [
    Path("/workspace/sd-scripts/anima_train_network.py"),
    Path("/workspace/sd-scripts/networks/lora_anima.py"),
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("Missing Anima training files: " + ", ".join(missing))
PY

COPY check_anima_env.sh /usr/local/bin/check_anima_env
COPY install_ykc_package.sh /usr/local/bin/install_ykc_package
COPY download_anima_models.sh /usr/local/bin/download_anima_models
COPY upload_server.py /usr/local/bin/upload_server.py
COPY start_upload_server.sh /usr/local/bin/start_upload_server
COPY start_download_server.sh /usr/local/bin/start_download_server
COPY file_manager.py /usr/local/bin/file_manager.py
COPY start_file_manager.sh /usr/local/bin/start_file_manager
RUN chmod +x /usr/local/bin/check_anima_env /usr/local/bin/install_ykc_package /usr/local/bin/download_anima_models /usr/local/bin/upload_server.py /usr/local/bin/start_upload_server /usr/local/bin/start_download_server /usr/local/bin/file_manager.py /usr/local/bin/start_file_manager

EXPOSE 2999 8000 8001

WORKDIR /workspace

CMD ["bash", "-lc", "echo 'Anima LoRA template ready. Run: check_anima_env'; sleep infinity"]
