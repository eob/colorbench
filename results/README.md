# Results

**Release 0.4.0 is fully measured and verified.** All thirteen configurations
completed its 512 questions on September 16, 2026, producing 6,656 final
responses. Four invalid answers remain scored observations. The
[repair notes](../docs/direct-color-repairs-0.4.0.md) describe the new controls.

- [fourth-pilot.md](fourth-pilot.md): measured findings, paired outcomes, and limitations.
- [colorbench-pilot-0.4.0.json](colorbench-pilot-0.4.0.json): compact verified publication data.
- [colorbench-pilot-0.4.0-analysis.json](colorbench-pilot-0.4.0-analysis.json): family, model, paired, hue-context, and RGB recovery results.
- [colorbench-pilot-0.4.0-audit.json](colorbench-pilot-0.4.0-audit.json): independent grades, controls, and execution accounting.
- [runs/0.4.0/pilot-20260916](runs/0.4.0/pilot-20260916): sealed raw evidence and ledger.

## September 2026 models

Claude Opus 5.5, GPT-6 Sol, and GPT-6 Luna each completed all 512 questions
on the same frozen 0.4.0 release on September 23, 2026. The separately sealed
run contains 1,536 final responses, with zero invalid answers or infrastructure
retries. Its full-cohort fingerprint matches the September 16 campaign:
`c6bb84361fdffea7887f62ebdedbfa9c6d24da6466b5c90b750c0712bed7ecfa`.
The prior responses were not rerun.

- [colorbench-september-models-0.4.0.json](colorbench-september-models-0.4.0.json): compact verified publication data for these three models.
- [colorbench-september-models-0.4.0-analysis.json](colorbench-september-models-0.4.0-analysis.json): family, model, paired, hue-context, and RGB recovery results.
- [colorbench-september-models-0.4.0-audit.json](colorbench-september-models-0.4.0-audit.json): independent grades, controls, and execution accounting.
- [runs/0.4.0/september-models-20260923](runs/0.4.0/september-models-20260923): sealed raw responses and ledger.

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
