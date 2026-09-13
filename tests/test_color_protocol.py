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


SAMEDIFF_SAME_A = (
    'Do patches A and B have exactly the same flat fill color? Answer "A" for same and "B" for different. '
    'Compare the colored interiors, not labels or borders. '
    'Return only a JSON object with one key, "choice", whose value is the selected option letter.'
)
SAMEDIFF_SAME_B = (
    'Do patches A and B have exactly the same flat fill color? Answer "B" for same and "A" for different. '
    'Compare the colored interiors, not labels or borders. '
    'Return only a JSON object with one key, "choice", whose value is the selected option letter.'
)
CONTEXT_PROMPT = (
    "Which option, A, B, C, or D, has the same flat interior fill color as reference R? "
    "Each option sits on a different surround color; compare the interiors only, not the surrounds, labels, or borders. "
    'Return only a JSON object with one key, "choice", whose value is the selected option letter.'
)
SMALLMATCH_PROMPT = (
    "Which swatch, A, B, C, or D, has the same color as reference R? "
    "The swatches are small; compare the colored regions, not labels or borders. "
    'Return only a JSON object with one key, "choice", whose value is the selected option letter.'
)


@pytest.mark.parametrize("family", ["samediff", "context", "smallmatch"])
def test_harder_choice_families_use_only_arbitrary_option_ids(family):
    assert parse('{"choice":" a "}', family) == {"choice": "A"}


@pytest.mark.parametrize("raw,family", [
    ('{"choice":"C"}', "samediff"),
    ('{"choice":"D"}', "samediff"),
    ('{"choice":"E"}', "context"),
    ('{"choice":"E"}', "smallmatch"),
    ('{"choice":"A","choice":"B"}', "context"),
])
def test_harder_choice_schema_rejects_unavailable_or_ambiguous_answers(raw, family):
    with pytest.raises(ValueError):
        parse(raw, family)


def test_harder_family_prompts_are_byte_frozen():
    from baseline.protocol import get_prompt
    assert get_prompt("samediff", "sameA") == SAMEDIFF_SAME_A
    assert get_prompt("samediff", "sameB") == SAMEDIFF_SAME_B
    assert get_prompt("context") == CONTEXT_PROMPT
    assert get_prompt("smallmatch") == SMALLMATCH_PROMPT
    with pytest.raises(ValueError):
        get_prompt("samediff")
    with pytest.raises(ValueError):
        get_prompt("samediff", "lighter")


def test_tight_score_and_bands_measure_near_exact_reconstruction():
    from baseline.evaluator import grade_prediction
    exact = grade_prediction("rgb", {"r": 128, "g": 64, "b": 32}, {"rgb": [128, 64, 32]})
    assert exact["tight_score"] == 100
    assert exact["within_bands"] == {"0.005": True, "0.01": True, "0.02": True, "0.05": True}
    near = grade_prediction("rgb", {"r": 132, "g": 64, "b": 32}, {"rgb": [128, 64, 32]})
    assert 0 < near["delta_e_ok"] < 0.05
    assert near["tight_score"] < near["score"] < 100
    assert near["within_bands"]["0.05"] is True
    assert list(near["within_bands"]) == ["0.005", "0.01", "0.02", "0.05"]
    far = grade_prediction("rgb", {"r": 0, "g": 0, "b": 0}, {"rgb": [255, 255, 255]})
    assert far["tight_score"] == 0
    assert far["score"] == 0
    assert set(far["within_bands"].values()) == {False}
    invalid = grade_prediction("rgb", None, {"rgb": [128, 64, 32]})
    assert invalid["tight_score"] == 0.0
    assert invalid["within_bands"] is None
    assert invalid["delta_e_ok"] is None


def test_band_hit_rates_cover_valid_answers_and_rgb_lsb_rates():
    from baseline.evaluator import grade_prediction
    from baseline.statistics import family_metrics
    rows = []
    for index, prediction in enumerate([{"r": 128, "g": 64, "b": 32}, {"r": 132, "g": 64, "b": 32}, None]):
        grade = grade_prediction("rgb", prediction, {"rgb": [128, 64, 32]})
        rows.append(dict(task_id=f"n{index}", family="rgb", group_id="g", ground_truth={"rgb": [128, 64, 32]},
                         prediction=prediction or {}, **grade))
    result = family_metrics(rows, "rgb")
    assert result["mean_tight_score"] == sum(row["tight_score"] for row in rows) / 3
    assert result["band_hit_rate"]["0.05"] == 1.0
    assert result["band_hit_rate"]["0.005"] == 0.5
    assert result["rgb_within_2_lsb"] == 0.5
    assert result["rgb_within_5_lsb"] == 1.0
    hsl_rows = [dict(task_id="h", family="hsl", group_id="g", ground_truth={"rgb": [128, 64, 32]},
                     prediction={"h": 0.0, "s": 0.0, "l": 50.0},
                     **grade_prediction("hsl", {"h": 0.0, "s": 0.0, "l": 50.0}, {"rgb": [128, 64, 32]}))]
    hsl_result = family_metrics(hsl_rows, "hsl")
    assert "band_hit_rate" in hsl_result and hsl_result["rgb_within_2_lsb"] is None
