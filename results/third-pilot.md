# Third ColorBench pilot: corrected design, results, and critique

Measured 2026-09-14 using release **0.3.2**. All thirteen configurations completed
the same **264 questions**, producing **3,432 final responses**. The corpus
contains 232 unique PNGs and twelve separately reported families. No scores
are transferred from earlier releases.

## What changed before this run

The publication review found that 0.3.1 exposed the answer through ordered
distractors and restricted target ranks. An image-only control that ignored R
scored approximately 74–75% on matching, binding, context, and small-region
questions. Those historical results are reproducible, but they cannot
establish reference-dependent matching ability.

In 0.3.2, each four-choice option field is repeated with four references so
A, B, C, and D are correct once each. The entire image outside R and the
external prompt stay identical within each cell. The independent decoded-pixel
gate verifies all 42 cells. A deterministic predictor using only those remaining
inputs scores exactly 25%; a stochastic input-only predictor has expected
accuracy 25%. The old order-based control now scores 25% in every affected family.
Hue expands from 16 to 32 questions so both lightness/chroma contexts have full
reference cells. Grading and provider requests retain their frozen semantics.

This is a new corpus. Numerical differences from 0.3.1 or 0.2.0 are not model
improvement or deterioration. The [full review](../docs/publication-review-2026-09-14.md)
and [0.3.2 methodology](https://github.com/eob/colorbench/blob/8fc558433146066b8e1ed9b44303689b2433478d/docs/methodology.md) record the construction, checks,
and remaining limitations.

## Choice results

These counts pool this roster's responses within each family. Every model sees
the same questions; repeated references share option fields, and matching and
binding share colors. The counts are descriptive, not independent trials,
confidence intervals, or a combined model ranking.

| Family | Correct / scored | Accuracy | Chance |
| --- | ---: | ---: | ---: |
| Exact color matching | 472 / 624 | 75.6% | 25% |
| Component fill matching | 463 / 624 | 74.2% | 25% |
| Lightness | 181 / 208 | 87.0% | 50% |
| Chroma | 200 / 208 | 96.2% | 50% |
| Hue | 370 / 416 | 88.9% | 25% |
| Gradient matching | 103 / 104 | 99.0% | 25% |
| Same–different | 137 / 208 | 65.9% | 50% |
| Surround-shifted context | 128 / 208 | 61.5% | 25% |
| Small-region matching | 97 / 208 | 46.6% | 25% |

Small-region matching has the lowest pooled choice accuracy in this run
(46.6%). Families differ in both their task and chance
baseline, so that observation does not put their perceptual dimensions on one
scale. GPT-6 Astra answered all 216 choice questions correctly. This describes
these exact stimuli; general color understanding requires broader evidence.

### Separation slices and paired component matching

Each row below has four reference variants × thirteen models. Nominal gaps are
construction parameters; [decoded gaps](../tickets/evidence/decoded-gaps-0.3.2.json)
vary after 8-bit quantization. Base colors also differ between separation levels.
These slices do not isolate a causal gap effect or establish a human threshold.

| Axis | Intended nearest gap | Matching correct / 52 | Binding correct / 52 |
| --- | ---: | ---: | ---: |
| Lightness | 0.08 | 50 / 52 | 49 / 52 |
| Lightness | 0.04 | 47 / 52 | 46 / 52 |
| Lightness | 0.02 | 34 / 52 | 33 / 52 |
| Lightness | 0.01 | 27 / 52 | 24 / 52 |
| Chroma | 0.025 | 49 / 52 | 48 / 52 |
| Chroma | 0.012 | 42 / 52 | 42 / 52 |
| Chroma | 0.007 | 21 / 52 | 29 / 52 |
| Chroma | 0.004 | 23 / 52 | 16 / 52 |
| Hue | 35° | 52 / 52 | 52 / 52 |
| Hue | 15° | 49 / 52 | 49 / 52 |
| Hue | 8° | 45 / 52 | 43 / 52 |
| Hue | 4° | 33 / 52 | 32 / 52 |

The 624 matching/binding model–question pairs contain
420 both correct, 52 correct only in flat matching,
43 correct only in component matching, and 109 both incorrect.
The paired treatment adds neutral component frames and accompanying question
wording. It does not isolate frames alone or measure object binding in general;
related references remain correlated.

## Same-different response breakdown

The correct “same” letter changes by prompt, so an A/B confusion table cannot
by itself describe semantic response bias. This table decodes each task's
mapping. Each correct/total denominator includes invalid answers as incorrect.
The last column uses valid answers only: an invalid response is neither “same”
nor “different” and is not counted as a false alarm.

| Model | Identical: correct / total | Different: correct / total | Invalid | “Same” / valid responses |
| --- | ---: | ---: | ---: | ---: |
| Claude Fable 5.1 | 8 / 8 | 4 / 8 | 0 | 12 / 16 |
| Claude Haiku 4.5 | 8 / 8 | 0 / 8 | 0 | 16 / 16 |
| Claude Opus 5 | 6 / 8 | 4 / 8 | 0 | 10 / 16 |
| Claude Sonnet 5 | 8 / 8 | 1 / 8 | 0 | 15 / 16 |
| Gemini 3.1 Pro Preview | 8 / 8 | 1 / 8 | 0 | 15 / 16 |
| Gemini 3.5 Flash-Lite | 8 / 8 | 0 / 8 | 0 | 16 / 16 |
| Gemini 3.8 Flash | 8 / 8 | 1 / 8 | 0 | 15 / 16 |
| GPT-5.6 Luna | 8 / 8 | 7 / 8 | 0 | 9 / 16 |
| GPT-5.6 Sol | 8 / 8 | 3 / 8 | 0 | 13 / 16 |
| GPT-5.6 Terra | 8 / 8 | 6 / 8 | 0 | 10 / 16 |
| GPT-6 Astra | 8 / 8 | 8 / 8 | 0 | 8 / 16 |
| Muse Spark 1.2 | 8 / 8 | 0 / 8 | 0 | 16 / 16 |
| Muse Spark 1.3 | 8 / 8 | 0 / 8 | 0 | 16 / 16 |

Across this roster, identical pairs were correct in 102/104 responses,
and differing pairs in 35/104. Models answered “same” in
171/208 valid responses. Different pairs were incorrectly labeled “same” in
69/104 responses, while identical pairs were incorrectly labeled “different” in
2/104; this family had no invalid answers. The higher identical-pair accuracy
accompanies a tendency to answer “same” at these sampled gaps.
Eight identical and eight differing trials per model are too few and too
heterogeneous to establish stable sensitivity, response criteria, or a
psychometric threshold. Binary outcomes already describe the response tendency;
confidence ratings would add information rather than being a prerequisite.

## Numeric reconstruction

RGB, HSL, and OKLCH use the same sixteen target PNGs with independent requests.
Mean distance and band hit rates use valid answers; similarity and tight-score
means include all scored answers, assigning invalid answers zero.

| Format | Valid / scored | Mean ΔE_OK | Similarity / 100 | Tight / 100 | ΔE_OK ≤ 0.01 | RGB within ±2 | Out of sRGB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RGB | 208 / 208 | 0.01354 | 93.23 | 74.48 | 51.4% | 28.4% | 0 |
| HSL | 208 / 208 | 0.02001 | 90.00 | 65.83 | 38.5% | — | 0 |
| OKLCH | 208 / 208 | 0.02320 | 88.61 | 60.39 | 35.6% | — | 16 |

The headline similarity uses a 0.2 ΔE_OK cap; tight similarity uses 0.05. Both are
engineering normalizations, not visibility thresholds. The fixed middle-gray
control scores approximately 18.11 similarity on these targets. Out-of-sRGB
OKLCH estimates remain unclipped when scored, so a different clipped color
cannot receive credit. Format differences may reflect visual estimation,
coordinate knowledge, response strategy, and request variability.

## Execution and cost evidence

The campaign recorded **3,432 runner attempts** and
**3,437 HTTP requests**, including **5 internal retries**.
There are **5 unmetered HTTP requests** and
**1 invalid final answer**. There are
0 separate infrastructure failure records
in the finalized campaign; internal retries are a distinct count.

Recorded token usage multiplied by archived catalog prices totals
**$22.79714445**. The ledger spending estimate is
**$22.97445845**, including **$0.17731400** in
conservative allowances for unmetered requests. These are catalog-price
estimates, not provider invoices. Meta's inherited catalog prices retain their
documented verification limitation. The run stayed within its $30 budget.

Muse Spark 1.3 exhausted its 16,384-output-token limit on
`colorbench-context-06` and returned an incomplete response. That invalid
answer remains scored as incorrect and was not retried to obtain a better
answer. Its raw response is preserved.

The [execution and independent-scoring audit](colorbench-pilot-0.3.2-audit.json)
separates these quantities and reproduces all 3,432 grades and all 156
model–family summaries. Maximum independent numeric-distance drift is
4.51e-16; maximum similarity-score drift is
9.09e-13. The
[sealed run](runs/0.3.2/pilot-20260914/) preserves source answers, usage,
configurations, checkpoint, and final artifact hashes.

## What these results leave open

Human agreement remains unmeasured. This small synthetic corpus describes
performance through providers' image pipelines, not human-calibrated color
understanding or general UI-design ability. The gradient family has only two
underlying option fields, and numeric tasks have sixteen targets. One response
per model/task does not estimate run-to-run variability.

Small squares and outlines also differ in axis and hue, so their scores do not
isolate geometry. In the eight outline tasks, the external prompt says to
ignore “borders” while the image footer explicitly says to compare colored
outlines. The visible instruction makes the task answerable, but performance
can include resolving that wording; the [next-protocol correction](../tickets/fix-04-small-region-prompt.md)
is tracked. Context likewise uses fixed surrounds and lacks an otherwise
identical neutral control, so it cannot isolate surround causality.

A useful next step is a blinded human-agreement study on these fixed inputs,
reported by construction cell and separation. A factorial geometry/surround
follow-up and repeated model requests would address different limitations.
Those would be new measurements, not reinterpretations of this frozen run.

## Reproduce the report

Use compatible source `8fc558433146066b8e1ed9b44303689b2433478d` in a
separate checkout, following the [historical replay instructions](../releases/README.md#historical-replay).
Current 0.4.0 source intentionally rejects the old protocol fingerprint.

```bash
.venv/bin/python -m baseline.finalize \
  --run-dir results/runs/0.3.2/pilot-20260914 --verify
.venv/bin/python scripts/analyze_pilot.py \
  results/runs/0.3.2/pilot-20260914 results/colorbench-pilot-0.3.2-analysis.json
.venv/bin/python scripts/audit_publication.py \
  results/runs/0.3.2/pilot-20260914 results/colorbench-pilot-0.3.2-audit.json
```

[Compact publication data](colorbench-pilot-0.3.2.json) and
[detailed analysis](colorbench-pilot-0.3.2-analysis.json) accompany this report.
