# ColorBench

Perception redesign is being planned in [the ColorBench question-design plan](tickets/plan-01-color-perception.md).
The 100-image prototype described below includes semantic judgments and visible
answer labels; its results are not valid evidence for the planned perception benchmark.

**ColorBench** is a vision-language benchmark evaluating multimodal AI models on semantic color perception, surface roles, WCAG contrast discrimination, and gradient fill understanding in software screenshots.

It forms the fourth foundational benchmark in Ted Benson's design perception suite:
1. [FontBench](https://github.com/eob/fontbench): Typography (family, category, weight, kerning, line-height)
2. [BorderBench](https://github.com/eob/borderbench): Surfaces & Edges (stroke width, style, sides, corner radius curvature, elevation/shadow)
3. [LayoutBench](https://github.com/eob/layoutbench): Spatial Geometry & Flow (direction, justify-content, align-items, gap tokens, padding tokens)
4. **ColorBench**: Semantic Palette, Surface Roles, & Contrast Tiers (primary/danger/success, wash/tint vs solid, WCAG AAA/AA/failing contrast, linear gradients)

---

## Dimensions Evaluated

ColorBench evaluates models across a standardized UI card container rendered on high-resolution Retina canvases (2× DPR, 560×380 px) across 5 core color dimensions:

1. **Semantic Role Intent** (`semantic_role`):
   - `primary`: Core call-to-action / brand emphasis
   - `secondary`: Neutral, supporting, or auxiliary surface
   - `success`: Positive confirmation, verified badge, or operational health
   - `warning`: Cautionary alert, transient advisory, or quota warning
   - `danger`: Destructive action, error modal, or failure badge
   - `info`: Informational callout, guide banner, or neutral telemetry

2. **Surface Role Treatment** (`surface_role`):
   - `neutral-surface`: Standard canvas/card surface (slate, gray, black, or white)
   - `subtle-tint`: Low-opacity or high-luminance wash (e.g. soft pastel tint for badge/pill backgrounds)
   - `brand-fill`: Bold saturated color fill
   - `elevated-surface`: Layered surface elevation steps (surface-0 to surface-3)

3. **WCAG Contrast Tier Discrimination** (`contrast_tier`):
   - `aaa-high`: Contrast ratio >= 7.0:1 (passes enhanced accessibility)
   - `aa-standard`: Contrast ratio between 4.5:1 and 6.9:1 (standard text body)
   - `large-text-subdued`: Contrast ratio between 3.0:1 and 4.4:1 (large text or decorative/subdued labels)
   - `failing-disabled`: Contrast ratio < 3.0:1 (disabled states or failing tone-on-tone contrast)

4. **Visual Fill Style** (`fill_type`):
   - `solid`: Flat opaque background fill
   - `linear-gradient`: Directional color ramp (e.g. 135deg hue blend)
   - `outline-transparent`: Transparent/ghost fill with colored perimeter stroke

5. **Color Theme Mode** (`theme`):
   - `light`: High-luminance canvas backgrounds
   - `dark`: Low-luminance canvas backgrounds

---

## Dataset Breakdown (100 Tasks)

The benchmark comprises exactly 100 systematic tasks covering:
- **Semantic Role Sweeps**: Solid fills across primary, secondary, success, warning, danger, and info in light and dark mode.
- **Subtle Tint Washes**: Soft tint surfaces paired with matched semantic text and border strokes.
- **Ghost Outlines**: Transparent pill badges with colored border strokes.
- **Directional Gradients**: Saturated multi-stop linear gradients.
- **Contrast Discrimination**: Pairs engineered at exact WCAG contrast boundaries (21:1 stark, 7:1 AAA, 4.5:1 AA, 3:1 subdued, and <2.5:1 disabled/failing).
- **Layered Surface Elevations**: Progressive elevation tiers from canvas to card to popover.
- **UI Component Archetypes**: Active beta pills, operational health badges, billing alert cards, failing build notices, and pro tier tags.

---

## Quick Start

### 1. Installation

```bash
bun install
python3 -m venv .venv
.venv/bin/pip install -e .
```

### 2. Render Benchmark Dataset

Renders all 100 high-DPI screenshots with Playwright Chromium and generates `dataset/colorbench-1/manifest.json`:

```bash
bun run render
```

### 3. Run Benchmark Baseline

```bash
# Run quick mock test
bun run benchmark:mock

# Run real evaluation against frontier vision models
.venv/bin/python baseline/runner.py --models gemini-3.1-pro-preview gemini-3.8-flash claude-sonnet-5 gpt-5.6-sol
```

### 4. Export Structured Summary

```bash
bun run export
```

---

## Manifest Task Format

Each task in `dataset/colorbench-1/manifest.json` provides:
```json
{
  "taskId": "colorbench-001",
  "imagePath": "/path/to/dataset/rendered/colorbench-001.png",
  "imageFilename": "colorbench-001.png",
  "groundTruth": {
    "semantic_role": "primary",
    "surface_role": "brand-fill",
    "contrast_tier": "aa-standard",
    "fill_type": "solid",
    "theme": "light",
    "bg_color": "#2563eb",
    "text_color": "#ffffff"
  },
  "prompt": "Analyze the visual color design and contrast of the card container in this software screenshot..."
}
```

---

## Testing

```bash
# Test specimen generation and token integrity
bun test

# Test evaluator scoring and SQLite state store
.venv/bin/pytest tests
```

---

## License

MIT © Edward Benson
