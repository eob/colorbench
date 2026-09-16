# Frozen releases

**0.4.0 contains 512 questions and 456 distinct images. Fresh measurements are
pending.** The new protocol repairs outline wording, gradient-endpoint and
single-patch shortcuts, and missing matched controls for surrounds and
geometry. See the [construction changes](../docs/direct-color-repairs-0.4.0.md)
and [methodology](../docs/methodology.md). Human agreement remains unmeasured.

The planned full campaign uses thirteen configurations on every question:
6,656 new responses. Even unchanged numeric images receive fresh requests;
responses from earlier releases are never copied into the new comparison.

## Freeze and run

A descriptor records `schema_version`, `benchmark_version`, `dataset_path`,
`dataset_manifest`, `dataset_git_commit`, `dataset_fingerprint`,
`evaluation_protocol_fingerprint`, and `expected_task_count`. Commit the
validated dataset before creating its descriptor. The fingerprint covers
manifest metadata and actual PNG bytes. The release gate checks committed
artifact bytes and inventory, canonical prompts, decoded targets, unique
answers, construction controls, and bundled font evidence.

The protocol fingerprint includes answer schemas, numeric score definitions,
prompts, native request construction, parsing, evaluation, color conversions,
and statistics. Changes require a new protocol identity. Version 0.4.0 retains
grading version `2` and the numeric scoring semantics, but its revised prompts
produce a different protocol fingerprint from 0.3.2. The new source deliberately
rejects an old protocol instead of silently reinterpreting old observations.

```bash
.venv/bin/python -m baseline.validate_dataset dataset/colorbench-v0.4.0/manifest.json
.venv/bin/python -m baseline.releases --release 0.4.0
.venv/bin/python -m baseline.runner --release 0.4.0 \
  --config config/models.all.json --run-id pilot-example \
  --concurrency 6 --budget-usd 65
```

Omitting `--max-tasks` selects the complete frozen cohort. The configured
roster comprises four Claude, four GPT, three Gemini, and two Muse models.
Model identifiers, catalog prices, output limits, endpoint timeouts, Git
identity, and invocation history are archived without API keys. Muse uses its
configured OpenAI-compatible endpoint, a 300-second timeout, and a
16,384-token output cap. These are the recorded configurations, not equalized
compute budgets or isolated reasoning interventions.

An unfinished run can resume under the same ID and unchanged identity. Invalid
model answers remain final observations and receive zero credit; infrastructure
failures remain retryable. The runner reserves estimated input and maximum
output costs before dispatch, including retry headroom. Unmetered attempts
leave marked conservative allowances in the ledger. These do not become
reported mean API-response costs; incomplete metering makes that mean null.
The budget is an accounting control based on catalog prices, not an invoice.

A successful process exit alone does not establish completion. Require
`summary.json` status `complete`, the intended thirteen-model roster, and
512 completed tasks for each model before committing and sealing the source
checkpoint. See [FINALIZATION.md](FINALIZATION.md). Publication uses an explicit
verified seal, not whichever scorecard was modified most recently.

The frozen-artifact gate protects registered dataset directories and
descriptors, entire previously sealed run directories, and existing top-level
JSON result snapshots. It allows unfinished checkpoints to advance, new runs
and exports to be added, and prose to clarify historical limitations.

## Historical releases

| Version | Questions | Distinct images | Status and interpretation |
| --- | ---: | ---: | --- |
| 0.3.2 | 264 | 232 | Measured; repaired the earlier option-order shortcut, but retained the task-control flaws addressed in 0.4.0. |
| 0.3.1 | 248 | 216 | Measured; a documented option-order shortcut limits its interpretation. |
| 0.3.0 | 248 | 216 | Superseded before a paid campaign after construction confounds were found. |
| 0.2.0 | 72 | 56 | Measured early pilot with answer-position/separation confounds. |

The [0.3.2 report](../results/third-pilot.md),
[0.3.1 report](../results/second-pilot.md), and
[0.2.0 report](../results/first-pilot.md) preserve their actual measurements.
Their scores do not transfer across corpora. The older semantic prototype is
also retained as history and is excluded from perception-benchmark results.

## Historical replay

Use the compatible 0.3.2 source pin in a separate checkout:

```bash
git clone https://github.com/eob/colorbench.git colorbench-replay-0.3.2
cd colorbench-replay-0.3.2
git checkout --detach 8fc558433146066b8e1ed9b44303689b2433478d
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m baseline.finalize \
  --run-dir results/runs/0.3.2/pilot-20260914 --verify
```

This offline replay checks all 3,432 stored observations, the dataset and
protocol identity, and the committed seal. It makes no model requests. The
[recorded compatibility check](../tickets/evidence/fix-05-frozen-historical-replay.log)
also reproduces the compact 0.3.2 export byte-for-byte. Keep that checkout's
protocol intact; do not weaken the new release gate to load historical data.
