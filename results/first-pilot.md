# First ColorBench pilot: results and critique

Measured 2026-09-13 using release 0.2.0. All 13 models completed the same 72
questions: **936 final responses, 936 attempts, zero invalid responses,
zero infrastructure errors, and no retries**. Estimated API cost was
**$5.1151914**, using recorded token usage and catalog prices. Every request had
complete usage evidence; no fallback token estimates or budget reserves entered
that total. The model catalog's Meta price-verification limitation still applies.

The [sealed run](runs/0.2.0/pilot-20260913/) includes original responses,
checkpoint, configuration, scores, and artifact hashes. The finalizer replayed
every answer before publication. [Detailed analysis](colorbench-pilot-0.2.0-analysis.json)
is reproduced with:

```bash
.venv/bin/python -m scripts.analyze_pilot \
  results/runs/0.2.0/pilot-20260913 \
  results/colorbench-pilot-0.2.0-analysis.json
```

## What the first measurements show

Each row below pools the 13 models' eight answers within one family: 104
responses per row. These describe this fixed pilot. They are not independent
human-calibrated observations or a combined benchmark score.

| Choice family | Correct / scored | Accuracy |
| --- | --- | --- |
| Exact color matching | 93 / 104 | 89.4% |
| Lightness | 104 / 104 | 100% |
| Chroma | 103 / 104 | 99.0% |
| Hue | 104 / 104 | 100% |
| Component fill matching | 91 / 104 | 87.5% |
| Gradient matching | 101 / 104 | 97.1% |

Lightness and hue have complete ceiling effects: every model scored eight of
eight. Chroma and gradients are also mostly at ceiling. These question sets
establish basic task success but distinguish these models poorly. We should
not interpret perfect scores as mastery of those color dimensions.

Matching and component fill matching expose more errors. Their aggregate
2-response difference does not establish a general UI penalty. Across the 104
paired model/target observations, 86 pairs were both correct, seven were
correct only in flat matching, five only in component matching, and six were
both wrong. Several models improve in the framed condition while others worsen.

The same eight target PNGs were used for every numeric representation. All
312 numeric answers were valid, so valid-only errors cover the full numeric
sample in this run.

| Numeric format | Mean ΔE_OK | Mean similarity / 100 | Out-of-sRGB estimates |
| --- | --- | --- | --- |
| RGB | 0.01236 | 93.82 | 0 |
| HSL | 0.01689 | 91.55 | 0 |
| OKLCH | 0.02123 | 89.39 | 4 |

Similarity uses the declared 0.2 error cap. Those scores do not mean 94%, 92%,
or 89% of colors were exactly correct, nor do they establish human visibility
thresholds. The constant middle-gray baseline scores approximately 30.56.

RGB had lower mean error than HSL for nine models, and lower mean error than
OKLCH for twelve. Across the 104 model/target pairs, RGB had lower error than
OKLCH in 75 cases. This is evidence that the requested representation matters.
It does not identify whether the difference comes from perception, coordinate
knowledge, response strategy, or independent request variability.

For example, GPT-5.6 Luna's fourth target had errors of approximately 0.00827
in RGB, 0.01648 in HSL, and 0.17412 in OKLCH despite identical image bytes.
Its OKLCH estimate was outside sRGB. Keep these tasks separate when discussing
color perception; averaging them into one model rank would hide that distinction.

## What the benchmark itself needs to improve

**The current matching/binding difficulty slices are confounded with answer
position.** Overall option positions are balanced, but wider-gap questions
always have the correct answer at A/C and narrower-gap questions at B/D.
The target colors also change between those sets.

Wide matching questions score 50/52 versus 43/52 for narrow questions. That
is not an isolated estimate of the effect of color separation. Gemini 3.5
Flash-Lite selected A on seven of eight matching questions, illustrating why
position preference can affect that split. Frozen pixel checks and overall
answer balance did not catch this experimental-design limitation.

The pilot remains a reproducible record of responses to these exact questions.
It does not yet support a clean discrimination threshold, calibrated difficulty
curve, or fine model ranking. Eight questions per family, correlated numeric
formats and UI pairs, a small color range, one rendering condition, and no
measured human agreement constrain what we can conclude.

## One proposed next step

Build a separation sweep for matching and its paired component version:
**use each base color at every chosen separation along lightness, chroma, or hue,
and rotate the correct answer through all four positions at every separation.**
Keep target size, option size, neutral surround, and response format fixed;
pair flat and framed conditions on the same color, separation, and position.
Verify actual decoded color gaps and choose the levels before seeing new model
results. Report accuracy against separation for each axis and model, with
position effects visible separately.

This directly addresses the observed confound and produces a more informative
measure of color discrimination. It is the proposed next experiment, not an
already implemented or measured second release. Human agreement remains a
separate unmeasured limitation of the current pilot.
