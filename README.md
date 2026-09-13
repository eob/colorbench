# ColorBench

Can a model see color?

ColorBench measures visual color matching, comparison, object association,
gradient recognition, and numeric color estimation. It is part of the design
perception quartet with [FontBench](https://github.com/eob/fontbench),
[BorderBench](https://github.com/eob/borderbench), and
[LayoutBench](https://github.com/eob/layoutbench).

**Release 0.2.0 is an exploratory pilot:** 72 questions, eight per family,
using 56 unique images. Human agreement has not been measured. These small,
controlled samples do not establish general model rankings or human perceptual
thresholds. Numeric estimation includes knowledge of color coordinates.

[Results and interactive examples](https://edwardbenson.com/benchmarks/colorbench)
· [Methodology](docs/methodology.md)
· [Design and implementation record](tickets/plan-01-color-perception.md)

| Family | Question | Reported measure |
| --- | --- | --- |
| Matching | Which swatch has exactly R's color? | Four-choice accuracy |
| Lightness | Which patch is lighter/darker? | Two-choice accuracy |
| Chroma | Which patch is more/less colorful, using a visible reference? | Two-choice accuracy |
| Hue | Which option has R's hue despite lightness/chroma changes? | Four-choice accuracy; exploratory |
| Binding | Which component has R's interior fill? | Four-choice accuracy, paired with matching |
| Gradient | Which strip reproduces R's full color progression? | Four-choice accuracy; exploratory |
| RGB | Estimate R as 8-bit gamma-encoded sRGB | Reconstruction error, similarity, validity |
| HSL | Estimate R as hue degrees and saturation/lightness percentages | Reconstruction error, similarity, validity |
| OKLCH | Estimate R as lightness, chroma, and hue degrees | Reconstruction error, similarity, validity |

There is no combined score across these different tasks. Answer positions are
balanced. The three numeric formats share identical target images but each gets
a fresh model request. No target color names or numeric answers appear in images.

## Reproduce

Use Bun 1.3.14 and Python 3.11. Chromium and the bundled DejaVu font are pinned
in the renderer's dependency and artifact records.

```bash
bun install --frozen-lockfile
bunx playwright install --with-deps chromium
python3 -m venv .venv
.venv/bin/python -m pip install -e .
bun run test
bun run validate:release
```

`bun run render` creates a replaceable candidate in
`dataset/candidate-rendered`; it refuses frozen and historical dataset paths.
`bun run validate:candidate` independently checks decoded pixels, geometry,
font evidence, canonical prompts, answer uniqueness, and controlled pairing.
Rendering does not revise a registered release.

```bash
# Offline smoke run; mock output cannot be finalized for publication.
bun run benchmark:mock

# A paid run of the frozen pilot with a shared 72-question cohort.
.venv/bin/python -m baseline.runner --release 0.2.0 \
  --config config/models.all.json --run-id pilot-example \
  --max-tasks 72 --budget-usd 25

# Seal only after every requested model has completed the shared cohort.
.venv/bin/python -m baseline.finalize \
  --run-dir results/runs/pilot-example --scope full
.venv/bin/python -m baseline.finalize \
  --run-dir results/runs/pilot-example --verify
.venv/bin/python -m baseline.export_structured \
  --run-dir results/runs/pilot-example --output results/colorbench-pilot.json
```

Set the providers' API key environment variables documented in
`config/models.all.json`. Recorded usage and catalog prices determine estimated
cost; the runner reserves budget before dispatch. Rerunning the same unsealed
run ID resumes its state with the same dataset, configuration, and protocol.
Invalid answers remain scored observations; they are not retried to improve scores.

## Historical prototype

`dataset/colorbench-1`, `dataset/rendered`, and
`results/colorbench_summary.json` preserve the earlier 100-image prototype.
It included semantic judgments and visible answer labels. Its scores are **not
valid evidence for this perception pilot** and are excluded from publication.

## License

MIT © Edward Benson. The bundled DejaVu font includes its own license.
