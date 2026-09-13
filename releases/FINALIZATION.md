# Offline finalization

Finish the runner, close its SQLite checkpoint, and commit the run evidence before sealing it. Finalization makes no provider requests and does not rewrite saved responses.

```sh
git add results/runs/0.2.0/first-pilot
git commit -m "Record ColorBench pilot observations"
python -m baseline.finalize --run-dir results/runs/0.2.0/first-pilot --scope full
python -m baseline.finalize --run-dir results/runs/0.2.0/first-pilot --verify
python -m baseline.export_structured --run-dir results/runs/0.2.0/first-pilot --output results/colorbench_summary.json
```

`full` requires every selected model to have all release questions. `common` publishes the explicit intersection of final task IDs, with a cohort fingerprint, and marks coverage partial. `--models` can fix a subset of recorded model IDs. Responses outside the publication cohort remain in the evidence. No nine-family aggregate score is computed.

For each choice family, accuracy includes invalid responses in its denominator and reports the available-option chance rate. Numeric formats each receive a separate mean bounded score over all responses, with invalid responses scored zero. The documented score is `100 * (1 - min(delta_e_ok / 0.2, 1))`; it is an engineering normalization, not a just-noticeable-difference threshold. Mean, median and linearly interpolated p90 color errors describe valid predictions only and appear beside validity counts. Raw OKLab error uses the unclipped estimate; out-of-sRGB predictions are flagged. Component hue error is omitted when the target OKLCH chroma is below 0.02, and HSL saturation error is omitted at black/white target endpoints.

Costs and latency use the same responses as each model or family score. API-response costs require complete metered tokens and recorded prices; any unknown measurement makes that mean null. Campaign spending also retains separate infrastructure attempts and estimated budget reserves, whose count is published.

The finalizer independently reconciles SQLite, the attempt export, scorecards, invocation timestamps, model configurations, per-model costs, and the committed source checkpoint. It reparses raw answers using the expected task family and recomputes grades and report metrics. `final_results.json` records the cohort, per-family results and source rows. `finalization.json` hashes the checkpoint, ledgers, scorecards, metadata, and report. Verification replays these checks instead of merely trusting the hash list.

Either finalization artifact prevents resuming that run. A finalized scope or roster cannot change. An interrupted seal with only `final_results.json` requires inspection; the tool fails closed rather than silently replacing it. Related images retain their shared groups and are not treated as independent observations for confidence intervals.
