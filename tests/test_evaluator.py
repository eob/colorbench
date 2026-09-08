from baseline.evaluator import BaselineEvaluator, TaskEvaluationResult, ColorBenchScorecard
from baseline.providers import ColorPrediction


def test_color_prediction_schema():
    valid = {
        "semantic_role": "primary",
        "surface_role": "brand-fill",
        "contrast_tier": "aa-standard",
        "fill_type": "solid",
        "theme": "light",
    }
    pred = ColorPrediction.model_validate(valid)
    assert pred.semantic_role == "primary"
    assert pred.surface_role == "brand-fill"
    assert pred.contrast_tier == "aa-standard"
    assert pred.fill_type == "solid"
    assert pred.theme == "light"


def test_evaluator_scoring():
    evaluator = BaselineEvaluator(mock=True)
    item = {
        "taskId": "test-1",
        "imagePath": "test.png",
        "groundTruth": {
            "semantic_role": "primary",
            "surface_role": "brand-fill",
            "contrast_tier": "aa-standard",
            "fill_type": "solid",
            "theme": "light",
        },
    }
    result = evaluator._eval_single_task(item, "prompt")
    assert result.all_correct is True
    assert result.semantic_role_correct is True
    assert result.surface_role_correct is True
    assert result.contrast_tier_correct is True
    assert result.fill_type_correct is True
    assert result.theme_correct is True

    scorecard = evaluator.score_results([result], expected_task_count=1)
    assert scorecard.overall_exact_match == 100.0
    assert scorecard.semantic_role_accuracy == 100.0
    assert scorecard.surface_role_accuracy == 100.0
    assert scorecard.contrast_tier_accuracy == 100.0
    assert scorecard.fill_type_accuracy == 100.0
    assert scorecard.theme_accuracy == 100.0
    assert scorecard.total_tasks == 1
