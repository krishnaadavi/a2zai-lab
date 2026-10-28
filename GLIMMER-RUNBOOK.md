# Glimmer Runbook — open-weights entrant (Trial #1 first)

Prepared Tue Oct 27, 2026. Everything below is ready except step 1, which is
Krish's (2 minutes, his account, his token — same pattern as the Meta key).

## Step 1 — Modal token (Krish)
Modal dashboard → Settings → API Tokens → create token → save it via the
Secure Vault card Muse provides. Muse stores it as the Modal connection
credential; it never lands in files or logs.

## Step 2 — Smoke test (Muse, ~15 min of compute)
1. `modal secret create glimmer-api-key GLIMMER_API_KEY=<random>` (value
   generated locally, stored with the connection, never printed).
2. `modal serve drivers/modal_glimmer_app.py` (ephemeral endpoint).
3. Verify, in order: weights download completes from `meta-models/Muse-Glimmer-30B`;
   `/v1/models` answers; one tiny chat completion returns text; one
   Trial-#1-shaped prompt (20k chars) returns parseable JSON with
   `--no-schema` behavior (JSON-only instruction).
4. Decision points the smoke test settles (do not guess them in advance):
   - Repo file layout: whether vLLM loads the repo root directly or a
     quantized subfolder is the right `--model` target.
   - Quantization: BF16 on A100-40GB first; try the 4-bit variant on A10G
     only after a scored BF16 run exists to compare against.
   - Throughput: tokens/sec at the trial's prompt size → feeds the
     Population Trials cost model.

## Step 3 — First scored run (Muse)
```
GLIMMER_BASE_URL=<modal endpoint>/v1 GLIMMER_API_KEY=<secret> \
  python3 drivers/glimmer_driver.py --trial trial1-structuring-split \
    --run-name glimmer-trial1-run1 --agent glimmer-modal --no-schema \
    --max-tokens 16000
```
Then the standard pipeline: score.py → cost_time.py → meta_analyst.py
(Spark writes the receipt) → replay.py → publish to the public repo →
wire into the /lab page next to Wonder 97.2 and Spark 96.8.

## Step 4 — Publish + posts
- Public repo commit with trace, score, receipt, replay (same as Day 1 runs).
- Day's build-in-public post: the third entrant is open-weights — this is
  also the Best Build on Meta Open Weights ($10K) lane entry, so the run's
  existence and its partner-inference route (Modal) get named explicitly.

## Budget guardrails
Modal: first run on the $30/mo free tier; a full Trial #1 pass is a few
GPU-dollars at most. Stop and report if a single deploy attempt burns >$10
without a served endpoint.
