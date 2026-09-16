# Results

**Fresh 0.4.0 measurements are pending.** Its 512 questions and 456 images
introduce new controls and require a new thirteen-model campaign. The
[repair notes](../docs/direct-color-repairs-0.4.0.md) describe the design;
passing offline checks does not establish model performance.

A new report must identify its completed run, full shared cohort, and verified
seal. Only sources accepted by `python -m baseline.finalize --run-dir <path>
--verify` using compatible code are eligible. Mock responses, unfinished
campaigns, and partial cohorts must not be presented as full-cohort results.

## Historical 0.3.2 publication

These files describe the previous 264-question corpus. They are preserved as
measured, including the limitations addressed in 0.4.0:

- [third-pilot.md](third-pilot.md): measured findings and interpretation.
- [colorbench-pilot-0.3.2.json](colorbench-pilot-0.3.2.json): compact verified publication data.
- [colorbench-pilot-0.3.2-analysis.json](colorbench-pilot-0.3.2-analysis.json): family, model, and paired summaries.
- [colorbench-pilot-0.3.2-audit.json](colorbench-pilot-0.3.2-audit.json): independent grades, reference controls, request counts, and cost accounting.
- [runs/0.3.2/pilot-20260914](runs/0.3.2/pilot-20260914): raw answers, SQLite ledger, sealed results, configurations, and artifact hashes.

Replay with source `8fc558433146066b8e1ed9b44303689b2433478d`, following the
[historical replay instructions](../releases/README.md#historical-replay).
The revised protocol intentionally does not reinterpret these old responses.

[0.3.1](second-pilot.md) and [0.2.0](first-pilot.md) also retain their measured
outputs and documented experimental flaws. Changes in corpus or protocol
prevent interpreting score differences between releases as model progress.
`colorbench_summary.json` belongs to the still-earlier prototype with visible
answer labels and is excluded from perception-benchmark publication.
