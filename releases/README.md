# Frozen releases

`0.2.0` is a 72-question perception pilot: eight questions in each of matching, lightness, chroma, hue, binding, gradient, RGB, HSL, and OKLCH. The 24 numeric questions reuse eight target images across three fresh, format-specific requests. Matching and binding share eight color groups. There are 56 distinct images. Human agreement has not been measured.

A descriptor records `schema_version`, `benchmark_version`, `dataset_path`, `dataset_manifest`, `dataset_git_commit`, `dataset_fingerprint`, `evaluation_protocol_fingerprint`, and `expected_task_count`. Freeze the dataset in Git before creating the descriptor. The dataset fingerprint covers every manifest property except location fields and hashes actual PNG bytes. The release gate checks committed artifact bytes and inventory, canonical prompts, decoded color targets, option uniqueness and balance, repeated-group identity, bundled font evidence, and pixels outside declared color regions.

The protocol fingerprint includes the family schemas, numeric score definition, prompts, native request construction, parser, evaluator, conversion implementation, and statistics. Any change requires a new protocol release. Numeric bounds are enforced locally; all provider requests use the same supported schema subset without numerical `minimum`/`maximum` constraints. This permits native Anthropic HTTP requests, whose structured-output schema subset does not accept those constraints.

```sh
python -m baseline.validate_dataset dataset/colorbench-v0.2/manifest.json
python -m baseline.releases --release 0.2.0
python -m baseline.runner --release 0.2.0 --run-id first-pilot --config config/models.all.json --max-tasks 72 --concurrency 6 --budget-usd 25
```

The catalog contains 13 enabled configurations: four Claude, four GPT, three Gemini, and two Muse models. Pricing dates and official source links remain attached to each catalog. Meta uses its own OpenAI-compatible endpoint, a 300-second read timeout, and a 16,384-token output limit inherited from the measured sibling configuration. Run metadata preserves configurations, endpoint timeouts, source commits, invocation chronology, and an optional Anthropic workspace ID, without storing API keys.

Partial work can resume with the same run ID and unchanged identity. Invalid model answers are final observations and receive zero credit; infrastructure failures remain retryable, with prior attempt costs retained. The budget uses conservative reservations for unmetered attempts, marked `cost_estimated`. Those reserves never become reported mean API-response costs. Reports show unknown means as null and retain known-value counts. Paid work is refused if frozen artifacts or the protocol differ.

Historical prototype artifacts remain historical. They are not eligible for the pilot's release comparisons. Publication accepts an explicitly named, verified sealed run rather than selecting scorecards by file modification time. See [FINALIZATION.md](FINALIZATION.md).
