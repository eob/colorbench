# Direct-color control repairs in 0.4.0

ColorBench asks direct questions about color: match a swatch, compare
lightness or chroma, identify a hue, compare a progression, or estimate color
coordinates. Release 0.4.0 keeps that scope and repairs the construction of
several tasks. It does not add object reasoning.

The 0.3.2 review reproduced the archived grades but found that some questions
could be solved without the intended comparison. These are limitations of
the stimulus design, not evidence that any particular model used a shortcut.
Historical releases and their measured responses remain unchanged.

## What changes

| Condition | 0.3.2 limitation | 0.4.0 construction |
| --- | --- | --- |
| Small colored outlines | External text excluded borders while the image scored the outline. | Both instructions explicitly include colored outlines and exclude labels/neutral areas. |
| Gradients | Each option had a distinct left endpoint; an 8-bit grayscale endpoint identified every answer. | Options share endpoints and histograms while two interior regions vary independently. Four palettes replace two. |
| Same–different | Identical and differing pairs had different single-patch color distributions. | Each endpoint pair produces `(c,c)`, `(c,d)`, `(d,c)`, `(d,d)`, each under both response mappings. |
| Lightness and chroma | All pairs straddled one absolute center, allowing a perfect one-patch rule. | Four overlapping five-color chains per family vary absolute ranges and reuse intermediate colors above and below their neighbors. |
| Surrounds | Each field appeared on one fixed surround assignment with no neutral control. | The same colors/reference/positions appear on neutral surrounds and four cyclic surround assignments. |
| Size and stroke | Geometry changed alongside the palette and color axis. | Every field appears as 20px and 84px filled squares and 84px outlines with 3px and 12px strokes. |

Size variants share region centers, label positions, image wording, external
prompts, colors, and references. Outline variants change stroke width at fixed
outer dimensions. Filled-size and outline-width effects are separate paired
comparisons. Surround variants change only the declared surround pixels.

## Construction controls

The decoded-image gate checks the committed PNGs, not just generator intent.
It retains the reference-masked control: every identical input outside R and
its accompanying prompt occurs with all four correct answers. Ignoring R
therefore has 25% expected accuracy on these balanced groups.

For same–different, either patch alone plus all remaining pixels and the
external prompt has a 50% optimal lookup accuracy. For ordering, the analogous
ceiling is 62.5%: three interior colors in each five-color chain occur with
both answers, while the two endpoint colors retain an ordering cue. Strict
finite scalar comparisons cannot make every endpoint equally likely to be
larger and smaller. This control removes perfect one-patch prediction without
claiming that all absolute-color information can be eliminated.

Gradient controls check shared endpoint pixels, identical histograms, unique
full-field matches, and the limited information from a single column. A
grayscale control checks that two of the four palettes become identical under
Pillow's 8-bit grayscale conversion. This removes that grayscale representation
as a solution, without claiming equivalence under every definition of
luminance. These are construction oracles with known region locations; they
are not measured grayscale or masked-input model experiments.

The generator rotates gap sizes through chain positions. Nevertheless, the
small chosen set does not establish a psychometric curve or human visibility
threshold. Human agreement has not been measured.

## Corpus and dependence

| Family | Questions |
| --- | ---: |
| Exact matching | 48 |
| Component fill matching | 48 |
| Lightness | 64 |
| Chroma | 64 |
| Hue | 32 |
| Gradient matching | 16 |
| Same–different | 48 |
| Context | 80 |
| Small-region matching | 64 |
| RGB / HSL / OKLCH estimation | 16 each |
| **Total** | **512** |

These are correlated designed observations. Four references share one option
field, two response mappings share an equality image, matched interventions
share colors, and numeric formats share target images. Group IDs and explicit
condition metadata retain those relationships. Report paired outcomes and
finite-corpus counts rather than treating all responses as independent new
colors. The unchanged hue family should remain split into fixed and varying
lightness/chroma slices.

## Protocol and result interpretation

The small-region and context prompts change, so 0.4.0 has a new protocol
fingerprint. It requires fresh model requests; old scores never transfer.
Numerical grading retains its existing semantics. Similarity out of 100 is a
normalized OKLab distance, not an exact RGB recovery percentage or a human
visibility threshold. Reports should show raw distances, tolerance rates,
validity, and exact RGB recovery alongside it.

Historical 0.3.2 replay uses compatible source revision
`8fc558433146066b8e1ed9b44303689b2433478d`. New source intentionally rejects an
old protocol fingerprint. Frozen dataset descriptors, PNGs, sealed run
directories, and existing JSON exports are protected from modification.

The repair ticket records validation evidence and campaign state:
[fix-05-direct-color-controls](../tickets/fix-05-direct-color-controls.md).
The dataset must pass all offline gates and be committed before freezing its
descriptor or making paid requests. A fresh result report must name the
completed run and verified seal; the existence of this design document is not
evidence that a model campaign completed.

The subsequent [0.4.0 measured report](../results/fourth-pilot.md) records the
completed thirteen-configuration campaign: 6,656 fresh responses, a verified
full-cohort seal, and independent grading/accounting audit. Historical
observations remain unchanged.
