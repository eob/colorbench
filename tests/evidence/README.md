# Pilot engine verification

Scope: Python protocol, parser, grading, release and image gates, native providers, model catalog, budgeted resumable execution, raw replay, offline finalization, and compact export. The initial prototype is commit `8c2cd592576e76c5acbd01f2e21c52d040b628bb`; execution and sealing machinery was ported from BorderBench `07ee6830be9ceb4a242c1edd78cb46321fe5c292`. The frozen dataset is committed at `1013fdb0deb1c2a4d2df6fba3c5bc38d05cab473`.

- `protocol-red.log`: 25 failures establish absent family parsing/grading and observed-cohort scoring.
- `protocol-reversion.log`: restoring the old provider module in an isolated Python process makes the six choice-parser cases fail again. No repository files were reverted.
- `dataset-gate-red.log`: the independent decoded-image gate was absent before implementation.
- `state-baseline-green.log`: 41 existing checkpoint/catalog checks already passed; copied sibling machinery preserved those behaviors.
- `final-review-red.log` and `final-review-reversion.log`: model cost subtotal forgery and unverified embedded PNG profiles were accepted before their checks; both fail again when those checks are disabled in an isolated process.
- `wire-schema-red.log` and `wire-schema-reversion.log`: nine provider/family cases show numeric bounds in native request schemas. The shared wire subset removes those unsupported keywords while local range validation remains strict. Anthropic's official structured-output documentation identifies numerical `minimum`/`maximum` as unsupported for raw HTTP requests: https://platform.claude.com/docs/en/build-with-claude/structured-outputs .
- `pilot-engine-green.log`: final full Python suite, **198 passed**, run with `/mnt/disks/data/borderbench/.venv/bin/python -B -m pytest tests -q` on the active branch based on dataset commit `1013fdb`.

After isolated reversions, 36 focused parser, wire-schema, subtotal and profile checks passed again. All native requests in tests use `httpx.MockTransport`; no paid inference was issued by this lane. The actual 72-question frozen dataset passed the independent pixel gate with zero errors. Model availability and current pricing checks are recorded separately in the root ticket's readiness evidence.

The implementation keeps choice accuracy and all three numeric-format scores separate. Numeric invalid responses contribute zero to the bounded mean score; raw error statistics describe valid predictions only. Related images retain group identity. Per-family costs and latency use the same scored rows, with unknown measurements retained as null. Sealed publications replay raw answers, compare committed checkpoints, and refuse further resume.

0.3.x Red/Green evidence lives in `tickets/plan-02-harder-tasks.md` (Red
evidence, adversarial review, gate matrix) rather than in per-log files;
the 0.2.0 logs above are preserved as the engine's construction record.
