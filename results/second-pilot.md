# Second ColorBench pilot: results and critique

Measured 2026-09-13 using release 0.3.1. All 13 models completed the same
248 questions: **3,224 final responses, 3,224 attempts, zero invalid
responses, zero infrastructure errors, and no retries**. Estimated API cost
was **$21.49166615**, using recorded token usage and catalog prices. Every
request had complete usage evidence; no fallback token estimates or budget
reserves entered that total. The model catalog's Meta price-verification
limitation still applies.

The [sealed run](runs/0.3.1/pilot-20260913/) includes original responses,
checkpoint, configuration, scores, and artifact hashes. The finalizer replayed
every answer before publication. [Detailed analysis](colorbench-pilot-0.3.1-analysis.json)
is reproduced with:

```bash
.venv/bin/python scripts/analyze_pilot.py \
  results/runs/0.3.1/pilot-20260913 \
  results/colorbench-pilot-0.3.1-analysis.json
```

## What the second measurements show

Rows pool every model's answers within one family: 624 responses for
matching/binding, 208 for the 16-question families, 104 for gradient. These
describe this fixed pilot. They are not independent human-calibrated
observations, a combined benchmark score, or comparable to 0.2.0 scores.

| Choice family | Correct / scored | Accuracy |
| --- | --- | --- |
| Exact color matching | 436 / 624 | 69.9% |
| Lightness | 177 / 208 | 85.1% |
| Chroma | 200 / 208 | 96.2% |
| Hue | 182 / 208 | 87.5% |
| Component fill matching | 405 / 624 | 64.9% |
| Gradient matching | 104 / 104 | 100% |
| Same–different | 134 / 208 | 64.4% |
| Surround-shifted context | 116 / 208 | 55.8% |
| Small-region matching | 99 / 208 | 47.6% |

The ceiling broke. The 0.2.0 corpus had lightness and hue at 100% with
seven perfect matching scores; here only gradient remains at ceiling (all
thirteen models 8/8 — its construction was kept near 0.2.0 deliberately,
and it now carries no information). Chroma-near is the softest remaining
sweep endpoint at 86.5%, still too easy relative to its siblings.

Separation slices show clean difficulty gradients, with every level crossed
against every answer position by construction and gate enforcement:

| ΔL / ΔC / ΔH | Matching | Binding |
| --- | --- | --- |
| 0.08 / 0.025 / 35° (wide) | 96.2 / 94.2 / 98.1% | 96.2 / 88.5 / 98.1% |
| 0.04 / 0.012 / 15° (mid) | 82.7 / 84.6 / 90.4% | 78.8 / 63.5 / 86.5% |
| 0.02 / 0.007 / 8° (narrow) | 63.5 / 55.8 / 71.2% | 55.8 / 46.2 / 75.0% |
| 0.01 / 0.004 / 4° (near) | 34.6 / 32.7 / 34.6% | 30.8 / 28.8 / 30.8% |

Near-level matching sits just above the 25% chance baseline. Lightness
falls 98.1% → 92.3% → 88.5% → 61.5% across ΔL 0.10 → 0.01; hue falls
100% → 98.1% → 82.7% → 69.2% across 70° → 6°. Fixed vs varying
lightness/chroma hue contexts score nearly identically (86.5% vs 88.5%),
so that manipulation did not add difficulty as intended.

The new families rank by difficulty as designed: smallmatch 47.6% (dots
46.2%, frames 49.0% — no meaningful geometry difference), context 55.8%,
samediff 64.4%. But samediff hides a severe asymmetry: identical pairs
score 96.2% while differing pairs score 32.7%, below the 50% chance line.
Five models score 0/8 on differing pairs while perfect on identical ones —
a near-total "same" response bias. Only GPT-6 Astra discriminates both
(8/8 and 8/8); Claude Opus is the only other model without a strong bias
(5/8 identical, 4/8 differing). Without confidence ratings, sensitivity
and response criterion cannot be separated here.

One model stands apart on choice tasks: GPT-6 Astra answered all 200
choice questions correctly. That is a descriptive fact about these exact
stimuli, not a general perception claim — and it sets the bar the next
corpus must clear.

Matching/binding pairs share colors at all 48 groups. Across 624 paired
model/group observations, 365 pairs were both correct, 71 correct only in
flat matching, 40 only in component matching, and 148 both wrong. The
flat advantage (71 vs 40) is larger than in 0.2.0 but still describes one
UI treatment, not object binding in general.

The same sixteen target PNGs were used for every numeric representation.
All 624 numeric answers were valid, so valid-only errors cover the full
numeric sample in this run.

| Numeric format | Mean ΔE_OK | Mean similarity / 100 | Mean tight / 100 | ±0.01 band | ±2 LSB (RGB) | Out-of-sRGB |
| --- | --- | --- | --- | --- | --- | --- |
| RGB | 0.01348 | 93.26 | 74.66 | 51.4% | 25.0% | 0 |
| HSL | 0.01905 | 90.47 | 65.95 | 37.0% | — | 0 |
| OKLCH | 0.02584 | 88.79 | 61.67 | 31.2% | — | 17 |

Headline similarity still compresses the field (88.8–93.3); the tight
score (0.05 cap) and bands spread it: per-model tight means run 46.2–91.8
in RGB and 15.5–85.9 in HSL. Only 25.0% of RGB answers land within ±2 LSB
on all channels. The constant middle-gray baseline scores
approximately 18.11 on these sixteen targets.

Representation still matters on identical bytes: RGB had lower error than
HSL in 136 of 208 valid model/target pairs and lower than OKLCH in 141;
HSL beat OKLCH in 109. Seventeen OKLCH estimates fell outside sRGB,
including a GPT-5.6 Luna case with mean ΔE_OK 0.0693 despite competitive
RGB/HSL errors. Perception, coordinate knowledge, response strategy, and
request variability remain unseparated.

## What the benchmark itself needs to improve

**Same–different confounds sensitivity with response criterion.** The
below-chance differing-pair accuracy shows most models default to "same"
at these gaps. A follow-up should add confidence ratings or an adaptive
staircase so threshold and bias separate.

**Chroma-near and gradient-near are still too easy.** Chroma ΔC 0.008
scores 86.5% and gradient sits at 100%. The next sweep should push chroma
below 0.008 and rebuild gradient with near-threshold stop shifts instead
of the preserved wide construction.

**One model cleared every choice question.** GPT-6 Astra's 200/200 means
the choice corpus no longer discriminates at the top. Harder follow-ups —
smaller separations, stronger surrounds, smaller regions — are needed,
calibrated against human agreement so "hard" stays meaningful.

**Human agreement is still unmeasured.** Near-threshold accuracy cannot be
interpreted as super- or sub-human without it. The blinded five-observation
screen proposed in the 0.2.0 critique remains the next methodological step.

## One proposed next step

Run the human-agreement screen on the 0.3.1 corpus before building harder
stimuli: five blinded observations per question, scored against the same
decoded ground truth, reported per separation. That single dataset would
calibrate every gradient above, resolve whether the samediff asymmetry is
criterion or sensitivity, and set principled floors for the next sweep —
instead of chasing one model's ceiling in the dark.
