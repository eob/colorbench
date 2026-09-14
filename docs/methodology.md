# ColorBench 0.3.2 methodology

ColorBench measures how vision-language models answer controlled color tasks
through their providers' image interfaces. It includes instruction following,
image preprocessing, and color-coordinate knowledge; it does not isolate a
human-like visual mechanism or assess aesthetic judgment.

## Corpus and construction

The fixed pilot has **264 questions and 232 unique 800 × 640 PNGs**:

| Family | Questions | Construction |
| --- | ---: | --- |
| Matching | 48 | Three color axes × four separations × four reference choices |
| Component fill matching | 48 | Same targets and options as matching, with neutral UI frames |
| Lightness | 16 | Four separations × two directions × two answer positions |
| Chroma | 16 | Four separations × two directions × two answer positions |
| Hue | 32 | Four separations × fixed/varying lightness and chroma × four reference choices |
| Gradient | 8 | Two option fields × four reference choices |
| Same–different | 16 | Eight identical and eight differing pairs, answer mapping crossed |
| Context | 16 | Four option fields on fixed per-position surrounds × four references |
| Small-region | 16 | Two dot fields and two outline fields × four references |
| RGB, HSL, OKLCH | 16 each | Three formats independently estimate the same sixteen target images |

Every four-choice option set is repeated with all four references. The full
image outside the reference R, and the external prompt, remain byte-for-byte
identical within that set. The independent dataset gate decodes each PNG,
masks only the reference rectangle, and requires each identical visible input
to have A, B, C, and D as its correct answer once. Thus any deterministic
predictor deprived of R scores exactly 25% on these complete cells; a
stochastic predictor using only those inputs has expected accuracy 25%.
The control includes labels, surrounds, and every pixel outside R, not just
sampled option colors.

This construction removes the reference-free option-order shortcut discovered
in 0.3.1. That historical corpus placed ordered distractors around a target
restricted to middle ranks; a solver ignoring R reached approximately 74–75%
on four families. Release 0.3.2 uses all four target ranks and counterbalances
rank against answer position in matching, binding, context, and small-region
families. Scoring semantics are unchanged, but the corpus changed, so scores
must not be compared across releases.

Matching and binding use equally spaced option coordinates. Lightness gaps
are 0.08, 0.04, 0.02, and 0.01; chroma gaps are 0.025, 0.012, 0.007, and
0.004; hue gaps are 35°, 15°, 8°, and 4°. Lightness comparisons use 0.10,
0.05, 0.02, and 0.01; chroma comparisons use 0.06, 0.03, 0.015, and 0.008.
Hue matching uses minimum distractor separations 70°, 30°, 12°, and 6°.
These are intended coordinate gaps, verified after 8-bit sRGB quantization
within declared tolerances. The [decoded gap ranges](../tickets/evidence/decoded-gaps-0.3.2.json)
record the actual nearest-option separations. For example, matching chroma
0.007 yields gaps from 0.00445 to 0.00745; nominal steps are not exact decoded
coordinates. They are not measured human detection thresholds.

Each matching/binding pair shares target color, geometry, option fills, and
option positions; binding adds neutral component frames. Their difference
measures transfer to this particular treatment. The four references sharing
an option field are correlated stimuli as well. `groupId` identifies the
matched image pair or numeric-format group; `design.optionSetId` additionally
identifies the four-reference construction cell, shared by matching and
binding. Neither identifier reaches a model.

Hue references use decoded option hue to create R. In the varying condition,
option lightness and chroma differ while R retains fixed lightness and chroma.
The decoded winning hue is unique, with the nearest distractor at the declared
gap within tolerance. Human hue-equivalence judgments have not been measured;
coordinate equality is a construction rule, not perceptual proof.

Gradient options are a forward progression, its reversal, and two cyclic
column shifts. All preserve the color histogram, and each complete field is
used as R once. Some reference strips therefore contain a visible transition
at the cyclic wrap. The question asks for exact visible progression; it does
not infer CSS syntax, stop counts, or aesthetic smoothness.

Same–different images contain two patches and no R. The mapping of answer
letters to "same" and "different" appears only in the external prompt and is
crossed with trial type. Different pairs vary along lightness, chroma, or hue.
Same-pair and different-pair outcomes must be reported separately: aggregate
accuracy can conceal a tendency to say "same". Binary hit and false-alarm
rates already describe that tendency; confidence ratings are optional richer
data, not a prerequisite for reporting it. These small heterogeneous samples
do not establish stable sensitivity, decision criteria, or thresholds.

Context option interiors sit inside four fixed surrounds. R remains neutral,
and the ground truth is interior equality. Small-region choices use 20px
squares (the renderer's "dot" layout) or 3px colored outlines. Dot and outline
cells also differ in hue and swept axis: their score difference does not
isolate geometry. Similarly, base colors vary across separation levels, so
separation slices are descriptive and do not estimate psychometric functions.

## Rendering and independent ground truth

The renderer writes opaque sRGB canvas pixels on neutral `rgb(238,238,238)`
backgrounds. Chromium uses a forced sRGB profile at device pixel ratio 1.
The manifest records browser version, viewport, font file hash, actual glyph
font evidence, image hash, and scored-region hashes. Bundled DejaVu Sans
renders neutral labels at 16px. Human-readable screenshots were visually
reviewed alongside automated checks.

Pillow independently decodes all PNGs. The gate checks exact RGB values,
unique answers, histogram equality for gradients, hue ordering, comparison
gaps, prompt identity, neutral pixels, color-profile absence, and pairing.
Ground truth comes from the decoded image rather than invisible CSS labels.
Numeric targets are opaque flat RGB interiors; HSL and OKLCH reference
coordinates derive from that same decoded RGB.

Every model request starts independently. Providers receive only image bytes
and the frozen family prompt. Task IDs, filenames, option-set IDs, manifests,
and previous answers are not supplied. Native provider tests pin this boundary.
Public task IDs contain family and position information for bookkeeping, so
external redistribution should rename files before passing them to a model.

The numeric targets are thirteen chromatic colors, one neutral gray, and two
near-neutral extremes. The same sixteen image byte strings are reused across
RGB, HSL, and OKLCH requests. Images contain no numeric calibration chart,
color names, or requested-format cue. They are procedural sRGB colors, not
Tailwind token labels.

## Answer contracts and scoring

Choice answers contain exactly `{"choice":"A"}` with an available option.
Case and surrounding letter whitespace are normalized. Four-choice families
have 25% chance accuracy; lightness, chroma, and same–different have 50%.
Balanced answer labels make a constant-letter predictor attain those same
accuracies over a complete family. Invalid answers count as incorrect.

Numeric contracts are RGB integers in 0–255; HSL hue in degrees with saturation
and lightness in 0–100 percent; and OKLCH lightness in 0–1, nonnegative chroma
in OKLCH units, and hue in degrees. Hue is normalized modulo 360. Chroma is
neither a percentage nor clipped to an invented upper bound. Booleans, strings,
extra fields, duplicate keys, nonfinite values, incompatible keys, Markdown
fences, and explanatory prose are rejected.

Every provider receives the same family-specific structured output schema.
Bounds are stated in the prompt and enforced locally. They are omitted from
the common wire schema to remain within the providers' supported subset.

Valid numeric answers convert to OKLab. Reconstruction error ΔE_OK is the
Euclidean distance from the decoded target. Out-of-sRGB OKLCH predictions are
scored without clipping and flagged separately; clipping would change the
predicted color. RGB and HSL inputs already have bounded sRGB domains.

The descriptive similarity is `100 × (1 − min(ΔE_OK / 0.2, 1))`; tight
similarity uses a 0.05 cap. Invalid answers receive zero for both. These are
engineering normalizations, not perceptual thresholds. Raw error means,
medians, and 90th percentiles are conditional on valid answers; validity must
accompany them. Similarity means include invalid answers in their denominator.

Near-exact hit rates at ΔE_OK ≤ 0.005, 0.01, 0.02, and 0.05 use valid-answer
denominators. RGB also reports the share of valid responses within ±2 and ±5
8-bit channel steps on all channels. Component errors retain each format's
units. Circular hue error is reported only for targets with OKLCH chroma ≥0.02;
HSL saturation error is undefined for exact black and white. These are declared
diagnostic conventions. Achromatic reference hue is canonically zero.

A fixed image-independent control always predicts decoded sRGB `[128,128,128]`,
expressed in each requested format. It scores approximately 18.11 similarity
on the sixteen targets. Numeric image bytes are unchanged across 0.3.0,
0.3.1, and 0.3.2, so the archived
[control evidence](../tickets/evidence/constant-gray-baseline-0.3.0.json)
remains applicable. This control was chosen before paid results; it is not an
optimized estimator.

There is no combined score or pooled model ranking across the twelve families.
No independent-item confidence intervals are reported. Models share the same
stimuli, formats share numeric targets, and references share option fields.
The small, designed corpus describes these observations rather than a random
sample of color perception in real interfaces.

## Execution, provenance, and publication

A release descriptor pins the committed dataset, image-content fingerprint,
expected count, and evaluation protocol fingerprint. Loading validates those
identities and decoded pixels before creating provider clients. The renderer
writes only a replaceable candidate path; it cannot overwrite registered or
historical releases. The current release retains grading version `2` and the
same protocol fingerprint as 0.3.1 because prompts, parsing, conversion, request
construction, and grading semantics are unchanged.

A SQLite ledger tracks attempts, token usage, costs, and resume identity. One
runner attempt can contain an internal retry; its `request_attempts` and
`unmetered_attempts` fields must be inspected before making request-count or
cost-completeness claims. Invalid model answers are scored observations, never
retried to select better answers. Infrastructure failures remain separate.
The runner reserves conservative budget before dispatch; an unmetered request
can leave a reserve allowance in the ledger spending total.

Finalization replays every raw answer against the frozen grader, verifies the
shared cohort and source artifacts, and seals the result. The publication
export uses an explicit verified run, not a timestamp-selected latest file.
An additional audit independently recomputes numeric equations and choice
counts, checks full-image reference controls, and separates metered token-price
estimates from unmetered retry reserves.

Model IDs, catalog prices, provider endpoints, output limits, and run-time Git
identity are archived. Prices are catalog estimates rather than provider
invoices. The 2026-09-13 availability record is in
[tickets/evidence/model-readiness-2026-09-13.json](../tickets/evidence/model-readiness-2026-09-13.json);
Meta's inherited price was not independently reverified from its documentation
at that check. Provider image preprocessing and stochastic response variability
remain part of the measurement. Human agreement has not been measured.

## References

Conversions follow [CSS Color 4](https://www.w3.org/TR/2026/CRD-css-color-4-20260908/)
and [Ottosson's updated OKLab matrices](https://bottosson.github.io/posts/oklab/).
Tests cover independent primary-color anchors, gray handling, transfer-function
boundaries, hue wrapping, and round trips. OKLab Euclidean distance is a common
reconstruction metric, not a complete model of human color discrimination.
