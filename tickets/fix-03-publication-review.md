# fix-03-publication-review: Remove choice-order shortcuts and verify publication

- **Status:** In Progress
- **Branch:** `fix-03-publication-review`
- **Machine:** `/mnt/disks/data/colorbench`
- **Harness:** codex
- **Session ID:** parent collaboration `/root/review_colorbench`
- **Assignee:** Edward Benson
- **Base:** `653183f23b7855fd3c9c855c876995878631ca0f`
- **Date:** 2026-09-14
- **PR:** https://github.com/eob/colorbench/pull/4

## Goal

Audit the renderer, corpus, protocol, grading, execution evidence, statistics,
and publication prose. Repair material findings under a new frozen release,
rerun every model, and publish only verified results.

## Red evidence and mechanism

The 0.3.1 renderer inserts the reference target into three distractors sorted
along the stimulus coordinate. A solver that reads only the four option
pixels, chooses the RGB channel with greatest spread, and finds middle-ranked
options whose removal leaves monotone distractors achieves:

```
matching 48 35.5 0.7395833333333334 {1: 25, 2: 23}
binding 48 35.5 0.7395833333333334 {1: 25, 2: 23}
context 16 12.0 0.75 {1: 8, 2: 8}
smallmatch 16 12.0 0.75 {1: 8, 2: 8}
```

The expected score integrates uniform guessing over ambiguous candidates.
This uses no reference pixels, task axis, target color, or answer metadata.
It disproves the published assertion that answer rank caps this shortcut at
50%. Target rank was itself restricted to the middle two options.

Separately, `second-pilot.md` incorrectly reports zero retries and complete
usage. Its sealed evidence contains 3,225 HTTP requests inside 3,224 runner
attempts: one GPT-5.6 Sol response includes an unmetered internal retry.
The $21.49166615 ledger total includes a $0.10192 conservative reserve; the
metered token-price subtotal is $21.38974615.

## Plan and gates

1. Pin a reference-free option-order control and target-rank coverage.
2. Revise the candidate to distribute target rank over all four ranks and
   randomize distractor order; preserve 0.3.1 artifacts.
3. Render and independently validate the new corpus; audit nuisance balance,
   labels, pixel-derived answers, and option-only controls before freezing.
4. Freeze 0.3.2 with unchanged scoring semantics; run all thirteen configured
   models with a $50 cap and complete shared 264-question cohort.
5. Independently replay scores, reconstruct cost/retry evidence, seal, export,
   and write a dated methodological review and measured-results report.
6. Run full Python/TypeScript/typecheck/frozen-artifact gates, simplify changes,
   push and integrate. Supply exact publication paths to the website owner.

## Baseline gates

- `bun run test`: 244 Python tests, 29 TypeScript tests (1,413 assertions),
  typecheck pass.
- Release 0.3.1 validation and full 3,224-response finalization replay pass.

## Decisions and durable findings

- A passing frozen-artifact gate establishes reproducibility, not experimental
  validity. Add independent controls that deliberately omit the reference.
- Runner attempts aggregate provider-internal retries; do not describe their
  count as HTTP requests or infer zero transient errors from final success.

## 2026-09-14 progress

- Adopted a stronger repair than shuffling alone: identical option fields
  crossed with all four references, verified on full decoded masked images
  and canonical external prompts. Hue expands to 32 questions so both
  contexts have complete reference cells. Total: 264 questions / 232 PNGs.
- Source control tests: six RED failures, all six GREEN, then six failures
  on temporary source reversion. Logs are in `tickets/evidence/option-control-*`.
- Frozen dataset commit: `09b0dd9`; registered release/runner commit: `1b3079e`.
- Full pre-run gates: 250 Python tests, 35 TypeScript tests (1,474 assertions),
  TypeScript check, decoded gate, and preservation of historical releases pass.
- Paid campaign: `results/runs/0.3.2/pilot-20260914`, all thirteen models,
  concurrency six, $30 cap. Started from a clean checkout of `1b3079e`.
- Replayed 0.3.1 export and analysis byte-identically; independent numeric
  equations reproduce all 624 numeric grades within 3.13e-16 ΔE_OK and
  6.26e-13 score units. Supplemental accounting exposes the unmetered retry.
