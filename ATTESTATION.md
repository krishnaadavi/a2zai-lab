# Receipt Attestation — how a Lab score becomes checkable

*The Lab's rule: attestation is the receipt. This page explains, in plain
language, how anyone can check that a published score is the score the
harness actually produced.*

## What is hashed

Every scored run produces a small set of machine artifacts — the files the
harness itself wrote, before any human touched them:

- `decisions.json` — every decision the agent submitted, alert by alert
- `score.json` — the rubric breakdown the scorer awarded
- `final_score.json` — the final score, its cost basis, and the scoring rule
- `run_meta.json` — the run's metadata (model, tokens, cost, timing)

For each file we compute a **SHA-256 hash** — a 64-character fingerprint of
the file's exact bytes — and store the fingerprints in an `attestation.json`
record inside the run folder, together with the run name, the model, the
final score, a timestamp, and one **attestation hash**: a hash of all the
per-file fingerprints plus the run name, binding the whole set together.

A rejected run gets the same treatment over what it actually produced — its
`raw_response.txt` and `rejection.json` — labeled as a *rejection*
attestation. A failure is a receipt too.

Two things are deliberately **not** hashed: `receipt.md` (the plain-language
write-up — it is prose, and it legitimately receives dated corrections) and
`trace.json` / `replay.html` (views derived from `decisions.json`; attesting
the decisions covers their source).

## What the hash proves

**Tamper-evidence.** If anyone changes one byte in an attested file — edits
a decision, nudges a score — its fingerprint no longer matches the
attestation, and the verifier fails, naming the file. The published
decisions and score in a run folder with a valid attestation are the ones
the harness produced, bit for bit.

## What it does not prove

- It does not prove the *scoring was fair* — that's what the published
  rubric, gates, answer-key policy, and full traces are for.
- It does not prove *who* ran the stamper. The attestation is written by the
  Lab at publish time; it protects the record from that moment on. (Signed
  attestations — a private key only the Lab holds — are the obvious next
  step, and the record format leaves room for it.)
- It does not cover files outside the canonical set (see above).

## Verify it yourself

```bash
python3 tools/verify_receipt.py trials/trial-1-structuring-split/harness/runs/glimmer-trial1-run2
# OK glimmer-trial1-run2: attestation verified (final score 98.4, 4 files, attestation 7dc5f65dc6...)

python3 tools/attest.py <run_dir>   # stamp a new run (writes attestation.json)
```

Exit code 0 means every attested file matches. A nonzero exit names the
file that doesn't — try it: copy a run folder, change any number in
`score.json`, and run the verifier on the copy.

## Attested runs (stamped Oct 28, 2026)

| Run | Final | Attestation hash |
|---|---|---|
| wonder-trial1-run1 | 95.2 | `2a47a9329f55db7297e38f03dbe70fe710af08853ab7e25222b5349289aad1cf` |
| spark-trial1-run1 | 96.8 | `72a99b9fc2f910040375c5c2aacedbdda1c1b50f174dfbb10138fd8b33725682` |
| glimmer-trial1-run2 | 98.4 | `7dc5f65dc6dec4935dfd9a2d2754dedb9fd226f8663d1d309687e4497f2ad4da` |
| glimmer-trial1-run1 | rejected pre-scoring | `94ce4f330ecf29127c248b0af9f23d768be69050e0eb27fa40fe905d3a938249` |
