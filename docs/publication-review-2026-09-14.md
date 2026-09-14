# ColorBench publication review — 2026-09-14

## Review conclusion and scope

The review found a material experimental flaw in 0.3.1 and repaired it in a
new frozen release, 0.3.2. Ordered distractors allowed accurate answers without
consulting the reference. Every four-choice field is now held identical across
four requests whose references select A, B, C, and D once each. The entire
remaining image and external prompt are independently checked for equality.
This gives any deterministic reference-free rule exactly 25% accuracy on a
complete cell and any stochastic input-only rule 25% expected accuracy.

The corpus has 264 questions and 232 PNGs, with 32 hue questions so fixed and
varying lightness/chroma contexts both receive complete reference cells. The
264-question campaign completed all thirteen configured models afresh. Publication
uses the sealed run and the [third-pilot report](../results/third-pilot.md).

This review covers dataset generation, rendering and geometry, labels and
answer uniqueness, option-position and stimulus confounds, model requests,
parsing, color conversion, scoring and aggregation, execution/resume behavior,
cost evidence, release freezing, finalization, exports, and written claims.
It does not supply human calibration, provider invoices, or access to provider
image preprocessing or model internals.

## Evidence for the repaired flaw

In 0.3.1, the target was inserted into three coordinate-sorted distractors and
restricted to coordinate ranks two and three. Removing a misplaced option
often restored sorted order, identifying it as the target without viewing R.
A control reads only the four option pixels, chooses the RGB channel with the
largest range, and retains middle-ranked candidates whose removal leaves the
remaining option values monotone. It guesses uniformly among remaining candidates.

| Family | 0.3.1 expected control score | Options observed |
| --- | ---: | ---: |
| Matching | 73.96% | 48 questions |
| Binding | 73.96% | 48 questions |
| Context | 75.00% | 16 questions |
| Small-region | 75.00% | 16 questions |

The control receives neither R, answer metadata, task axis, nor construction
parameters. The historical report's 50% target-rank bound missed this
additional order cue. Hue and gradient options also lacked a construction
that required R: for example, the old hue options contained a distinguished
near pair. The repair therefore covers all six four-choice families.

The first regression demanded that every identical option set have all four
reference answers. The existing source failed all six family tests:

```text
error: expect(received).toEqual(expected)
  [ "A", - "B", - "C", - "D" ]
0 pass
6 fail
```

[Full RED evidence](../tickets/evidence/option-control-red.log),
[GREEN evidence](../tickets/evidence/option-control-green.log), and
[temporary-reversion evidence](../tickets/evidence/option-control-reversion.log)
record the complete checks. Reinstating the old generator reproduced all six
failures; restoring the fix passed all six.

The decoded gate goes beyond source-field comparison: it masks only the target
rectangle in each PNG, then groups by full remaining pixel bytes and canonical
prompt. Each group must contain all four answers exactly once. Separate tests
alter a pixel outside R, add a prompt hint, duplicate an answer, drop a trial,
and remove a control-set identity; every mutation is rejected.

There are 42 controlled fields across the six families: twelve matching,
twelve binding, eight hue, two gradient, four context, and four small-region.
Matching and binding share their twelve underlying color sets. These are
construction cells, not independent statistical samples.

## Dataset and renderer review

- All task IDs and image hashes are unique except the deliberately shared
  numeric images. All four-choice and two-choice labels are balanced.
- Matching/binding separation cells retain all four answer positions. All
  four target ranks are balanced within each cell and against answer position.
  Context and small-region target ranks are also balanced against position.
- Hue crosses four separations with both fixed and varying lightness/chroma
  contexts and all four answers. Decoded hue winners are unique.
- Same–different crosses equal/different trial type with both response-letter
  mappings. Image text does not reveal the mapping. The original two-choice
  comparison and same–different stimuli are preserved.
- Gradient option fields have identical histograms, equal geometry, and unique
  full-field matches. Each of the four visible progressions becomes R; cyclic
  shifts can produce a visible wrap and are described accurately.
- Ground truth is independently checked against decoded RGB pixels and region
  hashes. Matching, binding, and context compare interior equality; small
  outlines compare the colored border; numeric targets use flat RGB interiors.
- The generator rejects out-of-gamut construction colors rather than clipping
  them. Decoded ordering and separation tolerances are checked after rounding.
  [Actual nearest-gap ranges](../tickets/evidence/decoded-gaps-0.3.2.json) expose
  quantization variation: nominal matching chroma 0.007 spans 0.00445–0.00745.
- Browser profile, 800 × 640 dimensions, DPR 1, font bytes and actual glyph use,
  opacity, metadata absence, neutral backgrounds, and fixed labels are checked.
  Matching, varying hue, gradient, and outline examples were visually inspected.
- Candidate rendering cannot overwrite historical or registered releases.
  The new PNGs and manifest were committed before their descriptor was created.

The decoded gate's spatial controls and the committed hashes jointly protect
against mislabeled images, hidden label cues, nondeterministic decoration,
stale canvas state, and accidental release mutation. They cannot establish
that provider preprocessing preserves every original pixel.

## Scoring and inference review

Choice invalids remain incorrect. Numeric invalids receive zero similarity and
zero tight similarity, while raw-distance and near-exact rates use explicit
valid-only denominators. There is no combined family score. The 0.2 cap and
0.05 tight cap are engineering choices rather than visibility thresholds.

The strict parser rejects duplicate keys, extra fields, strings, booleans,
nonfinite coordinates, incompatible schemas, and prose wrappers. RGB uses
strict integers; HSL uses percentages; OKLCH uses its native units. Hue wraps
modulo 360. Out-of-gamut OKLCH answers are scored without clipping. Gray target
hue is canonicalized; hue diagnostics exclude near-neutral targets according
to the declared chroma cutoff.

The protocol's math tests cover primary-color anchors, sRGB transfer-function
boundaries, achromatic handling, round trips, circular hue, invalid answers,
and extreme numeric cases. An independent audit script imports neither the
production conversion module nor its evaluator, reimplements HSL conversion
and the published matrix equations, parses archived answers, and reproduces
choice counts and every numeric distance and similarity.

Provider request review confirms fresh user messages contain only PNG bytes
and the frozen prompt/schema. Filenames, task IDs, group IDs, options metadata,
and previous answers never enter the request body. OpenAI storage is disabled.
Each provider retains its native image preprocessing and default inference
behavior; model configuration parity does not establish equal internal compute.
Recorded API model IDs are not archived model weights.

No changes were made to the frozen prompts, schemas, parser, color conversion,
provider requests, grader, or aggregation formulas. Consequently the protocol
fingerprint remains `a69ef1881b837a291a96f7f7995e31fbd19092b8cac59c3c7cfdadef158d84ce`.
The dataset fingerprint and release identity change. All thirteen models are
rerun because the stimuli changed; cached predictions are not transferred.

## Execution and publication review

The runner's release gate executes before provider clients are created. Resume
identity includes frozen data, model configuration, and protocol. Ledger and
budget tests cover independent model configurations, provider pauses,
infrastructure failures, worker exceptions, interruption, cost reservations,
and persistence. Invalid model answers are final scored observations.

Finalization verifies SQLite integrity, chronology, attempt exports, common
cohort, model roster, committed source artifacts, and replayed raw predictions.
Seals cover every output artifact. Verification rejects changes to source rows,
answers, costs, coverage, identities, and final metrics. Export consumes an
explicit verified run rather than choosing a file by modification time.

The review corrected a separate 0.3.1 reporting error. Its 3,224 ledger attempts
contained 3,225 HTTP requests: GPT-5.6 Sol retried `colorbench-oklch-10` once
without complete retry-usage evidence. The $21.49166615 spending figure included
a $0.10192 conservative allowance. Recorded token usage at catalog prices
summed to $21.38974615. "No retries" and "complete usage" were false; the
[historical report](../results/second-pilot.md) and
[supplemental audit](../results/colorbench-pilot-0.3.1-audit.json) now distinguish
these quantities. Underlying sealed historical artifacts remain untouched.

The independent audit reproduces all 624 historical numeric answers with
maximum distance drift 3.13e-16 and maximum score drift 6.26e-13. The original
structured export and detailed analysis reproduce byte-identically. This
confirms arithmetic fidelity while leaving the experimental criticism intact.

## Remaining interpretation limits

- Human agreement and display-calibrated perceptual thresholds are unmeasured.
  Small coordinate gaps are construction parameters rather than JND claims.
- The same targets and option fields are reused. Model responses, matched
  families, numeric formats, and four-reference cells are correlated. No
  independent-observation intervals or pooled rankings are warranted.
- Base colors vary across separation levels in matching and hue. Those slices
  describe this designed corpus, not an isolated separation effect or fitted
  psychometric function. Context uses fixed surrounds by position; it does not
  isolate surround causality without an otherwise identical neutral control.
  The matching/binding paired treatment includes both neutral frames and
  accompanying question wording, so it does not isolate frames alone.
- Small-region geometry is not factorial with axis/hue. Dot-versus-outline
  differences cannot establish a pure geometry effect. There are only two
  gradient option fields and sixteen numeric targets.
- Small-region external instructions say to ignore "borders," while the eight
  outline images explicitly say to compare colored outlines. The latter makes
  the scored region visible and answerable, but performance can include
  instruction resolution. A [next-protocol wording correction](../tickets/fix-04-small-region-prompt.md)
  is tracked; the completed run and its frozen protocol are preserved.
- Same–different binary outcomes expose response tendency, but eight trials
  of each type per model cannot establish stable response mechanisms. A human
  agreement screen would not by itself resolve model sensitivity or criterion.
- Numeric answers mix visual input and coordinate-system knowledge. RGB, HSL,
  and OKLCH differences are descriptive despite identical target images.
- A single request per model/task does not estimate run-to-run variability.
  API defaults, preprocessing, and model aliases can change outside this repo.
- Costs use archived catalog prices, not provider invoices. The inherited Meta
  prices retain their documented verification limitation. Individual internal
  retry error bodies are not archived separately by the provider wrapper.

These limits are disclosed in the current methodology and report. They do not
justify silently changing a frozen corpus or making unsupported general model
rankings.

## Validation record

Base reviewed: `653183f23b7855fd3c9c855c876995878631ca0f`.
Corrected dataset commit: `09b0dd9`; clean registered runner commit: `1b3079e`.

| Gate | Result |
| --- | --- |
| Baseline `bun run test` | 244 Python; 29 TypeScript; typecheck passed |
| Corrected `bun run test` | 250 Python; 35 TypeScript; 1,474 TS assertions; typecheck passed |
| Full decoded candidate/release gate | 264 tasks / 232 PNGs; zero errors |
| Whole-image reference controls | 42 complete four-reference fields |
| Regression/reversion | Six failures → six passes → six original failures → six passes |
| Historical frozen-artifact gate | All eight prior descriptor/dataset paths unchanged |
| 0.3.1 seal verification | 3,224 raw answers replayed |
| 0.3.1 export and analysis replay | Both byte-identical |
| Independent historical numeric replay | 624 answers; maximum ΔE drift 3.13e-16 |

Additional completed gates: the final code suite passes 258 Python tests and
35 TypeScript tests, the package wheel builds, a complete repeat render
reproduces all 232 PNGs and the manifest byte-identically, and both remote
GitHub Actions test jobs pass on the final code commit `8312b18`.

## Completed corrected campaign

The sealed 0.3.2 run contains all **3,432 final responses** across thirteen
configurations and all 264 questions. The clean runner source was `1b3079e`;
raw campaign artifacts were committed before finalization. The finalizer
records a clean checkout, and verification replays the complete shared cohort.
The [sealed data and independent audit](../results/colorbench-pilot-0.3.2-audit.json)
were published in `fcba535`.

| Final gate | Result |
| --- | --- |
| Full common cohort | 13 models × 264 tasks = 3,432 final responses |
| Finalization seal verification | Pass; clean committed source and complete cohort |
| Publication export, analysis, and audit replay | All three reproduce byte-identically |
| Independent raw-answer grading | 3,432 answers and 156 model–family summaries reproduced |
| Independent numeric replay | 624 answers; maximum ΔE drift 4.51e-16, score drift 9.09e-13 |
| Decoded reference controls | All 42 cells cover A/B/C/D; deterministic baseline 25% |
| Historical order control on 0.3.2 | 25% expected accuracy in all four affected families |
| Response validity | 3,431 valid; one incomplete response retained as incorrect |
| Execution accounting | 3,432 runner attempts; 3,437 HTTP requests; five internal retries |
| Cost audit | $22.79714445 metered subtotal + $0.17731400 reserve = $22.97445845 ledger |

The single invalid answer is Muse Spark 1.3 on `colorbench-context-06`, which
exhausted its 16,384-output-token limit. It was not retried for semantic
correctness. Five provider-internal retry requests lack complete usage;
there are no separate infrastructure failure records. Catalog prices and
reserve allowances remain estimates rather than billing evidence.

The [third-pilot report](../results/third-pilot.md) contains measured family
results, separation slices, paired outcomes, valid-only numeric denominators,
and a semantic same–different response table. Identical pairs were correct in
102/104 responses and different pairs in 35/104. There were 171/208 “same”
answers and no invalids in this family; this demonstrates a response tendency
on these inputs without fitting perceptual thresholds. All new conclusions
refer to 0.3.2 alone; the old shortcut prevents longitudinal interpretation.

Independent reviews by the website owner and the LayoutBench reviewer
confirmed the full-image control construction and scoring, and identified the
outline-wording limitation disclosed above. No frozen stimuli or protocol
were changed after the campaign started.
