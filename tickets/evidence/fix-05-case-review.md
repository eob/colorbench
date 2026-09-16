# ColorBench 0.4.0: independently verified post-hoc case illustrations

Source commit: `a8868c33d3270635a58046716286303418649613`. Run: `results/runs/0.4.0/pilot-20260916`.

Post-hoc illustrations; selected after seeing outcomes. Each condition has one independent response per model. These examples do not establish repeatability or a general causal mechanism.

## Recommended three illustrations

1. **Size helps, thickness can still hurt on the same palette.** Claude Opus 5 answers D to 20px fills (task smallmatch-01), A to 84px fills (-05), A to 3px outlines (-09), and D to 12px outlines (-13). A is correct in all four. The reference, option colors, centers, external prompt and truth stay fixed. The outlined squares retain an 84px outer width. In the complete Opus cohort, fills improve from 7/16 to 16/16, while outlines decline from 12/16 to 8/16. This selected palette illustrates both directions; it does not establish a monotonic perceptual rule.

2. **Same fills, different surroundings, different answer.** Muse Spark 1.2 answers A correctly on neutral context-01, then C incorrectly on surround-0 context-05. Both retain reference/option A RGB (191,131,126), every option fill, geometry and external prompt. The only image changes are the four surrounding rings. The other three cyclic rotations (-09/-13/-17) receive B/B/D, all wrong. Do not say it always follows a particular surround color: the selected answers do not support that. Complete-cohort neutral versus surround-0 accuracy is 12/16 versus 3/16 for this model.

3. **An unchanged letter can mean a changed judgment.** GPT-5.6 Sol replies A to both samediff-27 and samediff-28, which use the exact same PNG of two identical RGB (168,155,212) patches. Task 27 maps A to same, so the answer is correct; task 28 maps A to different, so it is wrong. Only the external answer-mapping prompt changes. This is one of Sol’s 2/24 semantically inconsistent mapping pairs. Independent requests confound a mapping effect with ordinary response variability; the observed inconsistency itself is exact.

## Verified responses

| Model | Task | Condition | Truth | Answer | Correct | PNG |
|---|---|---|---|---|---|---|
| claude-opus-5 | [colorbench-smallmatch-01](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/results/runs/0.4.0/pilot-20260916/scorecard_claude-opus-5.json#L12888) | filled-20 | A | D | False | `smallmatch-01.png` |
| claude-opus-5 | [colorbench-smallmatch-05](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/results/runs/0.4.0/pilot-20260916/scorecard_claude-opus-5.json#L12990) | filled-84 | A | A | True | `smallmatch-05.png` |
| claude-opus-5 | [colorbench-smallmatch-09](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/results/runs/0.4.0/pilot-20260916/scorecard_claude-opus-5.json#L17783) | outline-3 | A | A | True | `smallmatch-09.png` |
| claude-opus-5 | [colorbench-smallmatch-13](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/results/runs/0.4.0/pilot-20260916/scorecard_claude-opus-5.json#L16971) | outline-12 | A | D | False | `smallmatch-13.png` |
| muse-spark-1.2 | [colorbench-context-01](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/results/runs/0.4.0/pilot-20260916/scorecard_muse-spark-1.2.json#L3509) | neutral | A | A | True | `context-01.png` |
| muse-spark-1.2 | [colorbench-context-05](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/results/runs/0.4.0/pilot-20260916/scorecard_muse-spark-1.2.json#L3611) | surround-0 | A | C | False | `context-05.png` |
| muse-spark-1.2 | [colorbench-context-09](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/results/runs/0.4.0/pilot-20260916/scorecard_muse-spark-1.2.json#L3747) | surround-1 | A | B | False | `context-09.png` |
| muse-spark-1.2 | [colorbench-context-13](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/results/runs/0.4.0/pilot-20260916/scorecard_muse-spark-1.2.json#L15689) | surround-2 | A | B | False | `context-13.png` |
| muse-spark-1.2 | [colorbench-context-17](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/results/runs/0.4.0/pilot-20260916/scorecard_muse-spark-1.2.json#L17434) | surround-3 | A | D | False | `context-17.png` |
| gpt-5.6-sol | [colorbench-samediff-27](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/results/runs/0.4.0/pilot-20260916/scorecard_gpt-5.6-sol.json#L12263) | sameA | A | A | True | `samediff-pair-04-bb.png` |
| gpt-5.6-sol | [colorbench-samediff-28](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/results/runs/0.4.0/pilot-20260916/scorecard_gpt-5.6-sol.json#L12297) | sameB | B | A | False | `samediff-pair-04-bb.png` |

## Verification and immutable image identities

Read selected rows from committed final_results.json and independently compared them with committed scorecard tasks. All selected raw strings parse to the published answer; all are valid and included in the cohort; canonical result hashes match the seal. Every selected PNG matches committed bytes and manifest SHA-256. Pillow sampling verifies every declared colored region, including outlined edges, and confirms the unchanged palettes and identical same–different patches. Viewed the seven primary original PNGs at their native 800×640 resolution (four small-region conditions, neutral/surround-0, and same–different). No labeling or rendering defect found.

| PNG | SHA-256 |
|---|---|
| [smallmatch-01.png](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/dataset/colorbench-v0.4.0/smallmatch-01.png) | `eb404a940032a1d9c44e4b60e46a39f0f6cb353a6b74dbcae0e352af1532ce30` |
| [smallmatch-05.png](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/dataset/colorbench-v0.4.0/smallmatch-05.png) | `80f78915953afa82ba32f4be2d1d07210b8e23a6c45d1984e9c4542ae219c2e0` |
| [smallmatch-09.png](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/dataset/colorbench-v0.4.0/smallmatch-09.png) | `0f8d4707cdf9e61ac4ed5855590e09a12599e354cdc97a40406f451baa2cdc15` |
| [smallmatch-13.png](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/dataset/colorbench-v0.4.0/smallmatch-13.png) | `87d6b82449ca59ed79fc7017204db3c09358ef56ee44b44a3d52b99178234ea6` |
| [context-01.png](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/dataset/colorbench-v0.4.0/context-01.png) | `793523b828639f0f3c19e7b142537a52eccfc6f69d72ab22c680996253917a60` |
| [context-05.png](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/dataset/colorbench-v0.4.0/context-05.png) | `6ce217e7bce683abf8d2f5631ecb1312eae16fb6380200b9e9b8c1011d8e9cc7` |
| [context-09.png](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/dataset/colorbench-v0.4.0/context-09.png) | `a18c2d5c47c4d111f2804a57ec9793d96784c46a1dcaf2ed93245d781c4acc35` |
| [context-13.png](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/dataset/colorbench-v0.4.0/context-13.png) | `b6b44f7166d6dd59702f2991f3f81bc36a62cfb63b7af4e34f478476f99d53cf` |
| [context-17.png](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/dataset/colorbench-v0.4.0/context-17.png) | `9625f7b3319e7223ecfeb8aa5f6820f4411cc12bb14b081b0d4d144e450f23fd` |
| [samediff-pair-04-bb.png](https://github.com/eob/colorbench/blob/a8868c33d3270635a58046716286303418649613/dataset/colorbench-v0.4.0/samediff-pair-04-bb.png) | `d6d3855e4cc7685d701a16fe0d54510e9945e3d8161fa52ca61a3ee0e945cdcd` |

## Exact mapping prompts

Do patches A and B have exactly the same flat fill color? Answer "A" for same and "B" for different. Compare the colored interiors, not labels or borders. Return only a JSON object with one key, "choice", whose value is the selected option letter.

Do patches A and B have exactly the same flat fill color? Answer "B" for same and "A" for different. Compare the colored interiors, not labels or borders. Return only a JSON object with one key, "choice", whose value is the selected option letter.

## Raw response and result identities

- `claude-opus-5` / `colorbench-smallmatch-01`: raw `{"choice":"D"}`; result SHA-256 `c036d052ad88e23db8f84b4b0a5b86d249742726ed504882997105582ea111ff`; recorded `2026-09-16T14:22:49.130136+00:00`.
- `claude-opus-5` / `colorbench-smallmatch-05`: raw `{"choice":"A"}`; result SHA-256 `a6eab1cd16b9d5f12454729d2a4a10e01a1bd1e2caee2eeb4e65da50530ba203`; recorded `2026-09-16T15:54:43.654466+00:00`.
- `claude-opus-5` / `colorbench-smallmatch-09`: raw `{"choice":"A"}`; result SHA-256 `4066be84dd6adf11b95db8aee0a83159e9ad9764a921350c0a392abee2579893`; recorded `2026-09-16T16:27:32.009838+00:00`.
- `claude-opus-5` / `colorbench-smallmatch-13`: raw `{"choice":"D"}`; result SHA-256 `ef4ebf23f6a2b6774d75c8cef7f03527d886b6f5c3e9608b6beda30aa138997b`; recorded `2026-09-16T16:21:18.302164+00:00`.
- `muse-spark-1.2` / `colorbench-context-01`: raw `{"choice": "A"}`; result SHA-256 `4ca98fbd3293e1c10694f7395bbf4b1c76ba226c81a7111f6d5934748c92f423`; recorded `2026-09-16T15:42:56.441450+00:00`.
- `muse-spark-1.2` / `colorbench-context-05`: raw `{"choice": "C"}`; result SHA-256 `f193edf13eb7417249071f1526263058a77afe76d66aae00a8ce988791ffe89e`; recorded `2026-09-16T14:01:30.514004+00:00`.
- `muse-spark-1.2` / `colorbench-context-09`: raw `{"choice":"B"}`; result SHA-256 `7f61c412946f442a69e784d323484b58a3c260170376e9b2c14d0dc5869d2e5f`; recorded `2026-09-16T15:50:44.154149+00:00`.
- `muse-spark-1.2` / `colorbench-context-13`: raw `{"choice": "B"}`; result SHA-256 `a17fab63552d43fa21258fa099ba0f04501c4d067668ee8242442c35ecbd7e06`; recorded `2026-09-16T16:11:00.175886+00:00`.
- `muse-spark-1.2` / `colorbench-context-17`: raw `{"choice": "D"}`; result SHA-256 `a6a17b081c0962c3269231d2ffc1947fade827c3d1b97c98337545de4a8d9317`; recorded `2026-09-16T16:25:22.164325+00:00`.
- `gpt-5.6-sol` / `colorbench-samediff-27`: raw `{"choice":"A"}`; result SHA-256 `b8780ce27bbb14c733fc0106766526c0d23aa089013187360ae07209d9b0dfaa`; recorded `2026-09-16T15:32:30.719178+00:00`.
- `gpt-5.6-sol` / `colorbench-samediff-28`: raw `{"choice":"A"}`; result SHA-256 `b91ed1668768a89ea48176b001b327f10012dc0ec8bbb18ca7387e0a2ca99458`; recorded `2026-09-16T15:09:16.436200+00:00`.
