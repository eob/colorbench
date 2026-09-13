"""FontBench model snapshots and account-specific transport behavior stay aligned."""
import hashlib
import inspect
import json
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest

from baseline.evaluator import evaluation_protocol_fingerprint
from baseline.protocol import get_prompt
DEFAULT_PROMPT = get_prompt("matching")
from baseline.model_config import load_model_config
from baseline.releases import load_release
from baseline.runner import run_benchmark
from test_model_config import MODEL, catalog
from test_release_runs import _write_manifest

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HASHES = {
    'models.json': '98216c0c76c4876c57117f26f371fcae26bd92235ba9043da47c787bc40b06a2',
    'models.meta.json': '53f95ae38d053c81d69eb5e4bb2c9a2f316657d3c11a52293ed2551b8f055de2',
}
PREDICTION = {'choice': 'A'}


@pytest.mark.parametrize('name,digest', SOURCE_HASHES.items())
def test_fontbench_catalog_snapshot_bytes(name, digest):
    path = ROOT / 'config' / name
    assert path.is_file(), f'Missing FontBench catalog: {name}'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_combined_catalog_matches_both_sources_and_is_runner_default():
    path = ROOT / 'config/models.all.json'
    assert path.is_file(), 'The combined thirteen-model catalog is missing'
    combined = json.loads(path.read_text())
    expected = [row for name in SOURCE_HASHES for row in json.loads((ROOT / 'config' / name).read_text())['models']]
    assert combined['models'] == expected
    enabled = load_model_config(path)
    assert len(enabled) == 13
    assert len({row['id'] for row in enabled}) == 13
    assert inspect.signature(run_benchmark).parameters['config_path'].default == 'config/models.all.json'
    meta = [row for row in enabled if row['id'].startswith('muse-spark-')]
    assert {row['id'] for row in meta} == {'muse-spark-1.2', 'muse-spark-1.3'}
    assert all(row['base_url'] == 'https://api.meta.ai/v1' and row['max_output_tokens'] == 16384 for row in meta)


def test_openai_transport_does_not_combine_native_and_meta_catalog_limit(tmp_path):
    models = [{**MODEL, 'id': f'openai-{i}'} for i in range(4)]
    models += [{**MODEL, 'id': f'meta-{i}', 'base_url': 'https://api.meta.ai/v1'} for i in range(2)]
    assert len(load_model_config(catalog(tmp_path, models))) == 6


def _run_args(tmp_path, monkeypatch, models):
    manifest = tmp_path / 'manifest.json'
    _write_manifest(manifest, ['t1'])
    config = catalog(tmp_path, models)
    monkeypatch.setattr('baseline.runner.require_valid_dataset', lambda *args: None)
    for model in models:
        monkeypatch.setenv(model['api_key_env'], 'fixture-secret')
    return dict(manifest_path=manifest, config_path=config, output_dir=tmp_path / 'runs',
                run_id='parity', concurrency=1, budget_usd=25)


def _success(provider):
    text = json.dumps(PREDICTION)
    if provider == 'anthropic':
        return {'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': text}],
                'usage': {'input_tokens': 10, 'output_tokens': 10}}
    if provider == 'google':
        return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': text}]}}],
                'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 10}}
    return {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': text}]}],
            'usage': {'input_tokens': 10, 'output_tokens': 10}}


@pytest.mark.parametrize('provider', ['anthropic', 'openai', 'google'])
@pytest.mark.parametrize('workspace', [None, 'wrkspc_test123'])
def test_workspace_routing_is_anthropic_only_and_recorded(tmp_path, monkeypatch, provider, workspace):
    args = _run_args(tmp_path, monkeypatch, [{**MODEL, 'provider': provider}])
    if workspace is None: monkeypatch.delenv('ANTHROPIC_WORKSPACE_ID', raising=False)
    else: monkeypatch.setenv('ANTHROPIC_WORKSPACE_ID', workspace)
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=_success(provider))
    original = httpx.Client
    monkeypatch.setattr('baseline.providers.httpx.Client', lambda **kw: original(transport=httpx.MockTransport(respond), **kw))
    summary = run_benchmark(**args)
    assert summary['models'][MODEL['id']]['completed'] == 1
    expected = workspace if provider == 'anthropic' else None
    assert requests[0].headers.get('anthropic-workspace-id') == expected
    assert b'wrkspc_' not in requests[0].content
    metadata = json.loads((tmp_path / 'runs/parity/run.json').read_text())
    assert metadata['invocations'][-1].get('anthropic_workspace_id') == expected
    assert 'fixture-secret' not in json.dumps(metadata)


@pytest.mark.parametrize('endpoint,timeout', [('https://api.meta.ai/v1', 300.0),
    ('https://api.meta.ai/v1/', 300.0), ('https://api.openai.com/v1', 60.0)])
def test_meta_timeout_and_runtime_provenance(tmp_path, monkeypatch, endpoint, timeout):
    model = {**MODEL, 'base_url': endpoint, 'max_output_tokens': 16384}
    args = _run_args(tmp_path, monkeypatch, [model])
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=_success('openai'))
    original = httpx.Client
    monkeypatch.setattr('baseline.providers.httpx.Client', lambda **kw: original(transport=httpx.MockTransport(respond), **kw))
    run_benchmark(**args)
    assert requests[0].extensions['timeout']['read'] == timeout
    body = json.loads(requests[0].content)
    assert body['max_output_tokens'] == 16384
    assert 'reasoning' not in body
    metadata = json.loads((tmp_path / 'runs/parity/run.json').read_text())
    assert metadata['invocations'][-1]['request_timeouts_sec'][MODEL['id']] == timeout
    assert len(evaluation_protocol_fingerprint()) == 64


def test_invalid_workspace_fails_before_client_creation(tmp_path, monkeypatch):
    args = _run_args(tmp_path, monkeypatch, [{**MODEL, 'provider': 'anthropic'}])
    monkeypatch.setenv('ANTHROPIC_WORKSPACE_ID', 'invalid\r\nheader: value')
    client = Mock(side_effect=AssertionError('Client created before workspace validation'))
    monkeypatch.setattr('baseline.runner.BaselineEvaluator', client)
    with pytest.raises(ValueError, match='ANTHROPIC_WORKSPACE_ID'):
        run_benchmark(**args, max_tasks=0)
    client.assert_not_called()


def test_mock_run_ignores_workspace_configuration(tmp_path, monkeypatch):
    args = _run_args(tmp_path, monkeypatch, [{**MODEL, 'provider': 'anthropic'}])
    monkeypatch.setenv('ANTHROPIC_WORKSPACE_ID', 'ignored-in-offline-mode')
    assert run_benchmark(**args, mock=True)['status'] == 'complete'


@pytest.mark.parametrize('separate_account', [False, True])
def test_auth_failure_pauses_only_its_endpoint_and_account(tmp_path, monkeypatch, separate_account):
    first = {**MODEL, 'id': 'meta', 'base_url': 'https://api.meta.ai/v1', 'api_key_env': 'MODEL_API_KEY'}
    second = {**MODEL, 'id': 'other', 'base_url': 'https://api.meta.ai/v1' if separate_account else None}
    args = _run_args(tmp_path, monkeypatch, [first, second])
    requests = []
    def respond(request):
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(401, json={'error': {'message': 'Fixture authentication failure'}})
        return httpx.Response(200, json=_success('openai'))
    original = httpx.Client
    monkeypatch.setattr('baseline.providers.httpx.Client', lambda **kw: original(transport=httpx.MockTransport(respond), **kw))
    summary = run_benchmark(**args)
    assert summary['models']['meta']['completed'] == 0
    assert summary['models']['other']['completed'] == 1
    assert len(requests) == 2


def test_all_thirteen_catalog_models_use_native_requests_offline(tmp_path, monkeypatch):
    models = load_model_config(ROOT / 'config/models.all.json')
    args = _run_args(tmp_path, monkeypatch, models)
    manifest = json.loads(args['manifest_path'].read_text())
    manifest[0]['prompt'] = DEFAULT_PROMPT
    args['manifest_path'].write_text(json.dumps(manifest))
    requests = []
    def respond(request):
        requests.append(request)
        provider = 'anthropic' if request.url.host == 'api.anthropic.com' else 'google' if request.url.host == 'generativelanguage.googleapis.com' else 'openai'
        return httpx.Response(200, json=_success(provider))
    original = httpx.Client
    monkeypatch.setattr('baseline.providers.httpx.Client', lambda **kw: original(transport=httpx.MockTransport(respond), **kw))
    summary = run_benchmark(**args)
    assert summary['status'] == 'complete'
    assert len(requests) == len(summary['models']) == 13
    assert all(state['completed'] == 1 for state in summary['models'].values())
    for model, request in zip(models, requests):
        body = json.loads(request.content)
        if model['provider'] == 'google':
            assert model['model'] in request.url.path
            assert body['generationConfig']['maxOutputTokens'] == model['max_output_tokens']
            assert body['contents'][0]['parts'][1]['text'] == DEFAULT_PROMPT
        elif model['provider'] == 'anthropic':
            assert body['model'] == model['model']
            assert body['max_tokens'] == model['max_output_tokens']
            assert body['messages'][0]['content'][1]['text'] == DEFAULT_PROMPT
        else:
            assert body['model'] == model['model']
            assert body['max_output_tokens'] == model['max_output_tokens']
            assert body['input'][0]['content'][1]['text'] == DEFAULT_PROMPT
            assert body['input'][0]['content'][0]['detail'] == 'high'
    assert len(evaluation_protocol_fingerprint()) == 64


def test_auth_failure_still_pauses_siblings_on_same_account(tmp_path, monkeypatch):
    models = [{**MODEL, 'id': name, 'base_url': 'https://api.meta.ai/v1'} for name in ['first', 'second']]
    args = _run_args(tmp_path, monkeypatch, models)
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(401, json={'error': {'message': 'Fixture authentication failure'}})
    original = httpx.Client
    monkeypatch.setattr('baseline.providers.httpx.Client', lambda **kw: original(transport=httpx.MockTransport(respond), **kw))
    summary = run_benchmark(**args)
    assert all(state['completed'] == 0 and state['status'] == 'paused' for state in summary['models'].values())
    assert len(requests) == 1
