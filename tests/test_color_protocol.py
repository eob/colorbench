import json
import math

import pytest

from baseline import providers


def parse(raw, family):
    assert hasattr(providers, "parse_prediction"), "ColorBench needs a strict family-aware parser"
    return providers.parse_prediction(raw, family)


@pytest.mark.parametrize("family", ["matching", "lightness", "chroma", "hue", "binding", "gradient"])
def test_choice_families_use_only_arbitrary_option_ids(family):
    assert parse('{"choice":" a "}', family) == {"choice": "A"}


@pytest.mark.parametrize("raw,family", [
    ('{"choice":"C"}', "lightness"),
    ('{"choice":"C"}', "chroma"),
    ('{"choice":"A","why":"blue"}', "matching"),
    ('{"choice":"A","choice":"B"}', "matching"),
    ('{"choice":"A","\\u0063hoice":"B"}', "matching"),
    ('{"choice":true}', "matching"),
    ('```json\n{"choice":"A"}\n```', "matching"),
    ('{"r":1,"g":2,"b":3}', "matching"),
    ('{"r":true,"g":2,"b":3}', "rgb"),
    ('{"r":1.0,"g":2,"b":3}', "rgb"),
    ('{"r":256,"g":2,"b":3}', "rgb"),
    ('{"h":0,"s":101,"l":50}', "hsl"),
    ('{"h":NaN,"s":50,"l":50}', "hsl"),
    ('{"l":0.5,"c":-0.1,"h":90}', "oklch"),
    ('{"l":0.5,"c":1e999,"h":90}', "oklch"),
    ('{"l":0.5,"c":0.1,"h":90}', "unknown"),
])
def test_strict_family_schema_rejects_ambiguous_or_wrong_answers(raw, family):
    with pytest.raises(ValueError):
        parse(raw, family)


def test_numeric_schema_normalizes_hue_without_clipping_chroma():
    assert parse('{"r":0,"g":255,"b":128}', "rgb") == {"r": 0, "g": 255, "b": 128}
    assert parse('{"h":-1,"s":50,"l":50}', "hsl") == {"h": 359.0, "s": 50.0, "l": 50.0}
    assert parse('{"l":0.5,"c":2,"h":720}', "oklch") == {"l": 0.5, "c": 2.0, "h": 0.0}


def test_numeric_grading_keeps_formats_separate_and_uses_target_hue():
    from baseline.evaluator import grade_prediction
    exact = grade_prediction("rgb", {"r": 255, "g": 0, "b": 0}, {"rgb": [255, 0, 0]})
    assert exact["score"] == 100
    assert exact["delta_e_ok"] == 0
    assert exact["correct"] is None
    distant = grade_prediction("oklch", {"l": .5, "c": 2., "h": 0.}, {"rgb": [128, 128, 128]})
    assert distant["score"] == 0
    assert distant["out_of_srgb"] is True
    assert distant["component_errors"]["h"] is None
    assert math.isfinite(distant["delta_e_ok"])


def test_choice_grading_counts_observed_answers_and_invalids_without_cross_family_score():
    from baseline.evaluator import BaselineEvaluator
    from baseline.statistics import family_metrics
    evaluator = BaselineEvaluator(mock=True)
    item = {"taskId": "unit-1", "family": "matching", "groupId": "unit", "imagePath": "unused.png",
            "prompt": "Choose.", "groundTruth": {"choice": "A"}}
    row = evaluator._eval_single_task(item, "")
    card = evaluator.score_results([row], expected_task_count=72)
    assert card.total_tasks == 1
    assert card.families["matching"]["accuracy"] == 1
    assert "overall_exact_match" not in vars(card)
    invalid = dict(vars(row), task_id="unit-2", valid=False, correct=False, score=0.,
                   prediction={}, error="invalid", error_kind="invalid_response")
    metrics = family_metrics([vars(row), invalid], "matching")
    assert metrics["accuracy"] == .5
    assert metrics["validity_rate"] == .5
