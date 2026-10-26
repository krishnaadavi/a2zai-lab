#!/usr/bin/env python3
"""A2ZAI Lab — examiner-side trace analyst (Muse Spark 1.3).

Takes a COMPLETED run's trace.json + score.json (produced by
harness/runner.py) and asks Muse Spark 1.3, via the Meta Model API, to
write the public failure/success receipt: receipt.md in the run folder.

The analyst is examiner-side machinery. It sees only the run's own trace
and score — never the answer key — and is instructed to quote ONLY
numbers present in the score.json / trace.json it is given.

The API key is read from the MODEL_API_KEY environment variable only.
It is never hardcoded, printed, or logged.

Usage:
  MODEL_API_KEY=... python3 meta_analyst.py <run-dir> [--model muse-spark-1.3]
                                                      [--dry-run]

<run-dir> is a folder containing trace.json and score.json, e.g.
trial1-structuring-split/harness/runs/<run-name>.

--dry-run assembles the prompt, writes it to
drivers/last_analyst_prompt.txt, prints a size estimate, and makes NO
network call.
"""
import argparse, json, os, pathlib, sys, urllib.request, urllib.error

HERE = pathlib.Path(__file__).resolve().parent
API_URL = "https://api.meta.ai/v1/chat/completions"
DEFAULT_MODEL = "muse-spark-1.3"

SYSTEM = (
    "You are the A2ZAI Lab's trace analyst. You turn one completed agent "
    "run — its step-by-step trace and its score — into a public receipt "
    "that a smart non-specialist reader (think LinkedIn) can follow in "
    "about a minute.\n\n"
    "HARD RULES:\n"
    "- Quote ONLY numbers that appear in the score.json or trace.json "
    "provided. Do not invent, round, estimate, or import any number from "
    "outside them. If a figure is not present, leave it out.\n"
    "- Name alerts by their alert_id as they appear in the trace.\n"
    "- Plain language. No jargon without a one-phrase explanation.\n"
    "- Be exact about gates: if hard_gates_triggered is empty, say the "
    "run hit no hard gates; if it lists gates, name them and state the "
    "score cap consequence exactly as the score data states it.\n\n"
    "Write the receipt in Markdown with exactly these sections:\n"
    "# Receipt — <agent> on Trial #1 (model: <model or 'not recorded'>)\n"
    "## The score — the total and the component breakdown, as numbers.\n"
    "## What the agent did — how it worked the queue, in a few sentences.\n"
    "## What it caught — correct escalations, links it made (use the "
    "trace's trap_rewind data if present), rules cited well.\n"
    "## What it missed — dispositions or links the score shows it lost "
    "points on; if it lost none, say so.\n"
    "## Gates — hard gate outcomes, per the rules above.\n"
    "## The one-line verdict — a single sentence a reader could quote."
)


def assemble(run_dir: pathlib.Path):
    trace = (run_dir / "trace.json").read_text()
    score = (run_dir / "score.json").read_text()
    user = (
        "Here is the completed run. Write the receipt from these two "
        "documents and nothing else.\n\n"
        f"===== score.json =====\n{score}\n\n"
        f"===== trace.json =====\n{trace}\n"
    )
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": user}], (score, trace)


def est_tokens(text: str) -> int:
    return max(1, round(len(text) / 4))


def call_api(key, model, messages, max_tokens=8000):
    payload = {"model": model, "messages": messages,
               "temperature": 0.2, "max_tokens": max_tokens}
    req = urllib.request.Request(
        API_URL, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST")
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    else:
        # Secure Vault connection: Muse swaps in the real credential on the
        # approved request to api.meta.ai. The key itself never appears here.
        sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
        from dynamic_credentials import add_surrogate_to_request
        add_surrogate_to_request(req, "custom.meta-model-api",
                                 allowed_hosts=["api.meta.ai"])
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            return json.loads(resp.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, (e.code, e.read().decode(errors="replace"))
    except urllib.error.URLError as e:
        return None, (0, str(e))


def main():
    ap = argparse.ArgumentParser(description="A2ZAI Lab trace analyst (Muse Spark 1.3)")
    ap.add_argument("run_dir", help="folder containing trace.json and score.json")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    run_dir = pathlib.Path(a.run_dir).resolve()
    for f in ("trace.json", "score.json"):
        if not (run_dir / f).exists():
            print(f"ERROR: {run_dir / f} not found — the analyst needs a completed run.",
                  file=sys.stderr)
            return 1

    messages, (score, trace) = assemble(run_dir)
    full_text = "\n".join(m["content"] for m in messages)

    if a.dry_run:
        out = HERE / "last_analyst_prompt.txt"
        out.write_text("\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in messages))
        print("DRY RUN — no network call made.")
        print(f"Analyst prompt assembled from run dir: {run_dir}")
        print(f"  - score.json: {len(score)} chars")
        print(f"  - trace.json: {len(trace)} chars")
        print(f"  - system prompt: {len(SYSTEM)} chars (analyst instructions)")
        print(f"Total prompt: {len(full_text)} chars, ~{est_tokens(full_text)} tokens (chars/4 estimate)")
        print(f"Model that would be called: {a.model}")
        print(f"Written to: {out}")
        return 0

    key = os.environ.get("MODEL_API_KEY")
    if not key:
        print("NOTE: MODEL_API_KEY not set — using the Secure Vault connection "
              "(custom.meta-model-api) via surrogate credential exchange.")

    resp, err = call_api(key, a.model, messages)
    if err is not None:
        code, body = err
        print(f"ERROR: Meta Model API call failed (HTTP {code}): {body[:500]}",
              file=sys.stderr)
        return 1

    choice = resp["choices"][0]
    print(f"finish_reason: {choice.get('finish_reason')}")
    content = (choice["message"].get("content") or "").strip()
    if not content:
        print("ERROR: analyst returned empty content "
              "(reasoning may have consumed the token budget).",
              file=sys.stderr)
        return 1
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("markdown"):
            content = content[8:]
        content = content.strip()
    receipt = run_dir / "receipt.md"
    receipt.write_text(content + "\n")
    usage = resp.get("usage") or {}
    print(f"Receipt written: {receipt}")
    print(f"Analyst tokens: prompt={usage.get('prompt_tokens')} "
          f"completion={usage.get('completion_tokens')} total={usage.get('total_tokens')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
