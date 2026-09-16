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
- **PR:** https://github.com/eob/colorbench/pull/5
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
- [x] Authoritative ticket committed on main; feature branch and draft PR #5
  created; PR linked from this main ticket.
- [x] Construction contract fixed at 512 questions (table below); pairing
  and condition metadata shared with the implementation lanes.
- [x] Add failing decoded-control/construction checks and capture verbatim
  Red evidence under `tickets/evidence/fix-05-*`.
- [x] Implement generator, renderer, prompt, and gate changes.
- [x] Verify Red→Green and reversion against frozen 0.3.2 inputs; inspect
  representative actual PNGs, including all changed geometries/gradients.
- [x] Run complete Python/TypeScript/typecheck gates and independent controls.
- [x] Document/freeze 0.4.0 and verify historical replay at its pinned source.
- [ ] Run and resume the new 13-configuration campaign under an explicit cap;
  record task count, projected cost, cap, command, and run ID before dispatch.
- [ ] Seal/audit new results; write the repair explanation and measured report.
- [ ] Apply simplifyfu/comment review, sync main, finish PR and recovery memo.

### Construction counts and metadata

| Family | Questions | Construction |
| --- | ---: | --- |
| Matching / binding | 48 each | Existing paired fields and four references |
| Lightness / chroma | 64 each | Four five-color chains × four adjacent edges × two directions × two placements |
| Hue | 32 | Existing fixed/varying L/C and four references |
| Gradient | 16 | Four palettes × four references; shared endpoints/histograms, two independent interior swaps |
| Same–different | 48 | Six endpoint pairs × four pairings × two response mappings |
| Context | 80 | Four palettes × neutral plus four surround rotations × four references |
| Small regions | 64 | Four palettes × filled20/filled84/outline3/outline12 × four references |
| RGB / HSL / OKLCH | 16 each | Existing sixteen shared numeric target images |

All specimens record `design.controlVersion="0.4.0"`. Ordering records
`comparisonSetId`; equality records `pairSetId` and `mappingPairId`, reusing
identical PNGs and group IDs across response mappings. Context/small record
`interventionSetId`, `condition`, and a common group ID across conditions for
one reference; `optionSetId` remains unique per condition. Small geometry
records `layout`, `sizePx`, and `strokePx`; context records actual surrounds.

The equal-output-color one-patch Bayes ceiling is 50% for equality and 62.5%
for ordering chains, conditional on prompt and including all visible
nonmasked pixels. Ordering gap sizes rotate through chain positions. New
separation tables remain descriptive rather than psychometric thresholds.
Gradient construction also limits any single-column rule to at most 50%; two
palettes are intended to have identical 8-bit grayscale progressions across
all options. Verify those properties on encoded PNGs before freezing.

Historical cost scaling projects approximately $44.6 for 512 ×13 requests.
Use an explicit **$65 campaign ledger cap**, concurrency6, the existing13
configurations, and run ID `pilot-20260916` after the release is frozen. This
is a task planning cap, not a guaranteed provider invoice amount. Stop and
inspect any budget exhaustion; never silently raise the cap or claim a
partial run is complete. No paid requests have started at this checkpoint.

### Implementation ownership

- Coordinator `/root`: renderer, prompts, matched-render tests, documentation,
  integration, release freeze, paid campaign, result interpretation, commits.
- `review_layoutbench`: `src/specimens.ts`, generator/construction TS tests.
- `review_colorbench`: decoded gate and direct-control Python module/tests.
- `review_borderbench`: current version defaults, historical-artifact guard,
  its tests, and pinned historical replay.

Agents share this checkout. No subagent branch switches, commits, shared-file
edits outside ownership, or paid model calls. Root checkpoints finished units
on the remote feature branch.

### Renderer checkpoint — 2026-09-16

New tests reproduced four failures on the old renderer/prompts:

```text
0 pass
4 fail
4 expect() calls
```

The failures were missing explicit outline wording, ignored84px size,
ignored12px stroke, and hardcoded surrounds. Evidence is in
`tickets/evidence/fix-05-render-red.log`. Fixes use recorded geometry/surrounds
and fixed label anchors; all small conditions share external and image text.
An isolated source reversion reproduced the same four failures in
`fix-05-render-reversion.log`; restored-source renderer tests pass in
`fix-05-render-green.log`. No shared files were reverted during parallel work.

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
| New construction regressions | 0.3.2 then candidate | Expected Red, then Green; same failure under reversion | Pass; generator, renderer, decoded, frozen, analysis logs |
| `bun run test` | Feature branch | Python, TypeScript, typecheck pass | Pass: 308 Python, 46 TS, typecheck |
| Candidate decoded validation | Candidate manifest | Prompt/pixel/unique-answer and new controls pass | Pass: 512 tasks, 456 images; independent pixel review |
| Immutable artifacts check | Main vs feature | Historical dataset/run/seal bytes unchanged | Pass: 22 protected paths |
| Historical finalization replay | Published 0.3.2 source pin | All 3,432 grades/seal reproduce | Pass: byte-identical export |
| 0.4.0 release validation | Frozen dataset commit | Exact count, image inventory, fingerprints pass | Pass; offline mock 3 tasks × 13 configurations also passes |
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

- **2026-09-16 14:38 UTC:** Invocation 2 resumed successfully from clean
  checkpoint commit `f3224a8ca4f162649b4ade6a5605e5af2165885d` (pushed).
  Active PID `4123274`, root tool session `28522`; same console log, run ID,
  full cohort, concurrency 6, and $65 cumulative cap. All 1,470 prior results
  were loaded, including Luna's retained incomplete `colorbench-oklch-04`
  answer (4,096 output tokens). Do not start a duplicate active process.

- **2026-09-16 14:37 UTC:** Gracefully drained and closed invocation 1 to
  push a consistent raw checkpoint. Exit 130 is the intentional SIGINT,
  not a provider failure. Summary status `interrupted`; SQLite WAL closed;
  1,470 completed results = 1,470 attempts across all 13 models, including
  one retained invalid answer. Ledger spending is $10.7205501. No separate
  infrastructure error remains pending. Committing raw files and resuming
  the same run ID preserves all prior observations and cumulative budget.
  Previous PID `4058359` / tool session `86151` is finished; use the newest
  process entry above once resumed, never restart a second live process.

- **2026-09-16 14:13 UTC:** The campaign remains active. Latest branch CI
  passed twice, but an earlier intermittent new browser-test failure was
  investigated rather than dismissed. Forced Bun garbage collection reproduced
  loss of the active Chromium transport (5/10 failures). The new outline probe
  now owns Playwright in a short Node subprocess; the same forced-GC condition
  passes 30/30 times, and error/timeout cleanup works. The five-second test
  deadline and pixel assertions remain. Full TS suite passes 46 tests / 7,662
  assertions and typecheck. See `fix-05-render-ci-review.md` and adjacent logs.
  This is test-only; the paid dataset/protocol fingerprint is unchanged.
  Historical report links now name its pinned 0.3.2 methodology/replay source.

- **2026-09-16 14:00 UTC:** Paid campaign is running. Run creation time
  `2026-09-16T13:59:47.704119+00:00`; clean source
  `8aac23361559574e7b1d554fd3499055b4a01f2d`, recorded dirty flag `false`.
  Process PID `4058359`, root tool session `86151`, console log
  `/tmp/colorbench-fix05-campaign.log`. Initial snapshot: 16/6,656 completed,
  ledger $0.1812; full 512-task identity and all 13 configurations verified.
  Do not start another process while this one is active. Progress snapshots
  live in `results/runs/0.4.0/pilot-20260916/summary.json`; the SQLite ledger is
  durable. Raw run files remain unsealed until completion and reconciliation.

- **2026-09-16 13:58 UTC:** Frozen dataset commit
  `c14b9c971bd1fbe1a0126a2683ba4df8b0eeaf6c`; descriptor
  `releases/0.4.0.json`. Dataset fingerprint
  `3c6b248bfc25f4810c0083bbc5af3c5905fb1000795b21fdd0a57969a7aa3bc0`;
  protocol fingerprint
  `78be5960423e0ea7b850ffb5a5c07dbb41a4658d6c89dd8a43e9dc08c76ab502`.
  Release gate passes; all 22 historical paths remain unchanged. Offline
  `mock-fix05-smoke` covers three tasks per configuration (39 responses),
  correctly reports partial coverage, and is excluded from publication.
  All 13 loaded model configurations exactly match the prior campaign;
  required credentials are present. No paid requests yet.

- **2026-09-16 13:56 UTC:** Implementation and independent pixel/analysis
  reviews pass. Full suite: 308 Python tests, 46 TypeScript tests, 7,661 TS
  assertions, typecheck. Initial integration failures were stale prompt
  expectations and uppercase fixture IDs; fixed tests without relaxing gates.
  Simplifyfu review found no unnecessary abstraction or unresolved issue.
  Candidate manifest SHA256:
  `0271b7d47a79ec8988e2edd11c986555e135419695c51d682e1981aa093addc5`.
  All 176 retained task images are pixel-identical to 0.3.2. Gradient bounds,
  all 56 single-patch checks, and every matched intervention pass independently.
  Analysis now reports matched condition pairs, semantic mapping consistency,
  fixed/varying hue, and exact/tolerance RGB recovery. Historical aggregates
  reproduce exactly. Evidence is under `tickets/evidence/fix-05-*`.

- **2026-09-16 13:34 UTC:** Created feature branch after publishing the ticket
  on main; no implementation changes yet.

- **2026-09-16 13:32 UTC:** Started by codex on eob-dev2, session
  `01a09da1-c62d-7b60-8bc1-9fd70414ed46`; main clean at `a91acaa`.

## Recovery memo

- **Verified working:** Frozen 0.3.2 replay; repaired 512-task candidate;
  complete tests, decoded controls, independent pixel/analysis review.
- **Pending:** Finish the active paid campaign, then seal/audit,
  measured report, PR finalization.
- **Resume:** Read this ticket and PR; `git status`, then `bun run test`.
  Check run metadata before launching any paid request; resume a recorded run
  rather than creating a duplicate campaign.
- **Next action:** Monitor the active process above. If it exits early, inspect
  the status and infrastructure errors before resuming with this command:

```bash
.venv/bin/python -m baseline.runner --release 0.4.0 \
  --config config/models.all.json --run-id pilot-20260916 \
  --concurrency 6 --budget-usd 65
```

The raw run directory is `results/runs/0.4.0/pilot-20260916`. Resume only with
this same command and run ID. A successful process exit can still mean partial
or budget-exhausted work: require summary status `complete` and all 13 models
at 512 completed tasks before sealing. Commit closed raw artifacts first,
then finalize with `--scope full`, verify, export, independently audit, and
analyze. Do not alter the dataset or protocol during the campaign.
