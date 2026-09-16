# fix-04-small-region-prompt: Clarify colored outlines in the next protocol

- **Status:** Completed
- **Assignee:** Edward Benson
- **Found:** 2026-09-14 publication review of 0.3.2
- **Current handling:** Resolved and freshly measured in 0.4.0; historical 0.3.2 limitation preserved
- **PR:** https://github.com/eob/colorbench/pull/5
- **Merged:** `2026-09-16T18:01:15Z` by `eob` into `main`
- **Merge commit:** `32349bbed203d6e02c6d8ecbbdded840ff47b45c`

The replacement prompt now explicitly includes colored outlines and excludes
labels and neutral surroundings. It is shared by all four matched geometries.
Regression tests and decoded geometry controls pass. All thirteen models
completed the fresh 512-question cohort, including all 64 small-region tasks.
The sealed results and independent audit pass. The frozen 0.3.2 inputs
remain unchanged; release and campaign evidence are tracked in
[fix-05-direct-color-controls](fix-05-direct-color-controls.md), PR #5.

The historical 0.3.2 small-region external prompt says "compare the colored regions,
not labels or borders." Eight specimens score colored square outlines. Their
image footer explicitly says "Compare the colored outlines. Labels and neutral
areas are not part of the color." The visible task remains answerable, but
models may need to resolve these differently phrased instructions.

The original repair requirement was to replace the external exclusion with "ignore
labels and neutral surrounding UI" or otherwise explicitly include colored
outlines. Keep the same shared smallmatch prompt for both geometries and test
that the text describes each rendered task consistently.

Do not mutate the frozen 0.3.2 prompts or reinterpret its measured performance
as a pure size effect. This wording change affects inference input and must
receive a new protocol identity and new model requests when adopted. A
wording change alone would not isolate a geometry effect. Release 0.4.0 adds
matched palette, position, and prompt controls for size and stroke comparisons;
human agreement remains unmeasured.

## Closure and recovery

PR #5 incorporates this repair and is verified merged. The completed campaign
is sealed at `results/runs/0.4.0/pilot-20260916`; its measured report is
[fourth-pilot.md](../results/fourth-pilot.md). No additional model requests or
benchmark changes remain. Follow the offline replay instructions in that
report and the recovery metadata in [fix-05](fix-05-direct-color-controls.md).
The remote `fix-05-direct-color-controls` branch remains available at
`a243f42c1ae966dbc0e63b9b51f17646a83f69ac`; do not resume or alter the sealed run.
