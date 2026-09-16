# fix-05-direct-color-controls: Repair direct-color task controls

- **Status:** In Progress
- **Assignee:** Edward Benson
- **Branch:** `fix-05-direct-color-controls`
- **Base:** `a91acaa8ac248136e7278531ff844993d6974cec` (`main`)
- **Workspace:** `/mnt/disks/data/colorbench` (in-place branch; repository has no additional worktrees)
- **Machine:** `eob-dev2`
- **Harness:** `codex`
- **Session ID:** `01a09da1-c62d-7b60-8bc1-9fd70414ed46`
- **Coordinator:** `/root`
- **PR:** Pending
- **Target release:** `0.4.0`; immutable historical release `0.3.2` retained

## Goal and authorized scope

Repair the experimental controls in the existing direct-color benchmark, then
validate and measure the new frozen cohort. Direct hue matching and numeric
estimation already ask the intended questions. Retain the ColorBench name;
object reasoning, new applied-design task families, and a branding change are
out of scope. Keep rollout discovery links in their existing state.

The user requested these focused repairs, ticketfu documentation before code,
and a new feature branch that another agent can resume. Earlier authorization
to rerun revised benchmarks remains applicable. Deliver code/data/results on
this feature branch with a reviewable PR; do not silently replace historical
results or announce the new release through website discovery links.

## Evidence baseline

- Release `0.3.2`, `results/runs/0.3.2/pilot-20260914`: 264 questions,
  232 unique PNGs, 13 configurations, 3,432 final responses.
- Dataset commit: `09b0dd9afacb70364c52ae22cb21bd2918534c59`.
- Compatible published source: `8fc558433146066b8e1ed9b44303689b2433478d`.
- Final-results SHA256:
  `7d373266ef76a5aa93879dc2faf869ceca9a413d4ed3bb21610f0de1bb66d924`.
- Research and runnable controls:
  https://github.com/eob/brain/blob/09a7c9033db7e738977cc1f7536de51aae61e368/discussions/colorbench-publication-review-2026-09-16.md
- Existing `fix-04-small-region-prompt.md` is incorporated into this repair.

Locally reproduced baseline control output (2026-09-16):

```text
{'chroma': [16, 16], 'gradient': [8, 8], 'lightness': [16, 16], 'samediff': [14, 16]}
```

The ordering rules read patch A alone; the equality rule reads B alone; the
gradient rule reads only an 8-bit grayscale left endpoint. These are posthoc
construction diagnostics, not evidence that models used those strategies.
Eight outline cases also exclude borders in the external prompt while scoring
colored outlines. Independent replay found no material scoring defect.

## Exact repair contracts

1. **Outline wording:** explicitly include colored outlines and exclude labels
   and neutral surroundings. One compatible external prompt covers all
   small-region geometries. Update the protocol identity, never old prompts.
2. **Gradient interior:** options within each field share both endpoints and
   their color histogram but differ in interior arrangement. Every option is R
   once. Add independent gradient palettes beyond the old two fields. The
   decoded endpoint-only oracle must be at chance while full fields have one
   unique correct answer. Keep reference-masked balance intact.
3. **Same/different:** construct `(c,c), (c,d), (d,c), (d,d)` blocks, cross
   identical image pairs with both semantic answer mappings, and vary base
   colors/axes. Within each prompt, either single patch's decoded-color
   distribution must be identical for same and different outcomes. Both
   constant semantic and optimal single-patch controls must be at chance.
4. **Lightness/chroma:** vary absolute centers; reuse interior colors with
   partners above and below them under the same prompt. Cross requested
   direction and A/B placement. Each patch alone must be insufficient for
   perfect prediction; document the optimal single-patch ceiling. Exact
   marginal balance at chance is not generally possible for finite ordered
   scalar values, so do not impose the equality invariant on ordering tasks.
5. **Context:** repeat identical target/options/positions on neutral and
   colored surrounds, with surround assignment crossed independently where
   feasible. Use identical wording within pairs and record control-group IDs.
   Report paired effects for the actual intervention, without human color-
   constancy or psychometric-threshold claims.
6. **Size/stroke:** repeat identical color fields across small/large filled
   squares and thin/thicker outlines. Hold palette, axis, reference, positions,
   and wording constant within geometry comparisons; cross every reference.
   Treat filled-size and outline-width comparisons separately.
7. **Controls and reporting:** add decoded-image regression checks for these
   invariants, reject collapsed or ambiguous fields, retain the 42-group-style
   whole-image reference mask guarantee, distinguish fixed/varying hue,
   and report numeric raw/tolerance errors with similarity clearly labeled.
   Add a grayscale diagnostic where relevant; do not require grayscale failure
   in intentional lightness tasks or claim an oracle is a model ablation.
8. **Versioning and rerun:** freeze a new dataset and protocol as 0.4.0 after
   offline gates pass; run fresh requests for the shared new cohort, retain
   invalid answers, seal/replay/audit results. Historical datasets, protocols,
   run records, seals, and published 0.3.2 artifacts stay byte-identical.

Numeric text-only conversion experiments, broad model grayscale ablations,
human agreement studies, and optional new color-manipulation questions are
follow-up experiments, not prerequisites for these focused repairs. No claims
that those experiments were performed may appear in the new report.

## Execution plan and ownership

- [x] Read ticketfu/workfu, inspect existing tickets, verify clean baseline.
- [ ] Commit/push this authoritative ticket on main; create matching branch
  and draft PR; link PR back from the main ticket.
- [ ] Record concrete new construction counts and grouping metadata before
  implementation; keep total corpus small enough for a practical rerun.
- [ ] Add failing decoded-control/construction checks and capture verbatim
  Red evidence under `tickets/evidence/fix-05-*`.
- [ ] Implement generator, renderer, prompt, and gate changes.
- [ ] Verify Red→Green and reversion against frozen 0.3.2 inputs; inspect
  representative actual PNGs, including all changed geometries/gradients.
- [ ] Run complete Python/TypeScript/typecheck gates and independent controls.
- [ ] Document/freeze 0.4.0 and verify historical replay at its pinned source.
- [ ] Run and resume the new 13-configuration campaign under an explicit cap;
  record task count, projected cost, cap, command, and run ID before dispatch.
- [ ] Seal/audit new results; write the repair explanation and measured report.
- [ ] Apply simplifyfu/comment review, sync main, finish PR and recovery memo.

Initial read-only lanes: `review_layoutbench` proposes comparison balancing;
`review_borderbench` maps protocol/release compatibility; coordinator handles
ticket, scope, and integration. Implementation ownership will be recorded
before parallel edits. Agents share this checkout; no branch switching by
subagents, no shared-file edits without coordination, no independent paid runs.

## Files and release boundaries

Expected implementation: `src/specimens.ts`, `src/prompts.ts`, `src/render.ts`,
`src/types.ts` if needed, `baseline/prompts.json`, decoded validation/tests,
release/CI commands and documentation. Candidate rendering goes to
`dataset/candidate-rendered`; only a fully validated new dataset is copied to
`dataset/colorbench-v0.4.0` and committed before its release descriptor.

The protocol fingerprint includes prompts and implementation bytes. Historical
0.3.2 replay may therefore need its compatible source checkout after the new
prompt lands. Preserve this boundary rather than weakening fingerprint checks
or pretending the old run used the new protocol.

## Validation gate matrix

| Gate | Baseline/revision | Required result | Status |
| --- | --- | --- | --- |
| New construction regressions | 0.3.2 then candidate | Expected Red, then Green; same failure under reversion | Pending |
| `bun run test` | Feature branch | Python, TypeScript, typecheck pass | Pending |
| Candidate decoded validation | Candidate manifest | Prompt/pixel/unique-answer and new controls pass | Pending |
| Immutable artifacts check | Main vs feature | Historical dataset/run/seal bytes unchanged | Pending |
| Historical finalization replay | Published 0.3.2 source pin | All 3,432 grades/seal reproduce | Pending |
| 0.4.0 release validation | Frozen dataset commit | Exact count, image inventory, fingerprints pass | Pending |
| New finalization and independent audit | New run source checkpoint | Complete shared cohort, raw-answer replay, no grade drift | Pending |

## Decisions and durable findings

- Keep direct isolated-color questions. No object reasoning or rename.
- A prompt change requires new model observations and a new protocol identity.
- A high numeric similarity score is not an exact-reconstruction percentage.
- Oracle controls assess construction; they do not identify model strategies.
- Four references share a field, so group-aware analysis must retain their
  dependence. Matched interventions need explicit pairing metadata.
- Do not transfer old scores into 0.4.0 or compare releases as model progress.

## Handoff & takeover log

- **2026-09-16 13:32 UTC:** Started by codex on eob-dev2, session
  `01a09da1-c62d-7b60-8bc1-9fd70414ed46`; main clean at `a91acaa`.

## Recovery memo

- **Verified working:** Frozen 0.3.2 grades and numeric math replay; review
  controls above reproduce; main initially clean.
- **Pending:** All implementation, new release, and campaign work.
- **Resume:** Read this ticket and PR; `git status`, then `bun run test`.
  Check run metadata before launching any paid request; resume a recorded run
  rather than creating a duplicate campaign.
- **Next action:** Push the authoritative ticket, create the matching feature
  branch and draft PR, then establish Red tests and exact construction counts.
