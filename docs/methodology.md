# ColorBench 0.4.0 methodology

ColorBench measures how vision-language models answer direct color questions
through their providers' image interfaces. Performance includes instruction
following, image preprocessing, and coordinate knowledge. It does not isolate
a human visual mechanism or assess aesthetic judgment.

**All thirteen configurations completed the 0.4.0 cohort on September 16,
2026.** The [measured report](../results/fourth-pilot.md) accompanies this
description of the corpus and reporting protocol. The [0.3.2 report](../results/third-pilot.md)
remains a historical measurement of different inputs and instructions. The
[repair notes](direct-color-repairs-0.4.0.md) explain why the construction changed.

## Corpus and construction

The corpus has **512 questions and 456 unique 800 × 640 PNGs**:

| Family | Questions | Construction |
| --- | ---: | --- |
| Matching | 48 | Three color axes × four separations × four reference choices |
| Component fill matching | 48 | Matching colors and choices inside neutral component frames |
| Lightness | 64 | Four five-color chains × four adjacent pairs × two directions × two placements |
| Chroma | 64 | Four five-color chains × four adjacent pairs × two directions × two placements |
| Hue | 32 | Four separations × fixed/varying lightness and chroma × four reference choices |
| Gradient | 16 | Four option fields × four reference choices |
| Same–different | 48 | Six endpoint pairs × four pairings × two answer mappings |
| Context | 80 | Four option fields × five surround conditions × four references |
| Small-region | 64 | Four option fields × four geometry conditions × four references |
| RGB, HSL, OKLCH | 16 each | Independent requests over the same sixteen target images |

Every four-choice option field appears with all four references. Within each
construction cell, the external prompt and every pixel outside reference R
remain identical. The independent gate decodes each image, masks R, and
requires the remaining input to occur with every correct answer once. A
predictor using only that remaining input therefore has 25% expected accuracy
on the complete cell. The check includes labels, surrounds, and all other
visible pixels, not just sampled option colors.

Matching and component-fill tasks share colors, option positions, and scored
region geometry; the latter adds neutral component frames. Matching uses
intended lightness gaps of 0.08, 0.04, 0.02, and 0.01; chroma gaps of 0.025,
0.012, 0.007, and 0.004; and hue gaps of 35°, 15°, 8°, and 4°. Quantization
changes the exact decoded coordinates, which are checked within declared
tolerances. These values do not represent measured human detection thresholds.

### Lightness and chroma comparisons

Each family uses four chains of five ordered colors at different absolute
ranges. Adjacent colors are compared in both A/B placements and under both
requested directions: lighter/darker or more/less colorful. Interior colors
therefore occur as both the lower and the higher member of a pair. Gap sizes
rotate through chain positions. Intended lightness gaps are 0.10, 0.05, 0.02,
and 0.01; chroma gaps are 0.06, 0.03, 0.015, and 0.008.

Masking either compared patch leaves an optimal lookup accuracy of **62.5%**
within each chain and prompt. This removes the old perfect single-patch rule
but does not remove all absolute-color information: the finite chain's two
endpoints still reveal an ordering constraint. The decoded gate measures the
ceiling using the entire remaining image and prompt. Separation slices remain
descriptive; these few overlapping chains do not establish a psychometric
curve or a calibrated sensitivity threshold.

### Hue matching

Hue uses minimum distractor separations of 70°, 30°, 12°, and 6°. The fixed
lightness/chroma condition allows exact color matching because R and the
winning option share their complete color. In the varying condition, option
lightness and chroma differ while R has fixed lightness and chroma. Results
must keep these two conditions separate.

The renderer derives R's intended hue from decoded option coordinates, and
the gate verifies a unique nearest hue after quantization. Human judgments of
hue equivalence have not been measured; coordinate agreement alone does not
prove perceptual agreement.

### Gradient matching

Each of four palettes produces four fields with identical endpoints and
color histograms. Two independent interior block swaps change their spatial
arrangement. Every full field is used as R once. The gate checks one unique
full-field match, shared endpoints, equal histograms, and that no single
column identifies an option uniquely.

Two palettes also make the option fields identical under Pillow's 8-bit
`L` grayscale conversion. This is specific to that integer transform; it does
not establish equal linear-sRGB luminance, Oklab lightness, or perceived
brightness. Other fields retain structure under the same grayscale transform.
These are small, controlled
permutations; they do not test reconstruction of arbitrary gradients or CSS
syntax. Discontinuities between blocks are part of the visible field to match.

### Same–different judgments

Each endpoint pair `(c,d)` produces `(c,c)`, `(c,d)`, `(d,c)`, and `(d,d)`.
Every image is queried with both mappings between answer letters and the
semantic responses "same" and "different". Thus 48 questions use 24 images.
The mapping appears in the external prompt, not in the image.

For either patch alone, the full remaining image and prompt have identical
color distributions across same and different outcomes. An optimal lookup
rule therefore scores **50%** when the other patch is masked. Six endpoint
pairs vary base colors and lightness, chroma, or hue differences.

Reports retain same-pair and different-pair accuracy, semantic response
counts, and consistency across the two mappings of an identical image.
Consistency is not correctness: a model can give the same wrong semantic
answer under both mappings. Binary outcomes describe response tendencies;
these few heterogeneous cases do not establish stable decision criteria or
perceptual thresholds.

### Surround and geometry interventions

Context repeats each target and option field on neutral surrounds and four
cyclic assignments of the colored surrounds. R remains on the neutral
background. Colors, positions, labels, and wording stay fixed; only the
surround pixels change. Each neutral-versus-colored comparison contains
16 paired questions per model. This tests those particular surround changes,
not general human color constancy.

Small-region tasks repeat the same fields as 20px and 84px filled squares,
and as 84px outlines with 3px and 12px strokes. Region centers, labels,
references, option positions, colors, and wording remain fixed within each
comparison. Both external and visible instructions include colored outlines
and exclude labels and neutral areas. Reports compare filled-square sizes
separately from outline widths, with 16 pairs per model in each comparison.
They do not treat a filled-versus-outline difference as an isolated size effect.

### Dependence and controls

`groupId` identifies matched requests, while `design.optionSetId` identifies
an option field repeated across references. Intervention conditions and
same–different mapping pairs have explicit metadata. Four references share
one field; interventions share colors; two mappings share an image; and
numeric formats share a target. Question counts are not counts of independent
new colors.

Masking, endpoint, histogram, and grayscale checks are construction oracles
with known region locations. They do not show that a model used a shortcut,
and they are not model experiments on transformed images. Human agreement
and model responses to such transformations remain unmeasured.

## Rendering and independent ground truth

The renderer writes opaque sRGB canvas pixels on neutral `rgb(238,238,238)`
backgrounds. Chromium uses a forced sRGB profile at device pixel ratio 1.
The manifest records browser version, viewport, font file hash, actual glyph
font evidence, image hashes, and scored-region hashes. Neutral labels use
bundled DejaVu Sans at 16px.

Pillow independently decodes PNGs to check actual target colors, region
geometry, unique answers, ordering, gradient fields, and the construction
controls. The gate rejects embedded profiles, transfer overrides, text
metadata, and nonopaque images. Ground truth comes from decoded pixels;
HSL and OKLCH reference coordinates derive from the same RGB target.

Requests contain the PNG bytes and frozen prompt, without filenames, task
IDs, manifests, previous answers, or ground truth. The client does not resize
or re-encode the PNG. Provider-side decoding, resizing, and visual tokenization
remain unobserved parts of the measurement; matching source pixels do not
establish identical internal representations across providers.

Numeric targets comprise thirteen chromatic colors, one neutral gray, and
two near-neutral extremes. RGB, HSL, and OKLCH use the same sixteen PNG byte
strings in fresh, format-specific requests. Images contain no numeric
calibration chart, color name, or requested-format cue.

## Answers and scoring

Choice answers contain exactly `{"choice":"A"}` with an available letter.
Letter case and surrounding whitespace are normalized. Four-choice families
have 25% chance accuracy; lightness, chroma, and same–different have 50%.
Balanced labels give constant-letter predictors those same rates. Invalid
answers count as incorrect.

RGB requires integer channels from 0 to 255. HSL uses hue in degrees and
saturation/lightness in percent. OKLCH uses lightness from 0 to 1, nonnegative
chroma in OKLCH units, and hue in degrees. Hue is normalized modulo 360;
chroma is not clipped to an invented maximum. Extra fields, duplicate keys,
booleans, numeric strings, nonfinite coordinates, Markdown fences, and
explanatory prose are rejected. Providers receive the same supported schema
subset; numerical bounds are stated in prompts and checked locally.

Valid numeric answers convert to Oklab. Reconstruction error ΔE_OK is their
Euclidean distance from the decoded target. Out-of-sRGB OKLCH predictions
remain unclipped and receive a separate gamut flag. Similarity is
`100 × (1 − min(ΔE_OK / 0.2, 1))`; tight similarity uses a 0.05 cap. Both
assign zero to invalid answers. These are engineering scales, not accuracy
percentages or calibrated human visibility thresholds.

Raw error means, medians, and 90th percentiles use valid responses. So do
hit rates at ΔE_OK ≤ 0.005, 0.01, 0.02, and 0.05. Similarity means include
all scored answers. RGB additionally reports exact-channel recovery and
counts within ±2 and ±5 channel steps on every channel, retaining total,
valid, and invalid response counts. A high similarity can coexist with
inexact channel values; both measures should remain visible.

Component errors retain the requested format's units. Circular hue error is
reported only for targets with Oklch chroma ≥0.02: thirteen of the sixteen
numeric targets. The exact gray and two near-neutral extremes still receive
full reconstruction grades, but not a hue diagnostic. HSL saturation error
is undefined for exact black/white targets. These are declared conventions;
the chroma cutoff is not a human visibility threshold.

An image-independent control always returns sRGB `[128,128,128]`, expressed
in the requested format. It scores about 18.11 similarity on the sixteen
targets. Their image bytes are unchanged from 0.3.0 through 0.4.0, so the
[archived control](../tickets/evidence/constant-gray-baseline-0.3.0.json) remains
applicable. It was chosen before paid results and is not an optimized estimator.

The analysis exports per-model and pooled paired correctness tables for
surrounds and geometry, mapping consistency among pairs with two valid
answers, separate hue contexts, and numeric diagnostics. Paired correctness
includes invalids as incorrect; missing partners are counted explicitly.
There is no combined model score or independent-item confidence interval.
This finite, designed corpus is not a random sample of real interfaces.

## Execution, provenance, and publication

A release descriptor pins the committed dataset, image-content fingerprint,
expected count, and protocol fingerprint. Those identities and decoded pixels
are validated before provider clients are created. The renderer writes only
a replaceable candidate path. Grading version `2` and numeric scoring remain
unchanged in 0.4.0, but revised prompts require a new protocol fingerprint and
fresh observations.

The full campaign covers all 512 questions for thirteen configured models:
6,656 final responses, including any invalid answers. The documented example
uses concurrency six and a $65 accounting cap, without a task limit. A SQLite
ledger retains attempts, token usage, costs, and resume identity. Invalid
answers are not retried to select better answers. Infrastructure failures
remain retryable; one runner attempt can contain internal HTTP retries.
A paused invocation can exit zero, so completion requires checking the run
summary and each model's full coverage.

Budget reservations include estimated input, maximum output, and retry
headroom. Unmetered requests may leave conservative allowances in ledger
spending. Published mean API-response costs require complete metering and
archived prices; otherwise the mean is null. Catalog-price estimates and
reserve allowances are distinct from provider invoices.

After completed source artifacts are committed, finalization reparses raw
answers, recomputes grades, reconciles the SQLite ledger and exports, verifies
the shared cohort, and seals the result. Publication names an explicit verified
run. A separate audit recomputes numeric equations and choice counts and
reports request/retry accounting. Existing datasets, descriptors, sealed run
directories, and JSON publication snapshots remain frozen.

Historical 0.3.2 verification uses compatible source
`8fc558433146066b8e1ed9b44303689b2433478d`; see the
[replay instructions](../releases/README.md#historical-replay). New source
intentionally rejects old protocol fingerprints. Historical scores must not
be relabeled as 0.4.0 observations or compared as evidence of model progress.

Models retain their configured provider defaults and different output limits.
No equal-compute, reasoning-effort, or repeated-run experiment is claimed.
The [2026-09-13 availability record](../tickets/evidence/model-readiness-2026-09-13.json)
is historical; Meta's inherited catalog price was not independently reverified
at that check. Provider preprocessing, coordinate knowledge, response strategy,
and stochastic variation all limit causal interpretations of model differences.

## References

Conversions follow [CSS Color 4](https://www.w3.org/TR/2026/CRD-css-color-4-20260908/)
and [Ottosson's Oklab matrices](https://bottosson.github.io/posts/oklab/).
Tests cover independent primary-color anchors, gray handling, transfer-function
boundaries, hue wrapping, and round trips. Euclidean Oklab distance is a useful
reconstruction measure, not a complete model of human color discrimination.
