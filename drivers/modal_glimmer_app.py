#!/usr/bin/env python3
"""Serve Muse Glimmer (30B, Apache 2.0) on Modal behind an OpenAI-compatible
endpoint, for A2ZAI Lab's open-weights entrant runs.

STATUS: PREP — written Oct 27, 2026 from the documented vLLM pattern; not yet
deployed (needs Krish's Modal API token). Smoke-test decisions are listed in
GLIMMER-RUNBOOK.md (exact repo file layout + quantization flag).

Model: meta-models/Muse-Glimmer-30B (HF card: 29.6B params incl. perception
encoder, Apache 2.0, 131k context, released Aug 2026). BF16 weights ~60GB;
Meta ships 4-bit quantized variants that fit a 24GB card. We start on an
A100-40GB to dodge quantization surprises for the first scored run, then
optimize down if the numbers allow.

Run:
  modal deploy modal_glimmer_app.py        # persistent endpoint
  modal serve  modal_glimmer_app.py        # ephemeral, for smoke tests
Auth: the endpoint expects header  Authorization: Bearer <GLIMMER_API_KEY>
where GLIMMER_API_KEY is a Modal secret you create once:
  modal secret create glimmer-api-key GLIMMER_API_KEY=<random-long-string>
"""
import os
import subprocess

import modal

MODEL_ID = "meta-models/Muse-Glimmer-30B"
GPU = "A100-40GB"  # first-run choice: headroom over heroics; see runbook

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("vllm>=0.6", "huggingface_hub")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)
vol = modal.Volume.from_name("glimmer-weights", create_if_missing=True)
app = modal.App("a2zai-glimmer", image=image)


@app.function(
    gpu=GPU,
    volumes={"/weights": vol},
    secrets=[modal.Secret.from_name("glimmer-api-key")],
    timeout=60 * 60,
    scaledown_window=300,
)
@modal.web_server(port=8000, startup_timeout=600)
def serve():
    api_key = os.environ["GLIMMER_API_KEY"]
    cmd = [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", MODEL_ID,
        "--download-dir", "/weights",
        "--max-model-len", "16384",
        "--api-key", api_key,
        "--port", "8000",
    ]
    subprocess.Popen(cmd)
