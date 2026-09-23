# feat-06-september-2026-model-runs: Measure September models on ColorBench

- **Status:** Completed
- **Assignee:** Edward Benson
- **Branch:** `main` (direct publication requested)
- **Harness:** `codex`
- **Target release:** `0.4.0`
- **Source catalog:** `config/models.2026-09-22.json`
- **Catalog commit:** `a8c8a56acf4ba3b8cd2dad7270efc048e6a786bc`
- **Source checkpoint commit:** `82cde01`

## Goal

Run the complete frozen 512-question ColorBench cohort for `gpt-6-sol`,
`gpt-6-luna`, and `claude-opus-5-5` only. Commit and push the sealed source
evidence and a compact verified export for these three models. Keep the
dataset, prompts, evaluator, and prior result artifacts unchanged.

## Red evidence

Before adding the source catalog, the existing 13-model catalog could not
select the three September 22 models:

```text
AssertionError: Missing model configurations: ['claude-opus-5-5', 'gpt-6-luna', 'gpt-6-sol']
Missing requested ColorBench model IDs: claude-opus-5-5, gpt-6-luna, gpt-6-sol
```

## Plan and validation gates

1. Add a three-model catalog using provider model pages and standard API prices.
2. Validate the catalog and frozen release; run a small live preflight.
3. Resume the same campaign over all 512 questions per model; require `complete`.
4. Commit source evidence, seal the full cohort, verify the seal, and export
   publication data. Verify the source and export again after the final commit.

## Decisions and durable findings

The standing catalog contains four OpenAI and four Anthropic configurations.
The loader caps enabled models at five per provider endpoint, and that catalog
describes a prior full-cohort measurement. A dedicated catalog selects only
the new models and keeps the prior campaign intact.

## Validation gate matrix

| Gate | Result |
| --- | --- |
| `pytest -q tests/test_model_config.py` | 24 passed |
| `python -m baseline.releases --release 0.4.0` | 512 frozen questions; dataset/protocol identity verified |
| One-task live preflight, then full run | Three valid preflight responses; exactly 512 completed tasks for each model |
| `python -m baseline.finalize --scope full` | Sealed all 1,536 final responses from committed source `82cde01` |
| `python -m baseline.finalize --verify` | Passed independent seal replay |
| `scripts/analyze_pilot.py` | Generated three-model paired and family analysis |
| `scripts/audit_publication.py` | Independently graded 1,536 responses and 36 model-family summaries; zero invalid responses, retries, or missing usage |
| Old and new compact export comparison | Identical 512 task IDs and cohort fingerprint `c6bb84361fdffea7887f62ebdedbfa9c6d24da6466b5c90b750c0712bed7ecfa`; disjoint model rosters |

The run used 1,536 HTTP requests and cost an estimated $3.7491922 at
catalog rates. The published costs are estimates, not provider invoices.
