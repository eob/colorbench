# plan-01: ColorBench perception design

- **Status:** In Review
- **Date:** 2026-09-13
- **Assignee:** Edward Benson
- **Branch:** `valid-01-perceptual-pilot`
- **Harness / machine:** Codex / eob-dev2; session ID not exposed
- **PR:** https://github.com/eob/colorbench/pull/1
- **Scope:** Implement, measure, critique, and publish the first perception pilot

## Purpose and suite boundary

The design quartet measures recognition of observable visual properties:
FontBench covers typography; BorderBench covers strokes, corners, and shadows;
LayoutBench covers spatial arrangement; ColorBench covers color and its spatial
distribution. ColorBench should ask whether a model can distinguish, compare,
and locate colors in a rendered image. Aesthetics, semantic intent, and advice
about what a designer should choose are outside this scope.

The intended inference is performance on defined visual tasks through a model's
image-input interface. Short instructions reduce language demands. Numeric
color estimation additionally measures how a model expresses a perceived color
in a named coordinate system; report it separately from reference matching.
Neither task isolates an internal perceptual faculty from instruction-following
and provider preprocessing.

The accepted next step is to implement and publish a first measured pilot. This
plan does not establish perceptual thresholds or human calibration. The
principal hypotheses to test are that visible
references reduce vocabulary dependence, controlled distractors reveal useful
difficulty curves, and color-to-object tasks expose errors absent in isolated
swatches. Failure of those controls should change the question design.

## Inspected baseline

Read-only source inspection on 2026-09-13:

| Repository | Commit | Relevant evidence |
| --- | --- | --- |
| ColorBench | `8c2cd592576e76c5acbd01f2e21c52d040b628bb` | `src/specimens.ts:13`, `src/render.ts:82`, `baseline/evaluator.py:30` |
| BorderBench | `07ee6830be9ceb4a242c1edd78cb46321fe5c292` | `docs/methodology.md`, `baseline/runner.py`, `baseline/finalize.py`, `releases/FINALIZATION.md` |
| FontBench | `14b09c3ad89e5b587c19abee5b66978968252f85` | `README.md`, `baseline/runner.py`, `baseline/releases.py` |

ColorBench already has a 100-image prototype and TypeScript/Python scaffolding.
Its scored semantic roles, surface roles, and WCAG tiers do not implement this
perception scope. More seriously, `src/render.ts:93` prints the semantic answer
and line 94 prints the contrast-tier answer in each image. Theme is also printed.
Those images cannot establish color recognition independently of reading the
answers. Preserve this prototype as history; do not carry its scores into V1.

Use BorderBench's repaired release and execution machinery as the implementation
reference, with FontBench as a cross-check. Reusing the early ColorBench runner
without that reconciliation would also preserve its validity gaps.

Specific migration requirements are already visible in the prototype:
`baseline/runner.py:84` selects a sorted prefix of hand-grouped tasks;
`baseline/evaluator.py:189` divides accuracy by expected corpus size when
provided, mixing missing coverage with observed correctness;
`baseline/providers.py:214` uses ordinary JSON parsing without duplicate-key
rejection; and `baseline/export_structured.py:39` selects by filesystem
modification time while line 58 estimates cost from assumed 600/60 token counts.
Replace these paths with verified cohort selection, separate coverage,
strict parsing, provenance, and recorded usage before producing scored data.

## Proposed question bank

One image contains the target and any specified visual reference, with one scored question.
Option identifiers are neutral letters or numbers placed outside colored areas.
Examples below specify the operation; final prompt text must be frozen after
the pilot. Each family has its own answer schema. Discrete families have chance
baselines; continuous estimation requires declared baseline predictors instead.

| Priority / family | Example question | Construction and ground truth |
| --- | --- | --- |
| Core: reference matching | “Which swatch, A–D, matches the color of R?” | Exactly one candidate duplicates R's decoded interior pixels. Equal shape, size, and surround. Distractors differ in controlled ways. Four choices; chance 25%. |
| Core: lightness comparison | “Which patch is lighter, A or B?” | Begin with neutral grays, then fixed-hue, controlled-chroma colors. Record final color-space coordinates and human agreement. Balance both answer positions and lighter/darker question direction. Two choices; chance 50%. |
| Core: chroma comparison | “Which patch is more colorful, using the gray-to-color example above?” | Supply a small visual explanation of the dimension. Hold intended hue and lightness fixed; vary chroma. Validate converted pixels and residual coordinate differences. Two choices; chance 50%. |
| Exploratory pilot: hue matching | “Which option has R's hue, even though its lightness or colorfulness may differ?” | Begin with fixed lightness/chroma. Then vary both independently across correct and incorrect options. Exclude near-achromatic cases. Coordinate-defined hue requires human validation before claiming perceptual equivalence. Four choices; chance 25%. |
| Core: color-to-object binding | “Which numbered component has the same fill color as R?” | Exactly one matching interior fill among four neutrally labeled UI components. Distinguish fill from text and outline. Pair with a swatch-only version containing the same colors, matching fill area and positions where practical. Report transfer to UI placement; isolating binding from size/shape effects requires further controls. Four choices; chance 25%. |
| Exploratory pilot: gradient matching | “Which reference strip has the same left-to-right color progression as the target?” | Exactly one option reproduces the target's full decoded color field at equal dimensions. Include a controlled subset of reversed gradients with the same color distribution; other distractors can change transition positions and therefore distributions. Control geometry and interpolation. Do not ask for invisible CSS stop counts or syntax. Four choices; chance 25%. |
| Numeric: RGB estimation | “Estimate the target's sRGB color as red, green, and blue values from 0 to 255.” | Return integer `{r,g,b}`. Ground truth is the decoded flat interior's gamma-encoded 8-bit sRGB triplet. |
| Numeric: HSL estimation | “Estimate the target's HSL color: hue in degrees, saturation and lightness in percent.” | Return numeric `{h,s,l}`. HSL is the working interpretation of HSK; derive reference coordinates from the same decoded sRGB target. |
| Numeric: OKLCH estimation | “Estimate the target's OKLCH color: lightness from 0 to 1, chroma as a number, and hue in degrees.” | Return numeric `{l,c,h}`. Chroma is nonnegative and is not a percentage or universally bounded by 1. Reference coordinates derive from decoded sRGB. |

Matching already measures discrimination when distractors get closer. Report
its hue/lightness/chroma manipulations and difficulty levels as slices, rather
than counting “matching” and “discrimination” as independent headline skills.
An odd-one-out task can be a diagnostic alternative if matching saturates.

Lightness and chroma ordering of three patches can extend the pair tasks later;
keep the harder response contract separate. Color arrangement with identical
palettes and geometry is another extension, but it overlaps spatial perception
and should not displace the basic color experiments.

## References and fair quantization

For comparative tasks, use visible swatches and ramps with neutral option IDs. Attach
palette names to the result metadata and website. A default font can establish
geometric scale in BorderBench; color needs a displayed color reference. A gray
ramp supplies an axis example, not complete calibration of a provider's vision
pipeline or a human display.

Tailwind is a useful stimulus catalog. A proposed starting subset is
`red`, `orange`, `yellow`, `green`, `cyan`, `blue`, `violet`, `pink`, and `neutral`
at 200/500/800, with black/white controls. Pin **Tailwind 3.4.17** and vendor exact
sRGB values for continuity with BorderBench. This is a sampling proposal, not
a claim that these are universal color categories or equally separated steps.
The [versioned palette documentation](https://v3.tailwindcss.com/docs/customizing-colors)
provides the source values. Current Tailwind uses a different documented palette
representation; a version change must be explicit.

Add procedurally sampled colors for controlled comparisons and held-out color
regions. A Tailwind-only corpus would test a narrow set of familiar prototypes.
Do not ask for adjacent class names such as `blue-500` versus `blue-600` from
memory, and do not impose hidden nearest-token boundaries on arbitrary colors.
If a palette-matching extension uses off-anchor targets, define the matching
rule and minimum winning margin before accepting any item.

Use OKLCH as construction coordinates for lightness, chroma, and hue, then
verify the final 8-bit sRGB result. The [dated CSS Color 4 specification](https://www.w3.org/TR/2026/CRD-css-color-4-20260908/)
defines these spaces and powerless hue near the achromatic axis. Its section
20.4 also describes limitations of the original delta-E OK distance metric.
Consequently, coordinate separation is a stimulus descriptor, not a universal
just-noticeable-difference threshold. Equal numerical gaps must not be presented
as equally difficult without empirical calibration.

For each manipulation, propose several decreasing separations and publish the
accuracy curve. Determine useful separations with independent human review,
not by selecting items that make a favored model win. Preserve difficult or
ambiguous cases separately with their measured agreement instead of silently
calling every nonzero pixel difference obvious.

## Context and ambiguity

Start with opaque, flat colors on the same neutral surround. A context diagnostic
holds the target's interior pixels fixed while changing its surrounding colors.
Compare each model's answers against the matched neutral-context observation.
This measures sensitivity to context when identifying the rendered fill.

“Identical rendered color” and “identical appearance” are different targets.
Do not automatically mark human appearance judgments wrong using RGB equality.
Questions about what looks lighter under contrasting surrounds require a
separate human appearance experiment. Physical illumination, material color,
and spectra cannot be recovered uniquely from these flat screenshot stimuli.

Other exclusions from the initial core: success/danger/brand semantics,
warm/cool labels without a defined reference, harmony or attractiveness,
accessibility compliance, exact hex transcription, and recovery of hidden alpha
or blend mode. Different CSS constructions can produce the same final image.
For gradients, ask about the visible color field rather than its source recipe.

## Numeric color estimation protocol

Show an opaque flat target on a fixed neutral surround. Reuse exactly the same
target image bytes for RGB, HSL, and OKLCH questions, in separate fresh requests
with no earlier answer available. Keep the three observations in the same
stimulus group. Pin gamma-encoded sRGB/D65 conversions; do not grade against
pre-render coordinates that changed during conversion or quantization.

Grade closeness, rather than requiring exact coordinate transcription. Convert
each valid prediction to Oklab and report its raw Euclidean color distance from
the target. Do not clip out-of-sRGB OKLCH predictions before measuring distance;
flag their gamut status separately. Report per-channel errors in each format's
own units, mean/median/p90 color error among valid answers, and validity rate.

For a first-pilot bounded summary, predeclare
`100 * (1 - min(deltaE_OK / 0.2, 1))`, with invalid answers receiving zero.
The 0.2 cap is an engineering normalization, not a human visibility threshold.
Call it a similarity score, never exact-match accuracy. Report each format
separately and disclose error distributions so the cap cannot conceal large
misses. Fixed-color baselines use the same underlying color for all formats.

Normalize hue circularly: 359° versus 1° is a 2° difference. Use canonical hue
zero for achromatic ground truth, but omit hue-component error when target
OKLCH chroma is below 0.02; this is an explicit applicability cutoff, not an
empirical threshold. Eligibility depends on the target, so predicting gray
cannot evade a chromatic target's hue penalty. HSL saturation diagnostics also
omit exact black/white targets. Reconstructed-color error remains applicable.
Strict schemas reject wrong keys, strings in numeric fields, booleans, missing
values, non-finite numbers, out-of-range RGB/HSL lightness or saturation, and
negative OKLCH chroma. Hue accepts equivalent turns via normalization.

Numeric results combine visual estimation with coordinate-system knowledge.
Differences between formats do not establish a change in the model's underlying
vision. Conversion-only controls can help separate those effects in a later
iteration if the first measurements justify that next step.

## Construction and shortcut controls

- Pin browser/build, viewport/DPR, bundled font, CSS, conversion implementation,
  and PNG color handling. Render opaque sRGB PNGs. Save submitted image hashes,
  dimensions, and provider image-detail settings; internal provider resizing
  remains a stated limit.
- Save target/option interior masks, intended values, computed values, decoded
  pixel values, and actual post-conversion separations. Keep labels and
  antialiasing out of the color regions. Reject collapsed distinctions, clipped
  colors, duplicate choices, and multiple correct answers.
- Reject an entire controlled comparison block if a level is out of gamut,
  rather than clipping one option and introducing an unintended cue. Audit
  coverage after rejection so hue, difficulty, or answer position does not
  become predictable.
- Balance correct option locations, hue regions, separations, nuisance colors,
  layouts, and backgrounds within each task family. Keep all choices in view.
  Target/reference patches should have equal surroundings in the basic task.
- Audit grayscale controls for unintended lightness cues in hue/chroma tasks;
  fixed OKLCH coordinates alone do not prove isolation of perceptual dimensions.
  Use text-only controls for semantic leakage and shuffled-position variants
  for position bias. They are diagnostics, not extra independent samples.
- Cross object colors with neutral content and object positions. Compare binding
  items to isolated-color controls while recording residual area/shape effects;
  include gradient comparisons with equal color distributions to test whether
  a color-count shortcut explains performance.
- The model receives only the approved prompt and image, with no source CSS,
  manifest, answer-bearing filename, numeric color values, or pixel-reading tool.
  Pixel-based solvers are dataset validators, not comparable vision-model runs.

## Scoring and experimental units

Report each family separately, with its applicable baseline, sample count, error
rate, and difficulty breakdown. Hue regions and comparison direction need
balanced coverage. Do not average raw percentages across different response
spaces into an unexplained leaderboard score. Any later composite needs fixed,
published weights and a defined normalization before model evaluation.

Use short, strictly validated answers, for example `{"choice":"B"}` for
four-way matching. Distinguish response-format failures from perceptual errors
in diagnostics while counting invalid final model answers as incorrect.
Infrastructure failures remain missing observations with explicit coverage and
attempt costs; retries must not select a better substantive answer.

Related questions, permutations, contexts, and layouts share a base stimulus
group. Development/pilot/evaluation splits must keep each entire group together.
Select complete, balanced evaluation blocks before observing model scores, and
compare all models on the same frozen cohort. If confidence intervals are
reported, resample independently sampled base groups and state the population
they support; do not treat every rendering as an independent trial. A fixed
hand-authored demonstration set supports descriptive scores only.

## Repository structure and reuse

Retain the sibling layout; port the validated machinery deliberately rather
than carrying forward the ColorBench prototype's schema:

```text
src/          stimulus catalog, color construction, renderer, browser checks
baseline/     prompts, strict schemas, evaluator, providers, runner, validation
config/       versioned model catalogs and explicit inference settings
dataset/      isolated candidates and immutable accepted releases
releases/     code/dataset/protocol fingerprints and finalization instructions
results/runs/ release/run ledgers, raw attempts, usage, replayable exports
docs/         accepted methodology and dataset limitations
branding/     editable artwork and rendered assets
site/         generated results with shared-cohort comparisons
tests/        protocol, pixel validation, runner and release integrity checks
tickets/      design decisions, validity audits, implementation milestones
```

Reuse BorderBench's release identity, candidate protection, mandatory offline
validation before clients are created, resumable SQLite attempt ledger,
conservative budget reservations, shared-cohort reporting, independent grading
replay, and publication sealing. Adapt the renderer, ground truth, schemas,
group identifiers, validators, metrics, and website breakdowns for color tasks.
Copy the sibling model catalog only as a starting roster; verify availability
and prices when a campaign is actually scheduled.

## Proposed implementation sequence

1. **Question review:** Create a 72-question pilot, eight examples per family
   across six comparative and three numeric tasks. The three numeric formats
   reuse eight target images. This is a first design probe with descriptive
   scores, not a calibrated final V1 dataset.
2. **Validity-first renderer:** Replace leaking content and build pixel oracles,
   masks, gamut/uniqueness checks, and paired controls. Prove intended failure
   cases before implementing their validators. Preserve historical inputs.
3. **Pilot freeze:** Pin the nine families, source images, answer contracts,
   conversions, score definitions, 72-question cohort, and model settings before
   paid evaluation. Clearly identify hue and gradient cases as exploratory.
4. **Execution parity:** Port and verify the sibling pipeline, run offline and
   mock/resume/replay checks, then freeze the first pilot release.
5. **First measured campaign:** Run the predeclared shared cohort, independently
   replay grading, seal results, and publish at
   `edwardbenson.com/benchmarks/colorbench`. Include raw evidence, human-validation
   limits, family scores, numeric errors, and a critique. Propose one subsequent
   improvement for discussion; do not silently change the measured release.
6. **Later calibration:** A blinded human pilot remains an outstanding validity
   step. Use multiple independent observers on the exact images, recording
   display conditions, agreement, ambiguity, and reasons. Define inclusion rules
   beforehand. A proposed minimum of five observations per item is a pragmatic
   screen, not a population estimate. Any resulting changes require a new
   version and a fresh measured cohort.

The next concrete deliverable is the implemented, measured pilot. Remaining
empirical decisions are useful separation ranges, human agreement, the added
value of binding/gradient tasks, and final corpus coverage. The existing
prototype has not been repaired or evaluated under this proposed protocol.

## Planning validation

The source baseline, image answer leakage, sampling, accuracy denominator,
parser, and export paths were inspected directly. The question bank received
an independent methodological review. Document links and whitespace are checked;
application tests and provider calls are not part of this documentation change.

## First pilot execution — 2026-09-13

The accepted next step is implementation, automated validation, a first measured
model comparison, publication at edwardbenson.com/benchmarks/colorbench, and a
critique identifying one next improvement for discussion. Add numeric RGB,
HSL (HSK clarification pending), and OKLCH estimation to the six perception
families. Target 72 questions: eight per family across nine families, with
shared underlying color groups and descriptive pilot scores. Human calibration
remains unmeasured and must be prominent in the publication. Proposed campaign
uses the sibling 13-model roster with an estimated $25 cap.


## Implementation checkpoint — 2026-09-13

Source repository: https://github.com/eob/colorbench (draft PR #1). Root math
helpers passed 17 tests, including primary anchors, 128 round trips, circular
hue, gray coordinates, and unclipped out-of-gamut reconstruction. The frozen
artifact CI regression first failed with `ModuleNotFoundError: No module named
'scripts'`; adding the guard made the existing-release mutation/new-release
addition test pass. Raw red evidence: `/tmp/colorbench-frozen-red.log`.

The source-native 1200 × 630 share card was rendered and visually inspected;
its source and bundled-font renderer are in `branding/`. Read-only provider
availability and pricing evidence is in
`evidence/model-readiness-2026-09-13.json`. No inference was used for that check.

The actual pilot uses controlled procedural sRGB colors rather than the larger
proposed Tailwind sampling catalog. This is now explicit in the methodology.
The first measured run, independent replay, and publication remain pending at
this checkpoint; no mock score is presented as measured data.

Frozen artifact guard reversion reproduced the missing-module failure; restored
implementation passed with the 17 math checks (18 tests total). Candidate
validation passed all 72 questions in nine balanced families. Root visually
reviewed representative matching, binding, lightness, chroma, hue, gradient,
and numeric PNGs. A constant sRGB-128 gray predictor was fixed before paid
inference; its exact per-format results are recorded in
`evidence/constant-gray-baseline.json` (approximately 30.56 similarity).

Independent pre-run transport audit found that Claude rejects numeric schema
`minimum`/`maximum` constraints. Its documented SDK transformation does not
apply to our direct HTTP transport. Before protocol freeze, all providers
receive a common schema without those keywords; prompt units/ranges and
strict local validation remain in force. No paid requests preceded the fix.


## Frozen pilot execution gate

Dataset commit: `1013fdb0deb1c2a4d2df6fba3c5bc38d05cab473`.
Release descriptor: `releases/0.2.0.json`. Dataset and protocol fingerprints
were independently recomputed before registering that descriptor.

| Gate (implementation based on dataset commit above) | Result |
| --- | --- |
| `bun run test` | 198 Python tests; 10 TypeScript tests / 386 assertions; typecheck passed |
| `bun run validate:release` | 72 questions; frozen commit, protocol, files, pixels, and uniqueness verified |
| Frozen history guard against `origin/main` | Both historical dataset directories unchanged |
| Release mock smoke | 13 models × 3 completed observations, zero cost, explicitly mock and partial |
| Python package wheel | Built ColorBench 0.2.0 successfully |
| Independent source audit | No remaining critical scoring, leakage, or resume issue after wire-schema correction |

The first paid campaign will use all 72 questions for all 13 enabled models,
concurrency 6, and a cumulative $25 budget cap. Each saved malformed model
answer remains a final zero-score observation. Infrastructure retries, if
needed, retain their original attempt records and costs. No second benchmark
revision will run until the first results have been critiqued and discussed.


## First measured pilot and critique

Run `results/runs/0.2.0/pilot-20260913` completed 936/936 responses, 13 models ×
72 questions, at $5.1151914 estimated from fully recorded usage. There were no
invalid responses, infrastructure failures, or retries. Source startup was
clean commit `3481d5d`; checkpoint commit `ef4ffaa`; independently replayed
finalization, compact export, and analysis commit
`58fb5dfa5011a7ab21c51e16243407f2e950df57`. Source GitHub CI passed both push/PR
checks on the frozen implementation. Raw failure logs preserve their original
whitespace; production source passes diff whitespace checks.

The critique is in `results/first-pilot.md`. The important design finding is
within-difficulty position confounding in matching/binding: wide => A/C,
narrow => B/D, with different colors across difficulty sets. Overall answer
balance was insufficient. One next experiment is proposed: each base color
at each separation and each correct position, paired across flat/UI frames.
No second iteration has been implemented or run. Numeric formats remain
separate because output representation changes reconstruction error.

Website actual import uses source commit `58fb5dfa...`, verified source-ledger
replay and an independent TypeScript grader. Publication main/prod PRs and
live verification remain pending at this checkpoint.
