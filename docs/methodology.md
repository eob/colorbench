# ColorBench 0.2.0 methodology

This first pilot measures responses to controlled rendered color tasks through
providers' image-input interfaces. It does not isolate visual processing from
instruction following, image preprocessing, or coordinate-system knowledge.
It asks about visible properties, not aesthetic quality, semantic intent,
accessibility compliance, or which color a designer should choose.

## Stimuli and references

There are 72 questions: eight each for matching, lightness, chroma, hue,
color-to-component binding, gradient matching, RGB, HSL, and OKLCH. The three
numeric families reuse the same eight opaque colors, yielding 56 unique PNGs.
Each request starts independently; other predictions are never supplied.

Images are 800 × 640 device pixels at DPR 1 on an sRGB neutral background
`rgb(238,238,238)`. Flat color fields are written as exact RGB canvas pixels.
The renderer forces Chromium's sRGB profile and records browser version,
viewport, custom font identity, font file hash, and image hashes. DejaVu Sans
at 16 px supplies readable neutral labels. An independent Pillow decoder checks
all scored regions against their recorded RGB values and pixel hashes.

Matching and binding share colors, target geometry, option fill dimensions,
and option positions. Binding adds neutral component frames. Their difference
is a controlled transfer to this UI treatment; it does not isolate every
possible source of object-binding difficulty.

Lightness and chroma prompts balance both answer positions and question
directions (lighter/darker, more/less). Visible reference ramps illustrate the
requested dimension. Comparisons use decoded OKLCH coordinates and verify
that the intended ordering survives 8-bit sRGB conversion. Hue questions use
chromatic targets and a unique closest coordinate-defined hue, with half the
questions varying lightness and chroma. Human hue-equivalence judgments remain
unmeasured; coordinate equality is a construction rule, not a perceptual proof.

Gradient targets and choices have equal dimensions. Exactly one choice repeats
the target's complete decoded field. Distractors reverse or cyclically shift
its columns, preserving the color histogram. The task therefore requires
spatial color progression rather than merely detecting the available colors.
It does not ask for invisible CSS syntax or stop counts.

Numeric targets are seven chromatic colors and one neutral gray. They have no
labeled color calibration chart. Each format uses exactly the same image bytes,
including prompt-neutral image text. The external prompt names the requested
coordinate system and units. Ground truth is the decoded opaque interior RGB
triplet; reference HSL and OKLCH coordinates are derived from that common truth.

The pilot uses procedural, controlled sRGB colors. Tailwind remains a possible
versioned palette source for a larger corpus, not a hidden classifier or a
claim that adjacent class tokens have equal perceptual spacing. This pilot
does not score Tailwind color names.

## Answers and scoring

Each image has one question. Choice answers contain exactly `{"choice":"A"}`
with an available option letter. Case and surrounding letter whitespace are
normalized. Four-choice families have a 25% chance baseline; lightness and
chroma have a 50% baseline. Balanced ground truth makes a constant-letter
predictor attain those same accuracies over the complete pilot family.

Numeric response contracts are:

- RGB: integer `r`, `g`, `b` in 0–255, gamma-encoded sRGB.
- HSL: numeric `h` in degrees; `s` and `l` in 0–100 percent.
- OKLCH: numeric `l` in 0–1; nonnegative `c` in OKLCH units; `h` in degrees.

Hue is normalized modulo 360. Chroma is not treated as a percentage or clipped
to an invented upper bound. Booleans, strings, extra fields, duplicate keys,
nonfinite coordinates, and incompatible family schemas are rejected. Markdown
fences and prose are not stripped to rescue malformed output.

All valid numeric responses are converted to OKLab. Error is the Euclidean
OKLab distance from the target, written ΔE_OK. OKLCH predictions outside the
sRGB gamut remain unclipped when scored and are flagged separately. This avoids
crediting a different, gamut-clipped color. RGB and HSL inputs already have
bounded sRGB domains.

For a bounded descriptive chart, numeric similarity is
`100 × (1 − min(ΔE_OK / 0.2, 1))`. The 0.2 cap is an engineering normalization,
not a human detection threshold. Invalid responses receive zero similarity.
Report validity with similarity and raw error statistics; conditional error
among valid predictions alone could reward a model that frequently fails to
answer. Choice accuracy likewise counts invalid answers as incorrect.

Component errors remain in each format's units. Hue error takes the shorter
circular distance and is reported only when the target has OKLCH chroma at
least 0.02. This cutoff is a declared diagnostic convention. HSL saturation
error is undefined at exact target black/white. The reconstruction error still
applies. Achromatic reference colors use zero chroma and canonical zero hue.

A numeric control always predicts decoded sRGB `[128,128,128]`, expressed in
each requested space. It was selected before the first paid run and obtains
about 30.56 similarity on these eight targets (mean ΔE_OK about 0.16204).
The tiny OKLCH round-trip difference is matrix precision, not a distinct
predictor. Exact predictions and metrics are saved in
`tickets/evidence/constant-gray-baseline.json`. This is an image-independent
reference, not a trained or optimized baseline.

There is no pooled ranking across choice accuracy and numeric similarity.
Results describe eight fixed questions per family and do not warrant fine
model distinctions. Formats sharing a target and matching/binding pairs are
correlated observations. No independent-item confidence intervals or claims of
human calibration are made for this first pilot.

## Execution and publication integrity

A release descriptor identifies a committed dataset, its fingerprint, its
expected task count, and the evaluation protocol fingerprint. Release loading
verifies those identities and the decoded-pixel dataset gate before creating
provider clients. A changed prompt, grading implementation, schema, or image
cannot silently resume a frozen run under its old identity.

The model catalog matches FontBench and BorderBench's 13 enabled models. A
read-only availability check was made on 2026-09-13; evidence and price sources
are in `tickets/evidence/model-readiness-2026-09-13.json`. Cost is estimated from
recorded provider token usage and catalog prices. Meta's inherited price was
not independently reverified from its JavaScript-only documentation page at
that check. Missing usage is never replaced by invented token counts.

A SQLite ledger records each attempt, usage, errors, request identity, and
budget reservation. Infrastructure errors and incomplete coverage remain
separate from scored invalid model responses. Retries are not a way to choose
better semantic answers. Finalization replays raw predictions with the frozen
grader, verifies the common cohort and recorded artifacts, and seals output.
The website importer consumes a verified explicit run; it does not choose the
latest file by modification time or trust cached correctness flags.

## Sources

Color definitions and conversion conventions follow
[CSS Color 4, 8 September 2026 draft](https://www.w3.org/TR/2026/CRD-css-color-4-20260908/).
OKLab conversion uses the author's
[2021-01-25 updated matrices](https://bottosson.github.io/posts/oklab/), with
independent primary-color anchors, round trips, gray handling, and sRGB transfer
boundary tests. OKLab distance is a useful common reconstruction metric, not a
complete model of human color differences; CSS Color 4 §20.4 notes its unequal
sensitivity to colorfulness and lightness differences.
