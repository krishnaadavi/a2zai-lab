#!/usr/bin/env python3
"""A2ZAI Lab — blind contestant driver for the Meta Model API.

Runs ONE model against Trial #1 ("The Structuring Split") under exam
conditions:

- The prompt is assembled ONLY from the trial README's contestant brief
  and the four files in task-pack/ (alerts.csv, customers.json,
  ledger_90d.csv, policy_excerpt.md), verbatim. Nothing else enters the
  prompt — no baselines, no harness files, nothing from private/.
- The API key is read from the MODEL_API_KEY environment variable only.
  It is never hardcoded, printed, or logged.
- The model's decisions are validated locally, written to
  harness/runs/<run-name>/decisions.json, and scored by the existing
  harness/runner.py (which owns scoring via the examiner-side scorer).

Usage:
  MODEL_API_KEY=... python3 meta_driver.py [--model muse-wonder-1.0]
                                           [--run-name <name>]
                                           [--agent meta-model-api]
                                           [--max-tokens 8000]
                                           [--dry-run]

--dry-run assembles the prompt, writes it to drivers/last_prompt.txt,
prints the exact file list and a size estimate, and makes NO network call.

Default model is muse-wonder-1.0 (the frontier entrant). If the API
reports that model as not found / not enabled, the driver falls back to
muse-spark-1.3 and says so loudly in its output.
"""
import argparse, json, os, pathlib, subprocess, sys, time, urllib.request, urllib.error

HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parent
TRIAL = LAB / "trial1-structuring-split"
HARNESS = TRIAL / "harness"
API_URL = "https://api.meta.ai/v1/chat/completions"
DEFAULT_MODEL = "muse-wonder-1.0"
FALLBACK_MODEL = "muse-spark-1.3"
VALID_DISP = {"CLEAR", "MONITOR", "ESCALATE"}
VALID_RULES = {"P-1", "P-2", "P-3", "P-4", "P-5"}
TASK_PACK_FILES = ["alerts.csv", "customers.json", "ledger_90d.csv", "policy_excerpt.md"]

DECISIONS_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "aml_triage_decisions",
        "schema": {
            "type": "object",
            "properties": {
                "decisions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "alert_id": {"type": "string"},
                            "disposition": {"type": "string",
                                            "enum": ["CLEAR", "MONITOR", "ESCALATE"]},
                            "rule_cited": {"type": "string",
                                           "enum": ["P-1", "P-2", "P-3", "P-4", "P-5"]},
                            "evidence_fields": {"type": "array",
                                                "items": {"type": "string"}},
                            "linked_case_id": {"type": ["string", "null"]},
                            "one_sentence_reason": {"type": "string"},
                        },
                        "required": ["alert_id", "disposition", "rule_cited",
                                     "evidence_fields", "linked_case_id",
                                     "one_sentence_reason"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["decisions"],
            "additionalProperties": False,
        },
    },
}


def contestant_brief() -> str:
    """The trial README minus the operator-only folder map at the end."""
    text = (TRIAL / "README.md").read_text()
    marker = "\n## Folder map"
    if marker in text:
        text = text.split(marker)[0].rstrip() + "\n"
    return text


def assemble_messages(model_files_note=True):
    """Build (messages, source_files) from contestant-visible material only."""
    sources = []
    brief = contestant_brief()
    sources.append(("trial README — contestant brief (operator folder map excluded)",
                    str(TRIAL / "README.md"), len(brief)))
    parts = []
    for name in TASK_PACK_FILES:
        p = TRIAL / "task-pack" / name
        content = p.read_text()
        sources.append((f"task-pack/{name}", str(p), len(content)))
        parts.append(f"===== FILE: task-pack/{name} =====\n{content}")
    system = (
        "You are an AI agent under test in the A2ZAI Lab, working a real job: "
        "AML alert triage. Follow the brief exactly. Use ONLY the material "
        "provided below — the brief and the four task-pack files. Rules P-1 "
        "to P-5 in the policy excerpt are the only rules that exist for this "
        "job. Return your submission as a single JSON object of the form "
        "{\"decisions\": [ ... ]} containing exactly 25 decision objects, "
        "one per alert A01-A25, in the shape the brief specifies. Return "
        "JSON only — no commentary, no markdown fences."
    )
    user = brief + "\n\n" + "\n\n".join(parts)
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": user}]
    return messages, sources


def est_tokens(text: str) -> int:
    return max(1, round(len(text) / 4))


def call_api(key, model, messages, max_tokens, use_schema):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    if use_schema:
        payload["response_format"] = DECISIONS_SCHEMA
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
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
        body = e.read().decode(errors="replace")
        return None, (e.code, body)
    except urllib.error.URLError as e:
        return None, (0, str(e))


def model_unavailable(err) -> bool:
    if err is None:
        return False
    code, body = err
    b = body.lower()
    if code == 404:
        return True
    return ("model" in b and any(s in b for s in
            ("not found", "not enabled", "does not exist", "not available",
             "unknown model", "invalid model")))


def schema_unsupported(err) -> bool:
    if err is None:
        return False
    _, body = err
    b = body.lower()
    return "response_format" in b or "json_schema" in b


def extract_decisions(text):
    """Defensive parse: bare array, {decisions:[...]}, or fenced JSON."""
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
        t = t.strip()
    try:
        obj = json.loads(t)
    except json.JSONDecodeError:
        start = min([i for i in (t.find("["), t.find("{")) if i >= 0], default=-1)
        if start < 0:
            raise
        end = max(t.rfind("]"), t.rfind("}"))
        obj = json.loads(t[start:end + 1])
    if isinstance(obj, dict) and isinstance(obj.get("decisions"), list):
        return obj["decisions"]
    if isinstance(obj, list):
        return obj
    raise ValueError("response JSON is neither a list nor an object with a 'decisions' list")


def normalize(decisions):
    for d in decisions:
        if isinstance(d.get("disposition"), str):
            d["disposition"] = d["disposition"].strip().upper()
        if isinstance(d.get("rule_cited"), str):
            d["rule_cited"] = d["rule_cited"].strip().upper()
        if not isinstance(d.get("evidence_fields"), list):
            d["evidence_fields"] = [str(d["evidence_fields"])] if d.get("evidence_fields") else []
        d.setdefault("linked_case_id", None)
    return decisions


def validate(decisions):
    errs = []
    if not isinstance(decisions, list):
        return ["top level must be a list of decisions"]
    ids = [d.get("alert_id") for d in decisions if isinstance(d, dict)]
    want = [f"A{i:02d}" for i in range(1, 26)]
    if sorted(ids) != want:
        errs.append(f"must cover exactly A01-A25 once; got {sorted(set(ids))} (n={len(ids)})")
    for d in decisions:
        if not isinstance(d, dict):
            errs.append(f"non-object decision: {d!r}")
            continue
        if str(d.get("disposition", "")).upper() not in VALID_DISP:
            errs.append(f"{d.get('alert_id')}: bad disposition {d.get('disposition')!r}")
        r = (d.get("rule_cited") or "").strip().upper()
        if r and r not in VALID_RULES:
            errs.append(f"{d.get('alert_id')}: rule_cited {r!r} not in P-1..P-5")
        if not isinstance(d.get("evidence_fields", []), list):
            errs.append(f"{d.get('alert_id')}: evidence_fields must be a list")
    return errs


def main():
    ap = argparse.ArgumentParser(description="A2ZAI Lab blind contestant driver (Meta Model API)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--run-name", default=None)
    ap.add_argument("--agent", default="meta-model-api")
    ap.add_argument("--max-tokens", type=int, default=8000)
    ap.add_argument("--no-schema", action="store_true",
                    help="skip response_format json_schema; rely on JSON-only instruction")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    messages, sources = assemble_messages()
    full_text = "\n".join(m["content"] for m in messages)

    if a.dry_run:
        out = HERE / "last_prompt.txt"
        dump = "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in messages)
        out.write_text(dump)
        print("DRY RUN — no network call made.")
        print("Prompt assembled from exactly these contestant-visible sources:")
        for label, path, n in sources:
            print(f"  - {label}: {path} ({n} chars)")
        print(f"System prompt: {len(messages[0]['content'])} chars (driver boilerplate)")
        print(f"Total prompt: {len(full_text)} chars, ~{est_tokens(full_text)} tokens (chars/4 estimate)")
        print(f"Written to: {out}")
        return 0

    key = os.environ.get("MODEL_API_KEY")
    if not key:
        print("NOTE: MODEL_API_KEY not set — using the Secure Vault connection "
              "(custom.meta-model-api) via surrogate credential exchange.")

    model = a.model
    use_schema = not a.no_schema
    resp, err = call_api(key, model, messages, a.max_tokens, use_schema)
    if err is not None and schema_unsupported(err):
        print("NOTE: structured output (response_format json_schema) was rejected; "
              "retrying with JSON-only instruction.")
        use_schema = False
        resp, err = call_api(key, model, messages, a.max_tokens, use_schema)
    if err is not None and model_unavailable(err) and model != FALLBACK_MODEL:
        print(f"*** FALLBACK: model '{model}' is not available/enabled on this account. "
              f"Falling back to '{FALLBACK_MODEL}'. ***")
        model = FALLBACK_MODEL
        resp, err = call_api(key, model, messages, a.max_tokens, use_schema)
    if err is not None:
        code, body = err
        print(f"ERROR: Meta Model API call failed (HTTP {code}): {body[:500]}",
              file=sys.stderr)
        return 1

    try:
        print(f"finish_reason: {resp['choices'][0].get('finish_reason')}")
    except Exception:
        pass
    usage = resp.get("usage") or {}
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    total_tokens = usage.get("total_tokens")
    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens
    content = resp["choices"][0]["message"]["content"]

    try:
        decisions = normalize(extract_decisions(content))
    except Exception as e:
        print(f"ERROR: could not parse a decisions array from the model response: {e}",
              file=sys.stderr)
        raw = HERE / "last_raw_response.txt"
        raw.write_text(content)
        print(f"Raw response saved to {raw}", file=sys.stderr)
        return 1

    run_name = a.run_name or f"{model}-{time.strftime('%Y%m%d-%H%M%S')}"
    run_dir = HARNESS / "runs" / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    decisions_path = run_dir / "decisions.json"
    decisions_path.write_text(json.dumps(decisions, indent=2))

    errs = validate(decisions)
    if errs:
        (run_dir / "validation_failed.json").write_text(
            json.dumps({"validation_errors": errs}, indent=2))
        print(f"VALIDATION FAILED — decisions written to {decisions_path} but NOT scored:")
        for e in errs:
            print(f"  - {e}")
        return 2

    cmd = [sys.executable, "runner.py", str(decisions_path),
           "--agent", a.agent, "--model", model,
           "--out", f"runs/{run_name}"]
    if total_tokens is not None:
        cmd += ["--tokens", str(total_tokens)]
    print(f"Scoring with runner.py (agent={a.agent}, model={model}, "
          f"tokens={total_tokens}) ...")
    proc = subprocess.run(cmd, cwd=HARNESS, capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        print("ERROR: runner.py rejected the run.", file=sys.stderr)
        return proc.returncode

    score = json.loads((run_dir / "score.json").read_text())
    print("\n===== RUN COMPLETE =====")
    print(f"Model:            {model}")
    print(f"Run directory:    {run_dir}")
    print(f"Tokens (API):     prompt={prompt_tokens} completion={completion_tokens} total={total_tokens}")
    print(f"Score:            {score.get('subtotal_of_95')}/95 "
          f"(cost/time: {score.get('cost_time_5pts')})")
    for k, v in (score.get("components") or {}).items():
        print(f"  {k}: {v}")
    gates = score.get("hard_gates_triggered") or []
    print(f"Hard gates hit:   {gates if gates else 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
