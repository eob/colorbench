"""Native request schemas, metering, and raw-answer semantics across nine families."""
import json
from dataclasses import replace
from pathlib import Path

import httpx
from PIL import Image
import pytest

from baseline.evaluator import BaselineEvaluator, grade_prediction
from baseline.protocol import CHOICE_FAMILIES, FAMILIES, wire_prediction_schema
from baseline.providers import PredictionClient, PredictionResponse
from baseline.statistics import family_metrics


def prediction(family):
    return ({'choice': 'A'} if family in CHOICE_FAMILIES else
            {'r': 128, 'g': 128, 'b': 128} if family == 'rgb' else
            {'h': 0, 's': 0, 'l': 50} if family == 'hsl' else {'l': .5, 'c': 0, 'h': 0})


@pytest.mark.parametrize('provider', ['openai', 'anthropic', 'google'])
@pytest.mark.parametrize('family', ['rgb', 'hsl', 'oklch'])
def test_wire_schema_uses_the_shared_provider_supported_numeric_subset(provider, family):
    client = PredictionClient(provider, 'fixture-model')
    try:
        _, _, body = client._request('image-bytes', 'image/png', 'Frozen prompt', 'fixture-key', family)
    finally:
        client.close()
    encoded = json.dumps(body)
    assert 'minimum' not in encoded and 'maximum' not in encoded
    assert 'additionalProperties' in encoded and 'required' in encoded


@pytest.mark.parametrize('provider', ['openai', 'anthropic', 'google'])
@pytest.mark.parametrize('family', FAMILIES)
def test_provider_requests_use_only_expected_family_schema_and_image_prompt(tmp_path, monkeypatch, provider, family):
    image = tmp_path / 'do-not-send-this-answer-file.png'
    Image.new('RGB', (8, 8), (128, 128, 128)).save(image)
    monkeypatch.setenv('FIXTURE_KEY', 'fixture-only')
    text = json.dumps(prediction(family))
    requests = []
    def handler(request):
        requests.append(request)
        if provider == 'openai':
            body = {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': text}]}],
                    'usage': {'input_tokens': 20, 'output_tokens': 10}}
        elif provider == 'anthropic':
            body = {'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': text}],
                    'usage': {'input_tokens': 10, 'cache_read_input_tokens': 10, 'output_tokens': 10}}
        else:
            body = {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': text}]}}],
                    'usageMetadata': {'promptTokenCount': 20, 'candidatesTokenCount': 5, 'thoughtsTokenCount': 5}}
        return httpx.Response(200, json=body)
    client = PredictionClient(provider, 'fixture-model', api_key_env='FIXTURE_KEY')
    client._http.close()
    client._http = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        result = client.predict(str(image), 'Shared frozen prompt.', family)
    finally:
        client.close()
    assert result.error is None and result.parsed == prediction(family)
    assert result.input_tokens == 20 and result.output_tokens == 10 and result.unmetered_attempts == 0
    body = json.loads(requests[0].content)
    assert image.name not in requests[0].content.decode()
    assert 'groundTruth' not in requests[0].content.decode()
    schema = (body['text']['format']['schema'] if provider == 'openai' else
              body['output_config']['format']['schema'] if provider == 'anthropic' else body['generationConfig']['responseJsonSchema'])
    assert schema == wire_prediction_schema(family)


def test_grading_replays_raw_answer_instead_of_trusting_parsed_provider_object():
    evaluator = BaselineEvaluator(mock=True)
    evaluator.predict_image = lambda *args: PredictionResponse('{"choice":"A"}', {'choice': 'D'})
    item = dict(taskId='fixture', family='matching', groupId='fixture', imagePath='unused', prompt='frozen', groundTruth={'choice': 'A'})
    result = evaluator._eval_single_task(item)
    assert result.correct and result.prediction == {'choice': 'A'}
    evaluator.predict_image = lambda *args: PredictionResponse('{"choice":"A","choice":"B"}', {'choice': 'A'})
    invalid = evaluator._eval_single_task(item)
    assert invalid.error_kind == 'invalid_response' and invalid.score == 0 and not invalid.valid
    error = replace(result, error='timeout', error_kind='unavailable', valid=False, score=0.)
    card = evaluator.score_results([result, invalid, error], 72)
    assert card.total_tasks == 2 and card.families['matching']['accuracy'] == .5


def test_numeric_invalids_reduce_score_without_polluting_valid_error_statistics():
    row = dict(task_id='a', family='rgb', group_id='g', ground_truth={'rgb': [128, 128, 128]},
               prediction={'r': 128, 'g': 128, 'b': 128}, **grade_prediction('rgb', {'r':128,'g':128,'b':128}, {'rgb':[128,128,128]}))
    invalid = {**row, 'task_id': 'b', 'prediction': {}, **grade_prediction('rgb', None, {'rgb': [128,128,128]})}
    result = family_metrics([row, invalid], 'rgb')
    assert result['count'] == 2 and result['valid_count'] == 1 and result['mean_score'] == 50
    assert result['mean_delta_e_ok'] == result['median_delta_e_ok'] == result['p90_delta_e_ok'] == 0
    assert result['validity_rate'] == .5


def test_large_finite_chroma_is_unclipped_and_statistics_remain_finite():
    import math
    rows = []
    for index in range(8):
        parsed = {'l': .5, 'c': 1e308, 'h': 20.}
        grade = grade_prediction('oklch', parsed, {'rgb': [128,128,128]})
        assert grade['out_of_srgb'] and grade['score'] == 0 and math.isfinite(grade['delta_e_ok'])
        rows.append(dict(family='oklch', prediction=parsed, **grade))
    result = family_metrics(rows, 'oklch')
    assert math.isfinite(result['mean_delta_e_ok'])
    assert math.isfinite(result['mean_component_errors']['c'])
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize('color', [[0,0,0], [255,255,255]])
def test_hsl_extreme_targets_suppress_undefined_component_errors(color):
    grade = grade_prediction('hsl', {'h': 300., 's': 80., 'l': 50.}, {'rgb': color})
    assert grade['component_errors']['h'] is None and grade['component_errors']['s'] is None
    assert grade['component_errors']['l'] == 50 and grade['score'] < 100
