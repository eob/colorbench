"""Publication snapshots preserve live evidence and freeze an explicit cohort."""

import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess

import httpx
from PIL import Image
import pytest

from baseline import runner
from baseline.runner import dataset_fingerprint
from baseline.evaluator import evaluation_protocol_fingerprint
from baseline.protocol import get_prompt
from baseline.statistics import metrics


def finalizer():
    assert importlib.util.find_spec('baseline.finalize') is not None, 'Offline finalization tooling is missing'
    return importlib.import_module('baseline.finalize')


def test_offline_finalizer_is_available():
    assert callable(finalizer().finalize_run)


def test_model_summary_cost_must_match_its_attempt_ledger(campaign):
    path = campaign['directory'] / 'summary.json'
    summary = json.loads(path.read_text())
    summary['models']['model-a']['cost_usd'] += 1
    path.write_text(json.dumps(summary))
    git(campaign['root'], 'add', '.')
    git(campaign['root'], 'commit', '-qm', 'Forge model subtotal')
    with pytest.raises(ValueError, match='Model cost'):
        finalizer().finalize_run(campaign['directory'], scope='common', root=campaign['root'])


@pytest.mark.parametrize('filename,change', [
    ('run.json', lambda record: record.update(model_configs={})),
    ('summary.json', lambda record: record.update(cost_incomplete=True)),
])
def test_finalizer_checks_checkpoint_configuration_and_cost_completeness(campaign, filename, change):
    path = campaign['directory'] / filename
    record = json.loads(path.read_text())
    change(record)
    path.write_text(json.dumps(record))
    git(campaign['root'], 'add', '.')
    git(campaign['root'], 'commit', '-qm', 'Change fixture metadata')
    with pytest.raises(ValueError, match='configuration|cost completeness'):
        finalizer().finalize_run(campaign['directory'], scope='common', root=campaign['root'])


def git(root, *args):
    return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def campaign(tmp_path, monkeypatch):
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'user.email', 'test@example.com')
    git(tmp_path, 'config', 'user.name', 'Test')
    data = tmp_path / 'dataset/frozen'
    data.mkdir(parents=True)
    image = data / 'sample.png'
    Image.new('RGB', (4, 4), 'white').save(image)
    target = {'choice': 'A'}
    items = [dict(taskId=f'task-{i}', family='matching', groupId=f'group-{i}', groundTruth=target,
                  imageFilename='sample.png', imagePath=str(image), imageSha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                  prompt=get_prompt('matching'), design={'axis': 'hue', 'difficulty': 'wide'}) for i in range(3)]
    manifest = data / 'manifest.json'
    manifest.write_text(json.dumps(items))
    git(tmp_path, 'add', 'dataset')
    git(tmp_path, 'commit', '-qm', 'Freeze fixture dataset')
    release = dict(schema_version=1, benchmark_version='1.0.0', dataset_manifest='dataset/frozen/manifest.json',
                   dataset_path='dataset/frozen',
                   dataset_git_commit=git(tmp_path, 'rev-parse', 'HEAD'), dataset_fingerprint=dataset_fingerprint(items),
                   evaluation_protocol_fingerprint=evaluation_protocol_fingerprint(), expected_task_count=3)
    (tmp_path / 'releases').mkdir()
    (tmp_path / 'releases/1.0.0.json').write_text(json.dumps(release))
    configs = [dict(id=f'model-{name}', provider='google', model=f'model-{name}', display_name=name.upper(),
                    enabled=True, api_key_env='FIXTURE_API_KEY', source_url='https://example.com/models',
                    max_output_tokens=1024, input_per_m=price, output_per_m=2*price)
               for name, price in [('a', 2.0), ('b', 1.0)]]
    config = tmp_path / 'models.json'
    config.write_text(json.dumps(dict(version=1, verified_at='2026-09-09', models=configs)))
    monkeypatch.setenv('FIXTURE_API_KEY', 'fixture-only')
    monkeypatch.delenv('ANTHROPIC_WORKSPACE_ID', raising=False)
    monkeypatch.setattr(runner, 'load_release', lambda *args: release)
    monkeypatch.setattr(runner, 'release_manifest_path', lambda *args: manifest)
    monkeypatch.setattr(runner, 'validate_release', lambda *args: list(items))
    monkeypatch.setattr('baseline.validate_dataset.require_valid_dataset', lambda *args: {'valid': True})
    monkeypatch.setattr(runner, 'git_code_identity', lambda: dict(runner_git_commit=git(tmp_path, 'rev-parse', 'HEAD'), runner_git_dirty=False))
    prediction = json.dumps(target)
    requests = []
    def handle(request):
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(400, json={'error': {'message': 'Your credit balance is too low'}})
        return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': prediction}]}}],
                                        'usageMetadata': {'promptTokenCount': 100, 'candidatesTokenCount': 50}})
    original = httpx.Client
    monkeypatch.setattr('baseline.providers.httpx.Client', lambda **kwargs: original(transport=httpx.MockTransport(handle), **kwargs))
    args = dict(config_path=config, output_dir=tmp_path/'results/runs', run_id='sample', release='1.0.0',
                mock=False, concurrency=1, budget_usd=10)
    runner.run_benchmark(**args, max_tasks=1)
    runner.run_benchmark(**args, max_tasks=2)
    runner.run_benchmark(**args, max_tasks=3, selected_models=['model-a'])
    directory = tmp_path / 'results/runs/1.0.0/sample'
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-qm', 'Record fixture measurements')
    before = {p.name: p.read_bytes() for p in directory.iterdir() if p.name != '.runner.lock'}
    return dict(root=tmp_path, directory=directory, args=args, before=before, requests=requests)


def test_common_finalization_scores_all_responses_and_preserves_evidence(campaign):
    f = finalizer()
    report = f.finalize_run(campaign['directory'], scope='common', root=campaign['root'])
    assert report['comparison']['count'] == 2
    assert report['comparison']['model_ids'] == ['model-a', 'model-b']
    assert report['expected_task_count'] == 3
    assert len(report['results']) == 5
    assert sum(row['included_in_comparison'] for row in report['results']) == 4
    assert all(row['status'] == 'final' for row in report['results'])
    for model in report['models']:
        assert model['families']['matching']['accuracy'] == 1
        assert model['comparison_task_count'] == 2
        assert model['expected_task_count'] == 3
        assert model['mean_api_response_cost_usd'] == pytest.approx(.0004 if model['model_id'] == 'model-a' else .0002)
        assert model['families']['matching']['count'] == 2
    assert report['campaign']['infrastructure_attempt_count'] == 1
    assert report['campaign']['spent_cost_usd'] > sum(row['result']['cost_usd'] for row in report['results'])
    assert all((campaign['directory']/name).read_bytes() == contents for name,contents in campaign['before'].items())
    assert len(campaign['requests']) == 6
    assert f.verify_finalization(campaign['directory'], root=campaign['root']) == report


def test_finalization_is_idempotent_but_scope_cannot_change(campaign):
    f = finalizer()
    first = f.finalize_run(campaign['directory'], scope='common', root=campaign['root'])
    before = {p.name:p.read_bytes() for p in campaign['directory'].glob('final*.json')}
    assert f.finalize_run(campaign['directory'], scope='common', root=campaign['root']) == first
    assert before == {p.name:p.read_bytes() for p in campaign['directory'].glob('final*.json')}
    with pytest.raises(ValueError, match='scope|sealed|finalized'):
        f.finalize_run(campaign['directory'], scope='full', root=campaign['root'])


def test_full_scope_refuses_missing_inputs(campaign):
    with pytest.raises(ValueError, match='full|missing|complete'):
        finalizer().finalize_run(campaign['directory'], scope='full', root=campaign['root'])
    assert not (campaign['directory']/'finalization.json').exists()


def test_full_scope_accepts_complete_roster(campaign):
    runner.run_benchmark(**campaign['args'], max_tasks=3)
    git(campaign['root'], 'add', '.')
    git(campaign['root'], 'commit', '-qm', 'Complete fixture')
    report = finalizer().finalize_run(campaign['directory'], scope='full', root=campaign['root'])
    assert report['comparison']['count'] == 3
    assert len(report['results']) == 6
    assert all(m['coverage_status']=='complete' for m in report['models'])


def test_active_runner_refuses_finalization(campaign):
    f=finalizer()
    with runner._run_lock(campaign['directory']):
        with pytest.raises(RuntimeError, match='already running'):
            f.finalize_run(campaign['directory'], scope='common', root=campaign['root'])
    assert not (campaign['directory']/'final_results.json').exists()


def test_sealed_run_refuses_resume_before_clients_or_metadata_change(campaign, monkeypatch):
    directory=campaign['directory']
    (directory/'finalization.json').write_text('{}')
    monkeypatch.setattr(runner, 'BaselineEvaluator', lambda **kwargs: pytest.fail('Provider client constructed for sealed run'))
    with pytest.raises(ValueError, match='sealed|finalized'):
        runner.run_benchmark(**campaign['args'])
    assert all((directory/name).read_bytes()==contents for name,contents in campaign['before'].items())


@pytest.mark.parametrize('name', ['state.sqlite3','attempts.jsonl','run.json','summary.json','scorecard_model-a.json','final_results.json'])
def test_tampered_sealed_artifact_is_refused(campaign,name):
    f=finalizer();f.finalize_run(campaign['directory'],scope='common',root=campaign['root'])
    path=campaign['directory']/name;path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError,match='hash|changed|artifact'):
        f.verify_finalization(campaign['directory'],root=campaign['root'])


def test_raw_prediction_and_grade_disagreement_is_refused(campaign):
    f=finalizer();directory=campaign['directory']
    with sqlite3.connect(directory/'state.sqlite3') as c:
        model,task,raw=c.execute('select model_id,task_id,result_json from results limit 1').fetchone()
        row=json.loads(raw);row['correct']=False
        c.execute('update results set result_json=? where model_id=? and task_id=?',(json.dumps(row),model,task))
    c.close()
    with pytest.raises(ValueError,match='grade|attempt|scorecard|checkpoint'):
        f.finalize_run(directory,scope='common',root=campaign['root'])
    assert not (directory/'finalization.json').exists()


def test_semantic_forgery_is_rejected_even_with_updated_file_hash(campaign):
    f=finalizer();directory=campaign['directory'];f.finalize_run(directory,scope='common',root=campaign['root'])
    report=json.loads((directory/'final_results.json').read_text());report['comparison']['count']=3
    (directory/'final_results.json').write_text(json.dumps(report))
    seal=json.loads((directory/'finalization.json').read_text())
    seal['artifact_sha256']['final_results.json']=hashlib.sha256((directory/'final_results.json').read_bytes()).hexdigest()
    (directory/'finalization.json').write_text(json.dumps(seal))
    with pytest.raises(ValueError,match='comparison|cohort|final'):
        f.verify_finalization(directory,root=campaign['root'])


def rewrite_saved_response(campaign, change):
    """Alter fixture evidence consistently so independent grading is exercised."""
    from baseline.run_state import RunStore
    directory=campaign['directory']
    with sqlite3.connect(directory/'state.sqlite3') as c:
        model,task,raw=c.execute('select model_id,task_id,result_json from results order by model_id,task_id limit 1').fetchone()
        row=json.loads(raw);change(row)
        encoded=json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=False)
        c.execute('update results set result_json=? where model_id=? and task_id=?',(encoded,model,task))
        c.execute('update attempts set result_json=?,cost_usd=? where attempt_id=(select attempt_id from attempts where model_id=? and task_id=? order by rowid desc limit 1)',(encoded,row['cost_usd'],model,task))
    c.close()
    card_path=directory/f'scorecard_{model}.json';card=json.loads(card_path.read_text())
    card['tasks']=[row if result['task_id']==task else result for result in card['tasks']]
    card['families'] = metrics(card['tasks'])
    card_path.write_text(json.dumps(card))
    with RunStore(directory/'state.sqlite3') as store:
        exported=store.attempts('sample')
        summary=json.loads((directory/'summary.json').read_text())
        summary['spent_cost_usd']=store.spent_cost('sample')
        summary['models'][model]['cost_usd']=store.spent_cost('sample',model)
    (directory/'attempts.jsonl').write_text(''.join(json.dumps(attempt)+'\n' for attempt in exported))
    (directory/'summary.json').write_text(json.dumps(summary))
    git(campaign['root'],'add','.')
    git(campaign['root'],'commit','-qm','Change fixture evidence consistently')


def test_consistently_forged_grades_are_recomputed_from_raw_answer(campaign):
    rewrite_saved_response(campaign,lambda row: row.update(correct=False,score=0.0))
    with pytest.raises(ValueError,match='grades'):
        finalizer().finalize_run(campaign['directory'],scope='common',root=campaign['root'])


def test_metered_response_cost_excludes_internal_retry_reserves(campaign):
    rewrite_saved_response(campaign,lambda row: row.update(cost_usd=row['cost_usd']+1,cost_estimated=True,unmetered_attempts=1))
    report=finalizer().finalize_run(campaign['directory'],scope='common',root=campaign['root'])
    model=next(m for m in report['models'] if m['model_id']=='model-a')
    assert model['mean_api_response_cost_usd'] is None
    assert model['cost_known_response_count'] == 1
    assert report['campaign']['spent_cost_usd']>1


def test_invalid_model_answer_stays_final_and_zero_without_retry(campaign):
    def invalidate(row):
        row.update(raw_prediction='not a JSON answer', error='Invalid JSON', error_kind='invalid_response',
                   valid=False, correct=False, score=0.0, prediction={})
    rewrite_saved_response(campaign,invalidate)
    before=len(campaign['requests'])
    report=finalizer().finalize_run(campaign['directory'],scope='common',root=campaign['root'])
    invalid=[row for row in report['results'] if row['result'].get('error_kind')=='invalid_response']
    assert len(invalid)==1 and invalid[0]['status']=='final'
    assert invalid[0]['result']['correct'] is False
    assert len(campaign['requests'])==before


@pytest.mark.parametrize('remove_raw', [False, True], ids=['valid-answer-labeled-invalid', 'missing-raw-evidence'])
def test_invalid_marker_cannot_bypass_raw_response_replay(campaign, remove_raw):
    def forge(row):
        row.update(error='Invalid JSON', error_kind='invalid_response', valid=False, correct=False, score=0.0, prediction={})
        if remove_raw:
            row.pop('raw_prediction')
    rewrite_saved_response(campaign, forge)
    with pytest.raises(ValueError, match='raw|invalid|prediction|response'):
        finalizer().finalize_run(campaign['directory'], scope='common', root=campaign['root'])


def test_forged_source_commit_is_rejected_even_with_updated_hash(campaign):
    f=finalizer();directory=campaign['directory'];f.finalize_run(directory,scope='common',root=campaign['root'])
    report=json.loads((directory/'final_results.json').read_text());report['source_git_commit']='f'*40
    (directory/'final_results.json').write_text(json.dumps(report))
    seal=json.loads((directory/'finalization.json').read_text());seal['source_git_commit']='f'*40
    seal['artifact_sha256']['final_results.json']=hashlib.sha256((directory/'final_results.json').read_bytes()).hexdigest()
    (directory/'finalization.json').write_text(json.dumps(seal))
    with pytest.raises(ValueError,match='committed'):
        f.verify_finalization(directory,root=campaign['root'])


def test_explicit_roster_does_not_discard_other_original_responses(campaign):
    report=finalizer().finalize_run(campaign['directory'],scope='common',models=['model-a'],root=campaign['root'])
    assert report['comparison']['count']==3
    assert len(report['results'])==5
    assert sum(row['included_in_comparison'] for row in report['results'])==3


@pytest.mark.parametrize('roster',[[],['unknown'],['model-a','model-a']])
def test_invalid_roster_is_refused(campaign,roster):
    with pytest.raises(ValueError,match='roster'):
        finalizer().finalize_run(campaign['directory'],scope='common',models=roster,root=campaign['root'])


def test_exporter_refuses_tampered_sealed_run(campaign):
    from baseline.export_structured import build_structured_benchmark
    finalizer().finalize_run(campaign['directory'], scope='common', root=campaign['root'])
    report = build_structured_benchmark(campaign['directory'], root=campaign['root'])
    assert len(report['models']) == 2 and 'results' not in report
    card = campaign['directory'] / 'scorecard_model-a.json'
    card.write_bytes(card.read_bytes() + b' ')
    with pytest.raises(ValueError, match='hash|artifact'):
        build_structured_benchmark(campaign['directory'], root=campaign['root'])


def test_unknown_measurements_do_not_become_zero_or_partial_means(campaign):
    rewrite_saved_response(campaign,lambda row: row.update(input_tokens=None,latency_sec=None))
    report=finalizer().finalize_run(campaign['directory'],scope='common',root=campaign['root'])
    model=next(m for m in report['models'] if m['model_id']=='model-a')
    assert model['mean_api_response_cost_usd'] is None
    assert model['mean_latency_sec'] is None
    assert model['cost_known_response_count']==model['latency_known_response_count']==1


def test_orphan_final_results_also_refuse_resume(campaign,monkeypatch):
    (campaign['directory']/'final_results.json').write_text('{}')
    monkeypatch.setattr(runner,'BaselineEvaluator',lambda **kwargs: pytest.fail('Provider client constructed for unsealed publication'))
    with pytest.raises(ValueError,match='finalized|seal'):
        runner.run_benchmark(**campaign['args'])


def test_uncommitted_source_artifacts_cannot_be_sealed(campaign):
    path=campaign['directory']/'scorecard_model-a.json';path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError,match='committed'):
        finalizer().finalize_run(campaign['directory'],scope='common',root=campaign['root'])


@pytest.mark.parametrize('roster',[[{}],[None]])
def test_malformed_sealed_roster_fails_closed(campaign,roster):
    f=finalizer();directory=campaign['directory'];f.finalize_run(directory,scope='common',root=campaign['root'])
    report=json.loads((directory/'final_results.json').read_text());report['comparison']['model_ids']=roster
    (directory/'final_results.json').write_text(json.dumps(report))
    seal=json.loads((directory/'finalization.json').read_text())
    seal['artifact_sha256']['final_results.json']=hashlib.sha256((directory/'final_results.json').read_bytes()).hexdigest()
    (directory/'finalization.json').write_text(json.dumps(seal))
    with pytest.raises(ValueError,match='roster|Malformed'):
        f.verify_finalization(directory,root=campaign['root'])
