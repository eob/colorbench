# Frozen releases

`0.3.1` is a 248-question perception pilot: separation sweeps for matching
(48), binding (48), lightness (16), chroma (16), and hue (16), with every
separation crossed against every answer position; 16 same–different, 16
surround-shifted context, and 16 small-region questions; 8 gradient questions
with direction crossed against position; and 48 numeric questions over 16
shared targets. There are 216 distinct images. Human agreement has not been
measured. (`0.3.0` froze the same task design with confounded stimulus
assignments; it was adversarially reviewed, never measured, and superseded
before any paid run.)

Cost basis: the 0.2.0 campaign spent $5.12 for 936 responses. A full 0.3.1
campaign is 3,224 responses (248 × 13 models) at the same catalog prices,
estimated ≈$18 under the $25 budget cap. The runner reserves worst-case
output cost per request before sending; watch the first paid run for
output-token growth on long numeric answers.

`0.2.0` is a 72-question perception pilot: eight questions in each of matching, lightness, chroma, hue, binding, gradient, RGB, HSL, and OKLCH. The 24 numeric questions reuse eight target images across three fresh, format-specific requests. Matching and binding share eight color groups. There are 56 distinct images. Human agreement has not been measured. Scores never transfer across releases.

A descriptor records `schema_version`, `benchmark_version`, `dataset_path`, `dataset_manifest`, `dataset_git_commit`, `dataset_fingerprint`, `evaluation_protocol_fingerprint`, and `expected_task_count`. Freeze the dataset in Git before creating the descriptor. The dataset fingerprint covers every manifest property except location fields and hashes actual PNG bytes. The release gate checks committed artifact bytes and inventory, canonical prompts, decoded color targets, option uniqueness and balance, repeated-group identity, bundled font evidence, and pixels outside declared color regions.

The protocol fingerprint includes the family schemas, numeric score definition, prompts, native request construction, parser, evaluator, conversion implementation, and statistics. Any change requires a new protocol release. Numeric bounds are enforced locally; all provider requests use the same supported schema subset without numerical `minimum`/`maximum` constraints. This permits native Anthropic HTTP requests, whose structured-output schema subset does not accept those constraints.

```sh
python -m baseline.validate_dataset dataset/colorbench-v0.3.1/manifest.json
python -m baseline.releases --release 0.3.1
python -m baseline.runner --release 0.3.1 --run-id pilot-example --config config/models.all.json --max-tasks 248 --concurrency 6 --budget-usd 25
```

The catalog contains 13 enabled configurations: four Claude, four GPT, three Gemini, and two Muse models. Pricing dates and official source links remain attached to each catalog. Meta uses its own OpenAI-compatible endpoint, a 300-second read timeout, and a 16,384-token output limit inherited from the measured sibling configuration. Run metadata preserves configurations, endpoint timeouts, source commits, invocation chronology, and an optional Anthropic workspace ID, without storing API keys.

Partial work can resume with the same run ID and unchanged identity. Invalid model answers are final observations and receive zero credit; infrastructure failures remain retryable, with prior attempt costs retained. The budget uses conservative reservations for unmetered attempts, marked `cost_estimated`. Those reserves never become reported mean API-response costs. Reports show unknown means as null and retain known-value counts. Paid work is refused if frozen artifacts or the protocol differ.

Historical prototype artifacts remain historical. They are not eligible for the pilot's release comparisons. Publication accepts an explicitly named, verified sealed run rather than selecting scorecards by file modification time. See [FINALIZATION.md](FINALIZATION.md).
