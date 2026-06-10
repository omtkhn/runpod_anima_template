# RunPod Anima LoRA Custom Template

This folder contains a minimal Docker template for Anima LoRA training on RTX 4090-class RunPod Pods.

## What Is Baked In

- PyTorch 2.6.0 + CUDA 12.4 base image
- Latest `kohya-ss/sd-scripts`
- Anima training files:
  - `/workspace/sd-scripts/anima_train_network.py`
  - `/workspace/sd-scripts/networks/lora_anima.py`
- Helper commands:
  - `check_anima_env`
  - `install_ykc_package ykc3`
  - `download_anima_models ykc3`
  - `start_upload_server`
  - `start_download_server ykc3`

Model weights and character packages are intentionally not baked in. Keep Civitai tokens out of Dockerfiles and public registries.

## Build And Push

Use Docker Desktop, GitHub Actions, or another machine that can build Linux AMD64 images. The included `.github/workflows/publish-docker.yml` is ready for GitHub Actions.

### GitHub Actions Build With GHCR

This is the simplest path because it does not require Docker Hub.

1. Create a GitHub repository and upload every file from this folder.
2. Open Actions -> Publish Anima LoRA RunPod Image To GHCR -> Run workflow.

After it succeeds, the image will be:

```text
ghcr.io/YOUR_GITHUB_USERNAME/anima-lora-runpod:cu124-torch260
```

If RunPod cannot pull it, open the package page in GitHub and change package visibility to public.

### GitHub Actions Build With Docker Hub

1. Create a Docker Hub account.
2. Create a Docker Hub access token.
3. Create a GitHub repository and upload every file from this folder.
4. In the GitHub repository, open Settings -> Secrets and variables -> Actions.
5. Add these repository secrets:

```text
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
```

6. Open Actions -> Publish Anima LoRA RunPod Image -> Run workflow.

After it succeeds, the image will be:

```text
DOCKERHUB_USERNAME/anima-lora-runpod:cu124-torch260
```

### Local Docker Build

If you prefer to build locally:

```bash
cd runpod_anima_template

docker build --platform linux/amd64 -t YOUR_DOCKERHUB_USER/anima-lora-runpod:cu124-torch260 .
docker push YOUR_DOCKERHUB_USER/anima-lora-runpod:cu124-torch260
```

## Create RunPod Template

In RunPod:

1. Open Templates.
2. Create a custom Pod template.
3. Set Container Image to:

```text
YOUR_DOCKERHUB_USER/anima-lora-runpod:cu124-torch260
```

4. Use a container disk large enough for sd-scripts, models, package, and output. 40 GB can work for small jobs, while 80 GB is more comfortable.
5. Set the start command to the image default, or:

```bash
bash -lc "sleep infinity"
```

6. Add HTTP ports `8000,8001` if you want browser upload and download helpers.
7. Save the template.

## Use On A Fresh Pod

Upload `ykc3_lora_package.zip` to `/workspace`, then run:

If HTTP port `8000` is exposed, start the browser uploader from the Web Terminal:

```bash
start_upload_server
```

Open the RunPod HTTP service for port `8000`, upload `ykc3_lora_package.zip`, then stop the server with `Ctrl+C`.

Then run:

```bash
check_anima_env
install_ykc_package ykc3

export CIVITAI_TOKEN="set_this_in_runpod_terminal"
download_anima_models ykc3

bash /workspace/ykc3_lora/scripts/train_ykc3_anima_lora.sh
```

Expected output goes to:

```text
/workspace/ykc3_lora/output
```

To download results through the browser, expose HTTP port `8001`, then run:

```bash
start_download_server ykc3
```

Open the RunPod HTTP service for port `8001`, download the `.safetensors` files, then stop the server with `Ctrl+C`.

Download the resulting `.safetensors` before stopping or terminating the Pod if you are not using persistent storage.
