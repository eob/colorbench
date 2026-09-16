# ColorBench

Can a model match the color it sees?

ColorBench tests direct color judgments: matching swatches, comparing
lightness and chroma, identifying hue, matching color progressions, and
estimating color coordinates. It belongs to the design-perception quartet
with [FontBench](https://github.com/eob/fontbench),
[BorderBench](https://github.com/eob/borderbench), and
[LayoutBench](https://github.com/eob/layoutbench).

**Release 0.4.0 contains 512 questions using 456 unique images. All thirteen
configurations completed the full cohort on September 16, 2026.** It repairs
single-patch and gradient-endpoint
shortcuts, clarifies outline instructions, and adds matched controls for
surrounds, filled-square size, and outline width. The
[repair notes](docs/direct-color-repairs-0.4.0.md) explain the changes and their
limits. Scores from earlier releases do not transfer to this corpus.

[Current results](results/fourth-pilot.md) · [Methodology](docs/methodology.md)
· [Release and replay instructions](releases/README.md)
· [Historical 0.3.2 results](results/third-pilot.md)
· [Website report for 0.3.2](https://edwardbenson.com/benchmarks/colorbench)

| Family | Questions | Question | Measure |
| --- | ---: | --- | --- |
| Matching | 48 | Which swatch has exactly R's color? | Four-choice accuracy |
| Lightness | 64 | Which patch is lighter or darker? | Two-choice accuracy |
| Chroma | 64 | Which patch is more or less colorful? | Two-choice accuracy |
| Hue | 32 | Which option has R's hue? | Four-choice accuracy, split by fixed/varying lightness and chroma |
| Component fill matching | 48 | Which component has R's interior fill? | Four-choice accuracy, paired with matching |
| Gradient | 16 | Which strip matches R's color progression? | Four-choice accuracy |
| Same–different | 48 | Are A and B exactly the same color? | Two-choice accuracy, trial-type counts, and answer-mapping consistency |
| Context | 80 | Which interior matches R across surrounds? | Four-choice accuracy and paired neutral/surround outcomes |
| Small-region | 64 | Which filled square or outline matches R? | Four-choice accuracy, with separate size and stroke-width pairs |
| RGB | 16 | Estimate R in 8-bit sRGB | Reconstruction error, exact/tolerance counts, similarity, and validity |
| HSL | 16 | Estimate R as hue and saturation/lightness percentages | Reconstruction error, component errors, similarity, and validity |
| OKLCH | 16 | Estimate R as lightness, chroma, and hue | Same reconstruction measures, plus gamut flags |

Every four-choice option field appears with all four possible reference
colors. The decoded-image gate checks that the rest of the image and prompt
remain identical within each group, bounding a predictor that ignores R at
25% expected accuracy. Additional controls test whether one patch, gradient
endpoints, or unrelated pixels reveal an answer. These are construction
checks; they do not show which strategy a model uses.

There is no combined benchmark score. Related questions share colors, option
fields, images, or intervention conditions. Human agreement and repeated-run
variability have not been measured. Results describe this designed corpus
through provider image pipelines; numeric estimates also require coordinate
knowledge. Similarity out of 100 is not an exact-reconstruction percentage or
a human visibility threshold.

## Reproduce

Use Bun 1.3.14 and Python 3.11. Playwright is pinned, and the renderer records
the Chromium version and bundled DejaVu font evidence.

```bash
bun install --frozen-lockfile
bunx playwright install --with-deps chromium
python3 -m venv .venv
.venv/bin/python -m pip install -e .
bun run test
bun run validate:release
```

`bun run render` writes a replaceable candidate in `dataset/candidate-rendered`.
It refuses historical and registered release paths. `bun run validate:candidate`
checks decoded pixels, geometry, fonts, prompts, unique answers, and the
construction controls. Rendering does not revise a frozen release.

```bash
# Offline smoke test; mock output cannot be published as measurements.
bun run benchmark:mock

# Full shared cohort: 512 questions for all 13 configured models.
.venv/bin/python -m baseline.runner --release 0.4.0 \
  --config config/models.all.json --run-id pilot-example \
  --concurrency 6 --budget-usd 65

# Require summary.json status "complete" and 512 completed tasks per model.
# Commit completed source artifacts before sealing them.
.venv/bin/python -m baseline.finalize \
  --run-dir results/runs/0.4.0/pilot-example --scope full
.venv/bin/python -m baseline.finalize \
  --run-dir results/runs/0.4.0/pilot-example --verify
.venv/bin/python -m baseline.export_structured \
  --run-dir results/runs/0.4.0/pilot-example --output results/colorbench-pilot-0.4.0.json
.venv/bin/python scripts/analyze_pilot.py \
  results/runs/0.4.0/pilot-example results/colorbench-pilot-0.4.0-analysis.json
.venv/bin/python scripts/audit_publication.py \
  results/runs/0.4.0/pilot-example results/colorbench-pilot-0.4.0-audit.json
```

API key environment-variable names are in `config/models.all.json`. Resume an
unfinished campaign with the same run ID and unchanged dataset, protocol, and
model configurations. A paused or budget-exhausted invocation can exit zero;
check its summary before claiming completion. Invalid answers remain scored
observations. Infrastructure failures remain retryable, with earlier attempt
costs retained. Catalog-price estimates and unmetered budget allowances are
not provider invoices.

## Historical results

[0.3.2 results](results/third-pilot.md) describe 264 questions and retain the
construction limitations repaired in 0.4.0. Its frozen inputs, raw answers,
seals, and JSON exports remain unchanged. Replay requires compatible source
`8fc558433146066b8e1ed9b44303689b2433478d`; see the
[historical replay instructions](releases/README.md#historical-replay).

[0.3.1 results](results/second-pilot.md) preserve the corpus with an option-order
shortcut; [0.2.0 results](results/first-pilot.md) preserve an earlier pilot with
answer-position/separation confounds. Release 0.3.0 was superseded before a
paid run. Different release scores are not evidence of model improvement.

`dataset/colorbench-1`, `dataset/rendered`, and `results/colorbench_summary.json`
preserve a still-earlier 100-image prototype with visible answer labels. Its
scores are excluded from perception-benchmark publication.

## License

MIT © Edward Benson. The bundled DejaVu font includes its own license.
