# plan-02: Harder color perception tasks (release 0.3.1)

- **Status:** Done (branch `feat-02-harder-tasks`, PR [#3](https://github.com/eob/colorbench/pull/3))
- **Machine:** `eob-dev2` (`/mnt/disks/data/colorbench`)
- **Harness:** muse
- **Session ID:** `01a09afb-e4fe-7220-874f-fb82eeeaed74`
- **Date:** 2026-09-13
- **Branch:** `feat-02-harder-tasks`
- **Scope:** Five harder-but-perceptual slices for a new 248-question release:
  separation sweeps with enforced position counterbalancing, same–different
  trials, surround-shifted matching, small-region matching, tighter numeric
  metrics. Then regenerate, adversarially review, and re-run.

## Why (pilot evidence)

Release 0.2.0 measured 13 models × 72 questions (`results/first-pilot.md`):
lightness 104/104, hue 104/104, chroma 103/104, gradient 101/104, matching
93/104, binding 91/104. Seven models scored 8/8 on matching and binding.
Separations sit ~10x above just-noticeable differences (lightness narrow
ΔL=0.10, chroma narrow ΔC=0.03, hue distractors ≥70°, gradient shifts ≥33%),
patches are large flats on a neutral surround, and every trial guarantees a
present difference. The matching/binding difficulty slices are additionally
confounded with answer position (wide→A/C, narrow→B/D).

## Frozen corpus design (chosen before any new model results)

Release 0.3.1 is a new 248-question corpus. Scores never transfer across
releases. All construction is deterministic; no RNG anywhere. The 0.3.0
corpus below was amended by the pre-run adversarial review (hue assignment,
rank rotation, samediff layout, gray checkerboard, hue offsets, gradient
cross); every amendment predates any model result.

| Family | n | Labels | Construction |
| --- | --- | --- | --- |
| matching | 48 | ABCD | 3 axes × 4 separations × 4 positions |
| binding | 48 | ABCD | paired 1:1 with matching (colors, positions, truth) |
| lightness | 16 | AB | 4 separations × 2 directions × 2 positions |
| chroma | 16 | AB | 4 separations × 2 directions × 2 positions |
| hue | 16 | ABCD | 4 separations × 4 positions |
| gradient | 8 | ABCD | unchanged 0.2.0 construction (continuity anchor) |
| samediff | 16 | AB | 8 same + 8 different, answer mapping crossed |
| context | 16 | ABCD | fixed per-position surrounds; 4 hues × 4 positions |
| smallmatch | 16 | ABCD | 2 layouts × 8 (axes cycle, positions rotate) |
| rgb/hsl/oklch | 16 each | numeric | 16 shared targets × 3 formats |

Total 248 questions; 216 unique images; 3224 responses at 13 models.

### Frozen separation levels (intended OKLCH, verified post-quantization)

- matching/binding lightness ΔL: 0.08, 0.04, 0.02, 0.01 (base L 0.65, C 0.05)
- matching/binding chroma ΔC: 0.025, 0.012, 0.007, 0.004 (base C 0.05)
- matching/binding hue ΔH: 35°, 15°, 8°, 4° (hue axis base C resolved
  deterministically from [0.05, 0.07, 0.09, 0.11], first all-distinct wins)
- lightness pairs ΔL: 0.10, 0.05, 0.02, 0.01 centered at 0.62; gray vs
  chromatic (C 0.06) follows a `(level+direction+position)%2` checkerboard
  (one gray + one chromatic per cell, 4/4 per position)
- chroma pairs ΔC: 0.06, 0.03, 0.015, 0.008 centered at C 0.055, L 0.65
- hue minimum distractor distance: 70°, 30°, 12°, 6°; distractors at
  offsets `[sep, 150, 250]` (exact minimum at every level); fixed vs
  varying follows a `(level+position)%2` checkerboard (2/2 per level and
  per position); varying jitter rotates `(j+2*pos+level)%4`
- samediff different-trials: ΔL 0.015 (×3), ΔC 0.008 (×3), ΔH 6° at C 0.09
  (×2); same hue and direction sequences in both blocks (each hue one A
  and one B); darker/less patch left follows `(i//2)%2`, decoupled from
  the answer
- context interiors: axis cycles lightness (Δ0.04), chroma (Δ0.012), hue
  (Δ15°); distractor sets rotate rank-2 `{−1,+1,+2}` / rank-3
  `{−2,−1,+1}` by `(hueIndex+position)%2`
- smallmatch: axis cycles lightness (Δ0.03), chroma (Δ0.010), hue (Δ10°);
  rank sets rotate by `(block+position)%2`
- matching/binding distractor sets rotate rank-2/rank-3 by
  `(cell+position)%2` (2/2 per cell, 6/6 per position); base hues follow
  `(cell+position)%8` (every position sees all eight hues)
- gradient direction fully crossed with position (forward items 01–04,
  reverse 05–08); the 0.2.0 direction-parity confound is removed, not
  preserved

### Frozen context surrounds (verified in-gamut 2026-09-13, pre-model)

A dark neutral `fromOklch(0.25, 0, 0)` = [34,34,34]; B light warm
`fromOklch(0.85, 0.03, 80)` = [216,204,184]; C saturated red-orange
`fromOklch(0.6, 0.15, 30)` = [202,87,71]; D saturated teal `fromOklch(0.6,
0.09, 220)` = [53,141,165]. The first teal candidate (C 0.12) fell outside
sRGB and was replaced. Context base hues are [25, 115, 205, 295].
Quantization survival of every smallest separation (ΔL 0.01, ΔC 0.004, ΔH
4° at C 0.09) was verified at all eight sweep hues before implementation.

### Distinctness resolver (deterministic, loud on failure)

Quantized 8-bit RGB of target vs every distractor must be pairwise distinct
(the PNG pipeline is lossless sRGB, so pre-render distinctness equals decoded
distinctness). On collision the builder tries deterministic nudges — hue
axis: base C in [0.05, 0.07, 0.09, 0.11]; lightness axis: base L in
[0.65, 0.63, 0.67, 0.60]; chroma axis: base C in [0.05, 0.06, 0.04] — and
records the resolved base in `design.intendedTargetOklch`. Exhaustion throws
at build time. Lightness/chroma ordering items additionally require decoded
gap ≥ 0.006. Silence (clipping) is never an option.

### New-family geometry and ground truth

- samediff: reuses the pair layout (two 84×84 patches, no target). Image text
  is mapping-neutral ("Are A and B the same color?"); the A/B→same/different
  mapping lives only in the external prompt (`samediff-sameA`,
  `samediff-sameB`), like numeric formats. Ground truth: decoded bytes equal
  ⟺ `design.same`; expected choice derived from equality + mapping.
- context: R is an 84×84 solid on neutral; each option is a 108×108 canvas
  with a 12px surround ring around an 84×84 interior. Surrounds are fixed per
  position (A dark neutral, B light warm, C saturated red-orange, D saturated
  teal) across all 16 items, so masked non-region pixels are identical and the
  leakage check stays tight. Recorded option regions are the 84×84 interiors;
  ground truth is interior-sha equality with R. A ring-probe check verifies
  surround pixels against `design.surround` per position.
- smallmatch-dot: R and options are 20×20 solids; ground truth is sha
  equality. smallmatch-frame: R and options are 84×84 3px outlines (interior
  painted page background, opaque); ground truth is full-field sha equality.
  Layout is recorded in `design.layout` (`dot`/`frame`); masked-pixel grouping
  becomes (family, direction, layout) so the leakage check stays exact.

### Counterbalancing (enforced in code, not just constructed)

The validator's completeness gate pins the pilot's lesson: for
matching/binding every (axis, separation) must appear at every position; for
lightness/chroma every (separation, direction) at both positions; for hue
every separation at all positions; samediff crosses same/different with both
mappings (overall A/B 8/8). Overall position balance per family is retained.

### Tighter numeric metrics (score formula unchanged)

`score` (0.2 ceiling) is kept so the method stays comparable. Added:
`tight_score` (0.05 ceiling, same formula), `within_bands` hit flags at
ΔE_OK ∈ {0.005, 0.01, 0.02, 0.05}, family `mean_tight_score` and band hit
rates over valid answers, and for RGB the share of valid answers within ±2
and ±5 LSB on all channels. Eight new targets join the eight frozen ones
(saturated boundary colors plus near-black/near-white); the first eight stay
byte-identical. The constant-gray baseline is recomputed over 16 targets into
a new evidence file; the 0.2.0 file is untouched.

## Frozen prompts (new families)

- samediff-sameA: `Do patches A and B have exactly the same flat fill color?
  Answer "A" for same and "B" for different. Compare the colored interiors,
  not labels or borders.` + choice trailer.
- samediff-sameB: same stem with `"B" for same and "A" for different`.
- context: `Which option, A, B, C, or D, has the same flat interior fill
  color as reference R? Each option sits on a different surround color;
  compare the interiors only, not the surrounds, labels, or borders.` +
  choice trailer.
- smallmatch: `Which swatch, A, B, C, or D, has the same color as reference
  R? The swatches are small; compare the colored regions, not labels or
  borders.` + choice trailer.

The shared choice trailer is unchanged:
`Return only a JSON object with one key, "choice", whose value is the
selected option letter.` In-image questions: samediff `Are A and B the same
color?`, context `Which interior matches R? Ignore the surrounds.`,
smallmatch `Which small swatch matches R?`.

## Explicit non-goals

- Gradient stop-hardening (kept near the 0.2.0 stimuli, but direction is
  now fully crossed with position — the continuity anchor was dropped when
  review found its direction-parity leak).
- Human agreement measurement (still `not_performed`; small-separation hue
  items especially need it before any threshold claim).
- Website import (external repo; in-repo deliverables are the sealed run,
  structured export, analysis JSON, and results doc).
- Any change to frozen 0.2.0/1.x artifacts, model catalog, or pricing.

## Adversarial review (2026-09-13, pre-paid-run)

Three independent read-only reviewers audited the branch at `405f672`
against the frozen 0.3.0 bytes. Every blocker below was re-verified by me
with independent tabulations before fixing.

**Stimulus (4 blockers, 3 majors, 8 minors):**

1. Blocker, confirmed: `(3n+1)%8` stride aliases position — each base hue
   lands at exactly one answer position (6/6) in matching/binding, 2/2 in
   smallmatch/hue. My "position cannot determine hue" comment was wrong:
   `n ≡ 3(h−1) (mod 8)` fixes `n mod 4`. Fix: 2-D hue assignment.
2. Blocker, confirmed: `[-1,+1,+2]` distractors put the target at rank 2/4
   on every trial (16/16 lightness) — "pick second-highest" scores 100%
   without R. Fix: rotate rank-2 `{-1,+1,+2}` / rank-3 `{-2,-1,+1}` sets,
   crossed with position. Rank-only knowledge then caps at 50%, and any
   correct answer still requires reference comparison or guessing.
3. Blocker, confirmed: samediff answer redundant with base-hue parity
   (16/16) and with signed left−right gap in different-trials (8/8). Fix:
   identical hue and direction sequences in both blocks (each hue gets one
   A and one B); lo-left decoupled via `(i//2)%2`.
4. Blocker, confirmed: lightness gray/chromatic variant predicts the answer
   (gray→A 8/8). Fix: `(level+dirIdx+pos)%2` checkerboard, aliasing only
   the forced 3-way interaction.
5. Major, confirmed: hue wide-level offsets `[d,d+120,d+240]` wrap at d=70
   (actual minimum ~50°). Fix: uniform offsets `[sep,150,250]`; tighten
   validator hue tolerance to `max(2.5°, 0.25×intended)`.
6. Major, confirmed: hue varying ⟺ B/D plus L/C-extremum keying. Fix:
   `(level+pos)%2` checkerboard and `(j+2*pos+level)%4` jitter rotation
   (the reviewer's `(j+pos+level)` would still key correct-L rank to
   varying-ness; the `2*pos` term spreads all four L-ranks across the
   varying cells, each twice).
7. Major, confirmed: gradient direction ⟺ position parity (inherited 0.2.0
   confound). Fix: rebuild gradient with direction × position fully
   crossed instead of documenting it — the continuity anchor is not worth
   a known leak, and cross-release comparisons are invalid anyway.
8. Minor: context/smallmatch axis beats are already optimal given cell
   counts (`k%3 ≡ (block+pos)%3`); no change.
9. Minor: ordering-hue coupling — fixed by the 2-D hue assignment.
10. Minor: filenames/task IDs encode answers (harness-internal; providers
    send bytes+prompt only, pinned by test). Noted for blind releases.
11. Minor: matching/binding pairing halves effective N for position
    inference — will state in analysis.
12. Minor: frame ring color never asserted vs decoded pixels — adding a
    browser ring-pixel test.
13–14. Minors: surround-induction and near-hue threshold caveats — already
    gated on unmeasured human agreement; holding the line in write-ups.

**Grader (1 major, 5 minors):** masked-group bypass via unconstrained
direction/layout (fix: per-family whitelist); scorecard tight-metric
range checks; two KeyError-vs-ValueError clean rejections; samediff
same-branch axis validation; separation-tolerance looseness accepted as
quantization backstop (TS construction tests pin gaps tightly).

**Release (2 majors, 6 minors):** matching-42/binding-42 hue-8 pair
decodes a 4.99° nearest gap (fix: decoded-gap fidelity checks for
exact-match families + gap-aware resolver, riding the rebuild);
"nine-family" string in finalize.py (fix: count-agnostic wording);
freeze-commit mixing (committed note; 0.3.1 freeze will be pure);
unpinned mock coverage (adding FAMILIES-parametrized test);
tests/evidence pointer; budget-basis + output-cap watch note;
GRADING_VERSION "2" spans both releases (documented, not churned).

**Rebuild decision:** blockers 1–4 require new pixels, so the corpus is
rebuilt and refrozen as **0.3.1** (0.3.0 was never measured or published;
its descriptor stays in history). No model results existed before any fix,
so all amended levels remain pre-registered. Findings 5–7 and every minor
fix ride the same rebuild.

## Provenance note

The dataset-freeze commit `9885454` also carries the staged deletion of
`src/specimens.test.ts` (41 lines), whose 72-question assertions were
superseded by `src/harder-design.test.ts`. The release gate verifies only the
manifest bytes and the `dataset/colorbench-v0.3` census, so the extra path
does not affect release identity; `validate:release` passes. Recorded here so
the commit's mixed content is not mistaken for a data change.

## Implementation checklist

TS: types (families, direction union, ring/interior fields), prompts,
specimens (sweeps, resolver, new families, +8 numeric targets), render
(ring paint, region/canvas split, ground-truth branches, version),
specimen/render tests. Python: protocol (families, labels, prompts,
NUMERIC_SCORING), prompts.json, evaluator (tight_score, within_bands,
dataclass), statistics (tight/band/LSB metrics), validate_dataset (new
branches, counts, crossing checks, layout grouping, ring probes),
release 0.3.0 descriptor + DEFAULT_RELEASE + scripts + versions, tests,
constant-gray 0.3.0 evidence, docs (methodology, README), results doc.

## Validation gate matrix

| Gate / Command | Base commit | Result |
| --- | --- | --- |
| `bun run test` (main baseline) | `9a91fd4` | 198 pytest; 10 bun / 386 assertions; typecheck clean |
| `bun run validate:release` (0.2.0 baseline) | `9a91fd4` | valid, 72 tasks |
| `bun run test` (0.3.0 implementation) | branch head | 227 pytest; 20 bun / 1133 assertions; typecheck clean |
| `bun run render` + `validate:candidate` | branch head | 248 questions / 216 images; gate valid, zero errors |
| Visual review (rendered PNGs) | branch head | context, smallmatch dot+frame, samediff inspected; frame footer fixed |
| `bun run validate:release` (0.3.0) | `9885454` + code | valid, 248 tasks |
| `bun run benchmark:mock` (0.3.0 smoke) | branch head | completes; new metric fields flow through scorecards |
| Adversarial review (3 agents) | `405f672` | 4 blockers + 4 majors + 19 minors, all confirmed empirically |
| `bun run test` (0.3.1 rebuild) | branch head | 244 pytest; 29 bun / 1413 assertions; typecheck clean |
| `bun run render` + `validate:candidate` (0.3.1) | branch head | 248/216; gate valid, zero errors |
| Frozen-byte re-audit (0.3.1) | `96ee427` | hue×pos 0 leaks; ranks 24/24, 8/8, 4/4; samediff 8/8; gray 4/4/4/4; hue-min ±3°; gradient 8/8; gaps in tolerance |
| `bun run validate:release` (0.3.1) | `96ee427` + code | valid, 248 tasks |
| `bun run benchmark:mock` (0.3.1 smoke) | branch head | completes |
| Paid campaign (13 models × 248) | `49f7df5` | 3,224/3,224, zero invalid, $21.49 of $25 |
| `finalize --scope full` + `--verify` | `0a7bdea` | sealed; replay clean |
| `analyze_pilot.py` + `second-pilot.md` | `0a7bdea` | ceiling broken; gradients clean; samediff bias found |
| Final `bun run test` + frozen check | HEAD | 244 pytest; 29 bun; typecheck; 4 frozen paths verified |

## Red evidence

Python protocol surface, 15 failed / 5 passed (5 passes are rejection tests
that fail closed on unknown families today):

```text
FAILED test_harder_choice_families_use_only_arbitrary_option_ids[samediff]
FAILED test_harder_choice_families_use_only_arbitrary_option_ids[context]
FAILED test_harder_choice_families_use_only_arbitrary_option_ids[smallmatch]
FAILED test_harder_family_prompts_are_byte_frozen
FAILED test_tight_score_and_bands_measure_near_exact_reconstruction
FAILED test_band_hit_rates_cover_valid_answers_and_rgb_lsb_rates
FAILED test_samediff_accepts_matching_equality_and_mapping
FAILED test_samediff_rejects_wrong_choice_flag_or_mapping (x3)
FAILED test_context_checks_interior_match_and_surround_probes
FAILED test_smallmatch_accepts_dot_and_frame_layouts
FAILED test_hue_thresholds_follow_the_recorded_minimum_separation
FAILED test_complete_counts_and_crossing_rules_pin_the_248_question_release
FAILED test_lightness_decoded_gap_must_match_the_recorded_separation
```

Representative causal signatures: `ValueError: Not a choice family:
samediff`, `ValueError: Unknown task prompt: samediff-sameA`, `KeyError:
'tight_score'`, `AttributeError: module 'baseline.validate_dataset' has no
attribute 'COMPLETE_FAMILY_COUNTS'`. Each fails for absence of the new
surface, not for fixture syntax.

Rebuild Red (adversarial findings): 8/8 new TS confound audits fail
(hue×position, rank rotation, samediff hue/gradient, gray checkerboard,
hue offsets, varying checkerboard, gradient cross, exact-match gaps) while
all 8 prior design tests stay green; 5/5 new Python gate tests fail
(direction/layout whitelist, samediff axis, exact-match gaps, scorecard
tight checks, replay KeyError). The 12 mock-family pins pass unmodified.

TypeScript corpus surface, 13 failed / 0 passed after de-vacuuming two
passes (empty families trivially balanced; pair layout accidentally fits
samediff). All fail on absent families, counts, crossing, or paint fields.

