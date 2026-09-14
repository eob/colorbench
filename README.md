# ColorBench

Can a model match the color it sees?

ColorBench measures color matching, lightness and chroma comparisons, hue,
component fills, gradients, same–different judgments, and numeric color
reconstruction. It belongs to the design-perception quartet with
[FontBench](https://github.com/eob/fontbench),
[BorderBench](https://github.com/eob/borderbench), and
[LayoutBench](https://github.com/eob/layoutbench).

**Release 0.3.2 contains 264 questions using 232 unique images.** Every
four-choice option field appears with all four possible reference targets.
The decoded-pixel gate verifies that the whole image outside R and the prompt
stay identical, so an input-only predictor that ignores R has expected accuracy
25%. This repairs an option-order shortcut found during the publication review
of 0.3.1. Frozen historical releases remain available, but their scores must
not be compared to this revised corpus.

[Results and interactive examples](https://edwardbenson.com/benchmarks/colorbench)
· [Current results](results/third-pilot.md)
· [Methodology](docs/methodology.md)
· [Publication review](docs/publication-review-2026-09-14.md)

| Family | n | Question | Measure |
| --- | ---: | --- | --- |
| Matching | 48 | Which swatch has exactly R's color? | Four-choice accuracy |
| Lightness | 16 | Which patch is lighter/darker? | Two-choice accuracy |
| Chroma | 16 | Which patch is more/less colorful? | Two-choice accuracy |
| Hue | 32 | Which option has R's hue? | Four-choice accuracy; exploratory |
| Binding | 48 | Which component has R's interior fill? | Four-choice accuracy, paired with matching |
| Gradient | 8 | Which strip reproduces R's full progression? | Four-choice accuracy; exploratory |
| Same–different | 16 | Are A and B exactly the same color? | Two-choice accuracy and trial-type breakdown |
| Context | 16 | Which interior matches R across surrounds? | Four-choice accuracy |
| Small-region | 16 | Which small square or outline matches R? | Four-choice accuracy |
| RGB | 16 | Estimate R in 8-bit sRGB | Reconstruction error, similarity, tight metrics, validity |
| HSL | 16 | Estimate R as hue and saturation/lightness percentages | Same reconstruction measures |
| OKLCH | 16 | Estimate R as lightness, chroma, and hue | Same reconstruction measures; gamut flags |

There is no combined score across these different tasks. Numeric formats share
sixteen target images but use independent model requests. Matching and binding
share image pairs; four references within an option set share the same choices.
These correlations, the small designed sample, and unmeasured human agreement
limit the interpretation. Separation slices do not establish human thresholds
or isolated psychometric effects. Numeric estimates also measure coordinate
knowledge.

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
checks decoded pixels, geometry, font evidence, prompts, unique answers,
reference-masked controls, and paired fields. Rendering does not revise a release.

```bash
# Offline smoke test: mock output cannot be finalized for publication.
bun run benchmark:mock

# A full campaign over the frozen shared cohort.
.venv/bin/python -m baseline.runner --release 0.3.2 \
  --config config/models.all.json --run-id pilot-example \
  --max-tasks 264 --concurrency 6 --budget-usd 30

# Commit completed source artifacts before sealing them.
.venv/bin/python -m baseline.finalize \
  --run-dir results/runs/0.3.2/pilot-example --scope full
.venv/bin/python -m baseline.finalize \
  --run-dir results/runs/0.3.2/pilot-example --verify
.venv/bin/python -m baseline.export_structured \
  --run-dir results/runs/0.3.2/pilot-example --output results/colorbench-pilot.json
.venv/bin/python scripts/audit_publication.py \
  results/runs/0.3.2/pilot-example results/colorbench-pilot-audit.json
```

API key environment-variable names are in `config/models.all.json`. Resuming
an unsealed run keeps its dataset, model configuration, and protocol identity.
Invalid model answers are retained and scored rather than retried. Runner
attempts may contain internal HTTP retries: inspect their recorded counts and
usage coverage before interpreting cost. Catalog-price estimates and unmetered
budget allowances are distinct from actual provider invoices.

## Historical releases

[0.3.1 results](results/second-pilot.md) preserve the measured corpus with the
option-order flaw; [0.2.0 results](results/first-pilot.md) preserve an earlier
pilot with answer-position/separation confounds. Neither is current evidence
for the corrected corpus. Release 0.3.0 was superseded before a paid run.

`dataset/colorbench-1`, `dataset/rendered`, and
`results/colorbench_summary.json` preserve a still-earlier 100-image semantic
prototype with visible answer labels. Its scores are invalid evidence for this
perception benchmark and are excluded from publication.

## License

MIT © Edward Benson. The bundled DejaVu font includes its own license.
