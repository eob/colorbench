"""Paired analysis keeps conditions, invalid answers, and model identities intact."""

from copy import deepcopy
import json
from pathlib import Path
import runpy
import sys

import pytest

from baseline.color_math import rgb_to_hsl, rgb_to_oklch
from baseline.evaluator import grade_prediction
from baseline.protocol import FAMILIES
from baseline.statistics import family_metrics


SCRIPT = Path(__file__).parents[1] / "scripts/analyze_pilot.py"


@pytest.fixture
def report():
    specimens, results = {}, []

    def add(task, family, group, design, predictions, truth=None):
        truth = truth or {"choice": "A"}
        specimens[task] = dict(task_id=task, family=family, group_id=group, design=design)
        for model, prediction in zip(("alpha", "beta"), predictions):
            if type(prediction) is bool:
                prediction = {"choice": truth["choice"] if prediction else ("B" if truth["choice"] == "A" else "A")}
            row = dict(task_id=task, family=family, group_id=group, ground_truth=truth,
                       prediction=prediction or {}, **grade_prediction(family, prediction, truth))
            results.append(dict(model_id=model, included_in_comparison=True, result=row))

    for family in ("matching", "binding", "lightness", "chroma", "gradient"):
        add(family, family, "shared", {}, [True, False])
    for difficulty, outcomes in (("fixed-lightness-chroma", [True, False]),
                                 ("varying-lightness-chroma", [False, True])):
        add(difficulty, "hue", difficulty, {"difficulty": difficulty}, outcomes)
    for group in ("one", "two"):
        for condition in ("neutral", "surround-0", "surround-1", "surround-2", "surround-3"):
            outcomes = ([True, False] if group == "one" else [False, True]) if condition == "neutral" else (
                [False, False] if group == "one" else [True, True])
            add(f"context-{group}-{condition}", "context", group, {"condition": condition}, outcomes)
    for condition, outcomes in (("filled-20", [False, False]), ("filled-84", [True, None]),
                                ("outline-3", [True, False]), ("outline-12", [False, True])):
        # A context group deliberately has the same group ID.
        add(f"small-{condition}", "smallmatch", "one", {"condition": condition}, outcomes)
    for same, predictions in ((True, [[{"choice": "A"}, {"choice": "A"}],
                                      [{"choice": "A"}, {"choice": "B"}]]),
                              (False, [[{"choice": "B"}, {"choice": "A"}],
                                       [None, {"choice": "B"}]])):
        pair = f"equality-{same}"
        for direction, answers in zip(("sameA", "sameB"), predictions):
            truth = {"choice": "A" if same == (direction == "sameA") else "B"}
            add(f"{pair}-{direction}", "samediff", pair,
                dict(mappingPairId=pair, direction=direction, same=same), answers, truth)
    rgb = [128, 128, 128]
    for i, predictions in enumerate(([dict(r=128, g=128, b=128)] * 2,
                                     [dict(r=130, g=128, b=128)] * 2,
                                     [dict(r=133, g=133, b=133)] * 2,
                                     [None, dict(r=135, g=128, b=128)])):
        add(f"rgb-{i}", "rgb", f"numeric-{i}", {}, predictions, {"rgb": rgb})
    for family, prediction in (("hsl", rgb_to_hsl(rgb)), ("oklch", rgb_to_oklch(rgb))):
        add(family, family, "numeric-0", {}, [prediction, prediction], {"rgb": rgb})
    return dict(release="0.4.0", run_id="fixture", campaign={}, results=results,
                specimens=list(specimens.values()), comparison=dict(model_ids=["alpha", "beta"],
                    count=len(specimens), task_ids=sorted(specimens)),
                models=[dict(model_id=model, model_config={"display_name": model},
                             families={family: family_metrics([e["result"] for e in results if e["model_id"] == model], family)
                                       for family in FAMILIES}) for model in ("alpha", "beta")])


def analyze(report, tmp_path, monkeypatch):
    monkeypatch.setattr("baseline.finalize.verify_finalization", lambda _: report)
    output = tmp_path / "analysis.json"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "sealed-fixture", str(output)])
    runpy.run_path(str(SCRIPT), run_name="__main__")
    return json.loads(output.read_text())


def test_context_pairs_keep_every_condition_and_model(report, tmp_path, monkeypatch):
    result = analyze(report, tmp_path, monkeypatch)
    pairs = result["matched_condition_pairs"]["context"]
    assert set(pairs) == {f"neutral_vs_surround-{i}" for i in range(4)}
    pair = pairs["neutral_vs_surround-0"]
    pooled = pair["pooled"]
    assert pooled["count"] == 4
    assert [pooled[k] for k in ("both_correct", "first_only_correct", "second_only_correct", "both_incorrect")] == [1, 1, 1, 1]
    assert pooled["second_minus_first_accuracy"] == 0
    assert pair["models"]["alpha"]["first_only_correct"] == 1
    assert pair["models"]["beta"]["both_incorrect"] == 1


def test_size_and_stroke_are_separate_paired_interventions(report, tmp_path, monkeypatch):
    pairs = analyze(report, tmp_path, monkeypatch)["matched_condition_pairs"]["smallmatch"]
    assert set(pairs) == {"filled-20_vs_filled-84", "outline-3_vs_outline-12"}
    filled = pairs["filled-20_vs_filled-84"]["pooled"]
    assert filled["count"] == 2 and filled["second_only_correct"] == 1
    assert filled["second_invalid_count"] == 1
    assert filled["first_accuracy"] == 0 and filled["second_accuracy"] == 0.5
    assert filled["second_minus_first_accuracy"] == 0.5
    outline = pairs["outline-3_vs_outline-12"]["pooled"]
    assert outline["first_only_correct"] == outline["second_only_correct"] == 1


def test_missing_conditions_are_reported_without_inventing_pairs(report, tmp_path, monkeypatch):
    task = "context-two-surround-0"
    report["results"] = [entry for entry in report["results"] if entry["result"]["task_id"] != task]
    pair = analyze(report, tmp_path, monkeypatch)["matched_condition_pairs"]["context"]["neutral_vs_surround-0"]["pooled"]
    assert pair["count"] == 2 and pair["unpaired_first_count"] == 2
    assert pair["unpaired_second_count"] == 0


def test_duplicate_condition_never_silently_overwrites_an_observation(report, tmp_path, monkeypatch):
    duplicate = deepcopy(next(entry for entry in report["results"] if entry["result"]["task_id"] == "context-one-neutral"))
    report["results"].append(duplicate)
    with pytest.raises(ValueError, match="Duplicate.*condition"):
        analyze(report, tmp_path, monkeypatch)


def test_same_different_mapping_consistency_uses_semantics_and_valid_pairs(report, tmp_path, monkeypatch):
    result = analyze(report, tmp_path, monkeypatch)["same_different_mapping_pairs"]
    pooled = result["pooled"]
    assert pooled["count"] == 4
    assert pooled["valid_pairs"] == 3 and pooled["invalid_pairs"] == 1
    assert pooled["semantic_consistent_pairs"] == 2 and pooled["semantic_inconsistent_pairs"] == 1
    assert pooled["consistency_rate_among_valid_pairs"] == pytest.approx(2 / 3)
    assert pooled["both_correct"] == 1 and pooled["both_incorrect"] == 1
    assert result["models"]["beta"]["semantic_consistent_pairs"] == 2
    assert result["models"]["beta"]["both_incorrect"] == 1


def test_hue_contexts_remain_separate_for_each_model(report, tmp_path, monkeypatch):
    contexts = analyze(report, tmp_path, monkeypatch)["hue_contexts"]
    fixed = contexts["fixed-lightness-chroma"]
    varying = contexts["varying-lightness-chroma"]
    assert fixed["pooled"]["correct_count"] == varying["pooled"]["correct_count"] == 1
    assert fixed["models"]["alpha"]["accuracy"] == 1
    assert varying["models"]["alpha"]["accuracy"] == 0


def test_rgb_exact_and_tolerance_counts_retain_invalid_denominators(report, tmp_path, monkeypatch):
    result = analyze(report, tmp_path, monkeypatch)["rgb_reconstruction"]
    pooled = result["pooled"]
    assert pooled["response_count"] == 8 and pooled["valid_count"] == 7 and pooled["invalid_count"] == 1
    assert pooled["exact_count"] == 2
    assert pooled["within_2_lsb_count"] == 4 and pooled["within_5_lsb_count"] == 6
    assert pooled["delta_e_hit_counts"]["0.05"] == 7
    assert result["models"]["alpha"]["invalid_count"] == 1


def test_existing_matching_and_numeric_pairs_survive_new_conditions(report, tmp_path, monkeypatch):
    result = analyze(report, tmp_path, monkeypatch)
    assert result["matching_binding_pairs"]["alpha"]["both_correct"] == 1
    assert result["matching_binding_pairs"]["beta"]["both_incorrect"] == 1
    assert result["numeric_format_pairs"]["rgb_vs_hsl"]["valid_pairs"] == 2


def test_excluded_observations_do_not_enter_pair_counts(report, tmp_path, monkeypatch):
    duplicate = deepcopy(next(entry for entry in report["results"] if entry["result"]["task_id"] == "context-one-neutral"))
    duplicate["included_in_comparison"] = False
    report["results"].append(duplicate)
    pairs = analyze(report, tmp_path, monkeypatch)["matched_condition_pairs"]["context"]["neutral_vs_surround-0"]
    assert pairs["pooled"]["count"] == 4


def test_no_valid_answers_preserves_counts_without_a_fabricated_rate(report, tmp_path, monkeypatch):
    for entry in report["results"]:
        row = entry["result"]
        if row["family"] in ("rgb", "samediff"):
            row.update(grade_prediction(row["family"], None, row["ground_truth"]), prediction={})
    result = analyze(report, tmp_path, monkeypatch)
    rgb = result["rgb_reconstruction"]["pooled"]
    assert rgb["response_count"] == rgb["invalid_count"] == 8
    assert rgb["valid_count"] == rgb["exact_count"] == 0
    assert set(rgb["delta_e_hit_counts"].values()) == {0}
    mapping = result["same_different_mapping_pairs"]["pooled"]
    assert mapping["count"] == mapping["invalid_pairs"] == 4
    assert mapping["valid_pairs"] == 0 and mapping["consistency_rate_among_valid_pairs"] is None


def test_import_does_not_verify_or_write_a_report(monkeypatch):
    monkeypatch.setattr("baseline.finalize.verify_finalization", lambda _: pytest.fail("Imported analysis executed a run"))
    runpy.run_path(str(SCRIPT))
