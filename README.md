# RunPod Anima LoRA Custom Template

This folder contains a minimal Docker template for Anima LoRA training on RTX 4090-class RunPod Pods.

## Included In This Template

- PyTorch 2.6.0 + CUDA 12.4 base image
- Latest `kohya-ss/sd-scripts`
- Anima training files:
  - `/workspace/sd-scripts/anima_train_network.py`
  - `/workspace/sd-scripts/networks/lora_anima.py`
- Upload helper for LoRA packages and model files
- Download helper for finished LoRA outputs
- Workspace file manager for browser upload/download
- Helper commands:
  - `check_anima_env`
  - `install_ykc_package ykc3`
  - `download_anima_models ykc3`
  - `start_file_manager`
  - `start_upload_server`
  - `start_download_server ykc3`

Model weights and character packages are intentionally not baked in. Keep Civitai tokens out of Dockerfiles and public registries.

## Ports

| Connect Port | Internal Port | Description |
| --- | --- | --- |
| 2999 | 2999 | Workspace file manager for upload and download |
| 8000 | 8000 | Browser uploader for packages and model files |
| 8001 | 8001 | Browser downloader for finished `.safetensors` outputs |

## Environment Variables

| Variable | Description | Default |
| --- | --- | --- |
| `UPLOAD_PORT` | Port used by `start_upload_server` | `8000` |
| `UPLOAD_DIR` | Directory where uploaded files are saved | `/workspace` |
| `DOWNLOAD_PORT` | Port used by `start_download_server` | `8001` |
| `DOWNLOAD_DIR` | Directory served when no tag is passed to `start_download_server` | `/workspace` |
| `FILE_MANAGER_PORT` | Port used by `start_file_manager` | `2999` |
| `FILE_MANAGER_ROOT` | Directory shown by `start_file_manager` | `/workspace` |
| `FILE_MANAGER_TOKEN` | Optional upload token for `start_file_manager` | not set |
| `CIVITAI_TOKEN` | Token used by `download_anima_models` for Civitai model download | not set |

Do not save `CIVITAI_TOKEN` in the template. Set it directly in the RunPod terminal only when downloading models.

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

6. Add HTTP ports `2999,8000,8001` if you want browser file helpers.
7. Save the template.

## Use On A Fresh Pod

If HTTP port `8000` is exposed, start the browser uploader from the Web Terminal:

```bash
start_upload_server
```

Open the RunPod HTTP service for port `8000`, upload `ykc3_lora_package.zip`, then stop the server with `Ctrl+C`.

Alternatively, if HTTP port `2999` is exposed, start the workspace file manager:

```bash
start_file_manager
```

Open the RunPod HTTP service for port `2999` to upload packages and download outputs from `/workspace`.

Then install the package:

```bash
check_anima_env
install_ykc_package ykc3
```

Download the model files:

```bash
export CIVITAI_TOKEN="set_this_in_runpod_terminal"
download_anima_models ykc3
```

`download_anima_models` downloads the current Anima base as `anyAnimaForLora_102.safetensors` from the official `civitai.com` API, then creates `anyAnimaForLora_101.safetensors` as a compatibility symlink because package training scripts expect that filename.

Start training:

```bash
bash /workspace/ykc3_lora/scripts/train_ykc3_anima_lora.sh
```

Training packages should use `--discrete_flow_shift=3` for the current Anima base recommendation. They also keep `--network_train_unet_only`, which leaves the Qwen/LLM side untrained and matches the recommended LLM Adapter LR `0` intent.

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
