# fix-04-small-region-prompt: Clarify colored outlines in the next protocol

- **Status:** Implemented and freshly measured in 0.4.0; PR #5 ready for review
- **Assignee:** Edward Benson
- **Found:** 2026-09-14 publication review of 0.3.2
- **Current handling:** Disclosed in methodology and measured-results report

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
factorial geometry comparison would also need matched axis/hue cells and
human agreement rather than a wording change alone.
