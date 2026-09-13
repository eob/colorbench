"""Offline guards for paid run accounting, resume integrity, and final status."""
import json
from dataclasses import replace

import pytest

from baseline.evaluator import BaselineEvaluator
from baseline.runner import run_benchmark
from test_release_runs import _write_config, _write_manifest


def setup_run(tmp_path):
    manifest, config = tmp_path / 'manifest.json', tmp_path / 'models.json'
    _write_manifest(manifest, ['t1', 't2'])
    _write_config(config)
    return dict(manifest_path=manifest, config_path=config, output_dir=tmp_path / 'runs', run_id='rigor', mock=True)


def test_partial_run_finishes_with_partial_status(tmp_path):
    result = run_benchmark(**setup_run(tmp_path), max_tasks=1)
    assert result['status'] == 'partial'
    assert result['models']['mock-model']['status'] == 'partial'


def test_lost_checkpoint_refuses_to_repeat_completed_work(tmp_path):
    args = setup_run(tmp_path)
    run_benchmark(**args)
    directory = tmp_path / 'runs' / 'mock-rigor'
    (directory / 'state.sqlite3').unlink()
    before = (directory / 'attempts.jsonl').read_bytes()
    with pytest.raises(ValueError, match='checkpoint|state.sqlite3'):
        run_benchmark(**args)
    assert (directory / 'attempts.jsonl').read_bytes() == before


def test_rejected_config_does_not_mutate_metadata(tmp_path):
    args = setup_run(tmp_path)
    run_benchmark(**args)
    path = tmp_path / 'runs' / 'mock-rigor' / 'run.json'
    before = path.read_bytes()
    config = json.loads(args['config_path'].read_text())
    config['models'][0]['max_output_tokens'] *= 2
    args['config_path'].write_text(json.dumps(config))
    with pytest.raises(ValueError, match='config'):
        run_benchmark(**args)
    assert path.read_bytes() == before


def test_unmetered_attempt_retains_reserved_cost(tmp_path, monkeypatch):
    args = setup_run(tmp_path)
    evaluator = BaselineEvaluator(mock=True)
    original = evaluator._eval_single_task
    evaluator._eval_single_task = lambda *a: replace(original(*a), input_tokens=None, output_tokens=None, request_attempts=1, unmetered_attempts=1)
    monkeypatch.setattr('baseline.runner.BaselineEvaluator', lambda **kw: evaluator)
    monkeypatch.setattr('baseline.runner.require_valid_dataset', lambda *a: None)
    result = run_benchmark(**{**args, 'mock': False}, max_tasks=1)
    assert result['spent_cost_usd'] == pytest.approx((5000 + 16) / 1_000_000)
    assert result['models']['mock-model']['cost_usd'] > 0


def test_unknown_prices_refuse_budgeted_live_run(tmp_path, monkeypatch):
    args = setup_run(tmp_path)
    config = json.loads(args['config_path'].read_text())
    config['models'][0]['input_per_m'] = None
    args['config_path'].write_text(json.dumps(config))
    monkeypatch.setattr('baseline.runner.require_valid_dataset', lambda *a: None)
    monkeypatch.setattr('baseline.runner.BaselineEvaluator', lambda **kw: BaselineEvaluator(mock=True))
    with pytest.raises(ValueError, match='pric|cost'):
        run_benchmark(**{**args, 'mock': False})


def test_results_record_observation_time_and_inference_config(tmp_path):
    args = setup_run(tmp_path)
    run_benchmark(**args)
    directory = tmp_path / 'runs' / 'mock-rigor'
    card = json.loads((directory / 'scorecard_mock-model.json').read_text())
    assert all(row.get('recorded_at') for row in card['tasks'])
    assert card.get('model_config_fingerprint')
    assert card['model_config']['max_output_tokens'] == 16
    assert card['run_id'] == 'rigor'


def test_sealed_run_cannot_resume(tmp_path):
    args = setup_run(tmp_path)
    run_benchmark(**args)
    (tmp_path / 'runs' / 'mock-rigor' / 'finalization.json').write_text('{}')
    with pytest.raises(ValueError, match='finaliz|seal'):
        run_benchmark(**args)


def test_attempt_ledger_uses_commit_order_even_with_equal_timestamps(tmp_path):
    from baseline.run_state import RunStore
    with RunStore(tmp_path / 'state.sqlite3') as store:
        store.register_run('r', 'f', {})
        store.register_model('r', 'm', {})
        store.save_result('r', 'm', 't', {'error': 'timeout'}, attempt_id='z')
        store.save_result('r', 'm', 't', {'error': None}, attempt_id='a')
        store._connection.execute("UPDATE attempts SET created_at='2026-09-10T00:00:00Z'")
        ledger = store.attempts('r')
        assert [row['attempt_id'] for row in ledger] == ['z', 'a']
        assert [row['sequence'] for row in ledger] == [1, 2]
