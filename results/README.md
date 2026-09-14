# Results

Current publication uses release 0.3.2:

- `third-pilot.md`: measured findings and interpretation.
- `colorbench-pilot-0.3.2.json`: compact verified publication data.
- `colorbench-pilot-0.3.2-analysis.json`: per-family, per-model, and paired analysis.
- `colorbench-pilot-0.3.2-audit.json`: independent grades, reference controls,
  request counts, and metered-versus-reserved cost accounting.
- `runs/0.3.2/pilot-20260914`: raw responses, SQLite ledger, sealed results,
  model configurations, and artifact hashes.

Only runs accepted by `python -m baseline.finalize --run-dir <path> --verify`
are publication sources. Mock runs and unsealed or partial campaigns are not
benchmark results.

Historical 0.3.1 and 0.2.0 reports preserve their measured outputs and disclose
their experimental flaws. They are not comparable to the corrected 0.3.2 corpus.
`colorbench_summary.json` is output from the still-earlier invalid 100-image
semantic prototype and is excluded from perception-benchmark publication.
