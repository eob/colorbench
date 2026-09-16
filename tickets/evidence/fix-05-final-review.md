# Independent final campaign review — 2026-09-16

**Result: pass. No publication-blocking execution or analysis discrepancy found.**

This review read the closed SQLite database with `mode=ro&immutable=1`, the JSONL attempt ledger, all thirteen scorecards, the frozen manifest, final results, seal, and the exported publication/analysis/audit JSON. It made no provider calls, acquired no finalizer lock, and changed no campaign, dataset, protocol, or source files. Independent calculations imported no benchmark grader, statistics, analyzer, or finalizer implementation. Machine-readable findings and artifact hashes are in [fix-05-final-review.json](fix-05-final-review.json).

## Identity and coverage

- Source checkpoint: `a04d7ec74cfb8cd739208fcbf228228ae6653a42`; dataset fingerprint: `3c6b248bfc25f4810c0083bbc5af3c5905fb1000795b21fdd0a57969a7aa3bc0`.
- Exactly 13 configured models × all 512 unique task IDs = 6,656 terminal responses. All 456 PNGs and 200 analysis group IDs are represented by the common full cohort.
- The SQLite integrity check passes. JSONL equals the SQLite attempt rows; scorecards and sealed results equal terminal SQLite records. Artifact SHA-256 values match the seal and raw checkpoint bytes match the source commit.
- Four invocation records document the intended checkpoints/resumes. Every invocation has identical model configurations, no task limit, and a clean recorded source identity. No model/task pair appears twice in the ledger; no response was retried after reaching a valid or invalid terminal answer.
- Runtime provider, grader, protocol, generator, dataset, and release files do not change across invocation commits. The sole change under those source trees is `src/matched-render.test.ts`, which moves a test browser probe into Node; inspection confirms it does not affect campaign inputs or execution.
- Every result's family, group, ground truth, prompt SHA-256, image path, and recording interval matches its frozen task and invocation.

## Execution and cost accounting

| Quantity | Independently reproduced value |
| --- | ---: |
| Runner attempts / terminal answers | 6,656 / 6,656 |
| HTTP requests | 6,660 |
| Internal retries | 4 |
| Unmetered HTTP attempts | 4 |
| Separate unresolved infrastructure attempt rows | 0 |
| Recorded token usage × frozen catalog rates | $44.20451775 |
| Unmetered reserve allowances | $0.239334 |
| Accounted ledger total | $44.44385175 |

The four recovered retries are Sol `colorbench-oklch-13`, Gemini Pro `colorbench-matching-29`, Terra `colorbench-oklch-14`, and Gemini Flash `colorbench-smallmatch-52`. Each has two HTTP attempts, one unmetered attempt, and a preserved reserve. Per-attempt cost reconciles to recorded token usage plus the configured reserve formula. All four results are valid.

The audit correctly reports `usage_complete: false`. The runner's `cost_incomplete: false` means no attempt has a null accounted ledger cost; it does **not** mean every HTTP request supplied token usage. These costs are frozen catalog-rate calculations and allowances, not invoices. Individual failed HTTP bodies/statuses within an internal retry are not retained, so their precise causes cannot be reconstructed. Whole-response cost means are correctly withheld for the four affected models, each with only 511 fully metered responses; corresponding family means follow the same rule.

## Invalid answers retained

| Model | Task | Recorded failure | Scoring treatment |
| --- | --- | --- | --- |
| Claude Opus 5 | `colorbench-hue-22` | 4,096-token output cap; response stopped with `max_tokens` | Invalid choice, incorrect, score 0 |
| GPT-5.6 Luna | `colorbench-oklch-04` | 4,096-token output cap; incomplete response | Invalid numeric answer; both scores 0; distance absent |
| Muse Spark 1.2 | `colorbench-context-52` | Prose preceding a JSON object | Invalid choice, incorrect, score 0 |
| Muse Spark 1.3 | `colorbench-context-30` | 16,384-token output cap; incomplete response | Invalid choice, incorrect, score 0 |

All four are stored exactly once with raw evidence and metered usage. None was selectively replaced. Muse 1.2's embedded choice is B while the ground truth is D, so extracting the JSON would not have turned this particular failure into a correct answer. Its statement about sampling pixels is response text, not evidence of tool execution.

## Grade and analysis replay

- Reparsed every valid raw answer and independently checked all choice grades against the manifest.
- Recomputed all 623 valid numeric distances and both numeric scores using direct OKLab matrices and Python `colorsys` HSL conversion; agreement is within the required tolerances (this independent calculation has zero recorded distance drift). The 624th numeric result is Luna's invalid answer and remains zero in mean scores.
- Replayed 319 model/family, pooled, slice, and hue-context metric calculations. Checked reported cost-completeness and latency means for every model and family.
- Replayed all matching/binding pairs, numeric-format pairs, matched surround/size/outline comparisons, same/different response-mapping comparisons, hue contexts, and RGB reconstruction counts against terminal records. No discrepancy with the exported analysis or audit.

Decision-relevant totals:

- Neutral context: **168/208** correct. The same references under surround rotations score **137, 144, 147, and 139/208**. Each comparison has 208 paired observations; the neutral observations are reused, so the four comparisons are not independent.
- Filled patches, 20px → 84px: **106 → 147/208** correct; 24 first-only successes and 65 second-only successes. Outlines, 3px → 12px: **101 → 112/208**; 24 first-only and 35 second-only successes.
- Same/different: **299/312** response-mapping pairs are semantically consistent, but **96 pairs are wrong under both mappings**. Consistency must not be presented as equality-detection accuracy. Thirteen pairs change their semantic judgment when the answer mapping changes; all mapping answers are valid.
- RGB: **14/208 exact**, **63/208 within two integer levels per channel**, and **122/208 within five**. All 208 RGB responses are valid.
- Numeric-format comparisons use **208 valid RGB/HSL pairs** and **207 pairs involving OKLCH**, excluding the one invalid OKLCH response. RGB has lower distance than HSL in 127 pairs, and lower distance than OKLCH in 141 pairs; these are paired descriptive counts, not independent population estimates.
- Fixed-lightness/chroma hue context: **186/208** correct; varying-lightness/chroma: **178/208**, including Opus's invalid as incorrect. This is a corpus slice, not an isolated causal estimate of hue context.

The repaired corpus remains a finite pilot without human validation. These checks support reporting its observed results and paired intervention contrasts; they do not establish model strategy, general psychophysical thresholds, or performance outside the supplied colors and layouts.

## Written report review

Independently reconstructed all 26 model rows in the matching/ordering/hue and semantic same/different tables in `results/fourth-pilot.md`, all three main numeric rows, and the principal numerical prose claims. The ranking of mean-error winners, Astra's approximate RGB results despite perfect choice accuracy, model counts improving under larger fills, outline regressions, and out-of-sRGB counts all agree with raw records.

The report now explicitly preserves the matching/component-fill confound: both neutral frames and question wording change, so it does not isolate a frame effect. Its two Opus illustrations use the actual `smallmatch-01/05/09/13` PNGs and responses. Independent visual inspection and raw-answer checks confirm A is correct in all four, with Opus answering D/A/A/D. The report identifies these as selected post-hoc examples and makes no repeatability claim. Reference **color** is held fixed; reference geometry changes along with the options.
