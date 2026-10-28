#!/usr/bin/env python3
"""A2ZAI Lab — Glimmer contestant driver (Modal-hosted, OpenAI-compatible).

Reuses meta_driver.py wholesale — same task-pack assembly, same blind exam
conditions, same validation and trace contract — and swaps ONLY the
transport: instead of the Meta Model API, it posts to a configurable
OpenAI-compatible endpoint (the vLLM server from modal_glimmer_app.py).

Env:
  GLIMMER_BASE_URL  e.g. https://<workspace>--glimmer-serve.modal.run/v1
  GLIMMER_API_KEY   bearer token matching the Modal app's expected key

Usage:
  GLIMMER_BASE_URL=... GLIMMER_API_KEY=... \
    python3 glimmer_driver.py --trial trial1-structuring-split \
      --run-name glimmer-trial1-run1 --agent glimmer-modal --no-schema
"""
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meta_driver  # noqa: E402

BASE_URL = os.environ.get("GLIMMER_BASE_URL", "").rstrip("/")
API_KEY = os.environ.get("GLIMMER_API_KEY", "")
SERVED_MODEL = os.environ.get("GLIMMER_MODEL", "meta-models/Muse-Glimmer-30B")


def call_api_glimmer(key, model, messages, max_tokens, use_schema, schema):
    if not BASE_URL:
        raise SystemExit("GLIMMER_BASE_URL is not set — deploy modal_glimmer_app.py first (see GLIMMER-RUNBOOK.md)")
    payload = {
        "model": SERVED_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    # vLLM accepts response_format json_schema on recent versions, but the
    # proven route from Day 1 is --no-schema (JSON-only instruction). If a
    # caller insists on schema mode we pass it through and let the scorer
    # gates judge the result honestly.
    if use_schema:
        payload["response_format"] = schema
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {API_KEY}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=1200) as resp:
            return json.loads(resp.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, (e.code, e.read().decode(errors="replace"))
    except urllib.error.URLError as e:
        return None, (0, str(e))


if __name__ == "__main__":
    meta_driver.call_api = call_api_glimmer
    # meta_driver.main() parses sys.argv; --model is accepted but the served
    # model id above is what actually gets called.
    meta_driver.main()
