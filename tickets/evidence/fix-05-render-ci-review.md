# Bounded rendering-test transport repair — 2026-09-16

Only `src/matched-render.test.ts` and this evidence were changed in this lane. Renderer code, prompts, protocol, dataset files, dependencies, and model requests were not changed. The existing five-second Bun test deadline remains in force.

## Observation and cause

The failing GitHub Actions run [35105506316](https://github.com/eob/colorbench/actions/runs/35105506316) and passing run [35105501198](https://github.com/eob/colorbench/actions/runs/35105501198) share commit `8aac23361559574e7b1d554fd3499055b4a01f2d`. The failed run timed out in the new outline-width test; the other 45 TypeScript tests passed.

Repeating the unmodified test locally reproduced the same timeout during the second `page.setContent` call. Browser/API instrumentation showed that the first document was complete and its font was already loaded. Chromium then reported `Connection terminated while reading from pipe`, `Could not write into pipe`, and exited with code zero before Playwright's pending call timed out. A slower font or insufficient five-second limit therefore does not explain this observation.

Forcing `Bun.gc(true)` immediately before the second content replacement reproduced pipe loss on every second browser launch: five failures in ten repetitions. The temporal cause is garbage collection interacting with browser-process transport lifetime after a previous browser has exited. We did not inspect or patch Bun's internal descriptor ownership; identifying its exact internal implementation defect is outside this repair.

## Bounded remedy

The existing test now passes its two generated HTML documents to a short Node subprocess that owns Playwright and Chromium. It uses the same installed Playwright version, Chromium binary, viewport, sRGB flag, document-loading operation, and canvas pixel probes. The parent Bun test still checks the 84px geometry and expects the 3px outline's inner probe to be neutral and the 12px outline's probe to contain the target color.

The child closes Chromium in `finally`, returns a nonzero exit when the probe fails, and has a four-second process deadline inside the unchanged five-second test deadline. No retry or increased deadline masks a failure. Node is already available in this workspace and GitHub Actions environment; no dependency or global test-runner migration was introduced.

Existing rendering tests that still create Playwright browsers directly in Bun retain the inherited transport exposure. This patch fixes only the newly added test identified by CI, not Bun or all browser tests.

## Validation

| Check | Result | Evidence |
| --- | --- | --- |
| Original unmodified test, 50 repetitions | Same timeout reproduced; subsequent spawn failures were collateral errors | `fix-05-render-ci-repeat-red.log` |
| Browser/document phase tracing | First document complete/fonts loaded; DevTools pipe lost during second replacement | `fix-05-render-ci-state.log` |
| Original harness with forced GC, ten repetitions | 5 pass / 5 fail; Chromium pipe closed immediately after collection | `fix-05-render-ci-gc-red.log` |
| Concurrent A/B: original harness with GC before second replacement | 5 pass / 5 fail | `fix-05-render-ci-ab-old.log` |
| Concurrent A/B: isolated probe with GC while the child browser is active | 30 pass / 0 fail; boundary marker verified in every trial | `fix-05-render-ci-ab-new.log` |
| Missing-canvas fault injected in a temporary copy | Expected failed test, child exit 1, Chromium gracefully closed | `fix-05-render-ci-probe-failure.log` |
| Nonterminating child probe injected in a temporary copy | Expected failed test in 4.16s, Chromium gracefully closed | `fix-05-render-ci-probe-timeout.log` |
| `bun test src` | 46 pass / 0 fail / 7662 assertions | `fix-05-render-ci-suite-green.log` |
| `bun run typecheck` | Pass | Terminal execution recorded in task handoff |

All test-owned browser and child processes exited; no browser process remained after the checks. Environment: Bun 1.3.14, Node v22.22.3, Playwright 1.63.0, Chromium headless shell 153.0.8010.12.

## Reproduce the causal comparison

Run `python3 tickets/evidence/fix-05-render-ci-reproduce.py` to create temporary test variants from the original committed test and current repaired test. The old variant collects while Chromium is active immediately before the second document. The new variant signals the parent after its first canvas probe; the parent collects while the child browser is active before the second document. The 100ms pause exists only in this diagnostic variant to make that boundary observable; production code adds no sleep.

Then run these two commands concurrently:

```sh
DEBUG=pw:api,pw:browser bun test /tmp/colorbench-render-ci-reversion/matched-render.test.ts --test-name-pattern 'outline width' --rerun-each 10
DEBUG=pw:api,pw:browser bun test /tmp/colorbench-render-ci-node-active/matched-render.test.ts --test-name-pattern 'outline width' --rerun-each 30
```
