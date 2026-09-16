# Independent decoded candidate review — 2026-09-16

The rendered 0.4.0 candidate passes this independent review. No paid model requests or production edits were made. The replay script uses Pillow directly, without importing the generator or release validator; manifest coordinates locate regions, while equality and colors come from decoded PNGs. Run `.venv/bin/python tickets/evidence/fix-05-pixel-review.py` to reproduce the adjacent JSON.

## Pixel findings

- All 512 question rows reference the expected image hashes; there are 456 unique PNG filenames. Manifest SHA-256: `0271b7d47a79ec8988e2edd11c986555e135419695c51d682e1981aa093addc5`.
- All 176 retained matching, binding, hue, and numeric task images are pixel-identical to their frozen 0.3.2 counterparts.
- All 16 context reference groups retain their 0.3.2 colors. Within each new group, colors, region centers, prompts, and answers stay fixed across five conditions. Only the declared 12px surround rings change; each of four distinct surrounds occupies every option position, with a neutral control.
- All 16 small-region reference groups retain their 0.3.2 colors. Within each new group, colors, centers, prompts, and answers stay fixed across four geometries. The complete 84px maximum footprint matches the declared filled square or outlined square, including the neutral band around the 20px variant. Every pixel outside these footprints stays identical.
- Every gradient field has shared endpoints and an exact shared RGB histogram, four distinct interiors, and a unique full-field answer. All 240 single-column signatures have accuracy ceilings at or below 50%; the endpoint ceiling is 25%. Exactly two palettes become pixel-identical under Pillow’s 8-bit grayscale conversion.
- The full-image oracle with only the other patch hidden, conditioned on the full prompt, is exactly 50% for all 24 same–different cell/mapping/position checks and 62.5% for all 32 lightness/chroma cell/direction/position checks.

## Visual inspection

Viewed original, unmodified PNGs `gradient-01`, `gradient-09`, `smallmatch-01`, `smallmatch-05`, `smallmatch-09`, `smallmatch-13`, `context-01`, `context-05`, and `context-09`. Labels and instructions are legible, region centers stay fixed, the gradient permutations are visible, and no clipping or mismatched labels were found. Thin outlines are deliberately small colored regions; the current wording explicitly includes them.

## Validator review

The first draft of `baseline/direct_controls.py` correctly checks decoded pairing, prompt conditioning, identity mappings, exact matches, reference crossings, surround rotations, and matched-color/position groups. Three regression omissions were sent to its owner: require the gradient single-column ceiling, pin exactly two grayscale-matched palettes for the complete corpus, and validate the full 84px footprint around the 20px square before masking it. These are validator coverage improvements; the rendered candidate already satisfies each condition under the independent replay above. All three are now implemented in the stable validator with negative regression tests. Independently ran `tests/test_direct_controls.py` and `tests/test_pilot_analysis.py`: 34 tests passed. No remaining substantive validator finding.

## Interpretation limits

These are finite-corpus input guarantees, not evidence of how a model solves the questions or how it will generalize. Ordering cannot have an exact 50% one-patch ceiling in a finite strict-order corpus; 62.5% is the declared five-color-chain bound. The four fields and their crossed conditions remain dependent observations. Grayscale identity is specific to the declared Pillow conversion, and the gradient control requires comparison of at least two interior locations rather than proving exhaustive inspection of the strip.

## Paired-analysis cross-check

Independently reviewed `scripts/analyze_pilot.py` and its eleven tests. A separate two-model synthetic report built from all 512 actual candidate specimen IDs, group IDs, and design metadata confirms per-model denominators: 16 reference pairs for each context condition comparison, 16 for each size/thickness comparison, 24 same–different mapping pairs, 16 hue questions per fixed/varying context, 16 RGB estimates, and 48 matching/binding pairs. Contrasting all-correct versus all-choice-wrong responses preserve model separation and produce the expected semantic consistency. Invalid responses remain in correctness denominators, and mapping consistency uses only pairs with two valid responses. No issue found. This is a metadata/aggregation fixture, not a model result.
