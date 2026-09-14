"""Independently reproduce grades and execution accounting from a verified run.

The independent grader deliberately imports neither color_math nor evaluator.
It uses the published OKLab matrices and CSS HSL conversion equations directly.
"""
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

from PIL import Image, ImageDraw

from baseline.finalize import verify_finalization
from baseline.protocol import CHOICE_FAMILIES


def lab(rgb):
    linear = [(v / 255 / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4) for v in rgb]
    cones = [[0.4122214708, 0.5363325363, 0.0514459929],
             [0.2119034982, 0.6806995451, 0.1073969566],
             [0.0883024619, 0.2817188376, 0.6299787005]]
    roots = [sum(a * b for a, b in zip(row, linear)) ** (1 / 3) for row in cones]
    output = [[0.2104542553, 0.7936177850, -0.0040720468],
              [1.9779984951, -2.4285922050, 0.4505937099],
              [0.0259040371, 0.7827717662, -0.8086757660]]
    return [sum(a * b for a, b in zip(row, roots)) for row in output]


def independent_distance(family, prediction, target):
    if family == "rgb":
        color = lab([prediction[k] for k in "rgb"])
    elif family == "hsl":
        h, s, l = prediction["h"] % 360, prediction["s"] / 100, prediction["l"] / 100
        chroma = (1 - abs(2 * l - 1)) * s
        x = chroma * (1 - abs((h / 60) % 2 - 1))
        sectors = [(chroma, x, 0), (x, chroma, 0), (0, chroma, x),
                   (0, x, chroma), (x, 0, chroma), (chroma, 0, x)]
        color = lab([255 * (v + l - chroma / 2) for v in sectors[int(h // 60)]])
    else:
        angle = prediction["h"] % 360 * math.pi / 180
        color = [prediction["l"], prediction["c"] * math.cos(angle), prediction["c"] * math.sin(angle)]
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(color, lab(target))))


def ordered_distractor_candidates(colors):
    """Historical attack: inspect only option pixels, never R or design metadata."""
    channel = max(range(3), key=lambda c: max(v[c] for v in colors) - min(v[c] for v in colors))
    values = [color[channel] for color in colors]
    candidates = []
    for i, value in enumerate(values):
        remaining = values[:i] + values[i + 1:]
        if (remaining == sorted(remaining) or remaining == sorted(remaining, reverse=True)) and sorted(values).index(value) in (1, 2):
            candidates.append(i)
    return candidates or list(range(4))


def audit(run_dir):
    directory = Path(run_dir)
    report = verify_finalization(directory)
    repository = Path(__file__).resolve().parents[1]
    manifest = json.loads((repository / report["dataset_manifest"]).read_text())
    items = {item["taskId"]: item for item in manifest}
    rows = [entry for entry in report["results"] if entry["included_in_comparison"]]
    family_counts, choice_correct = Counter(), Counter()
    maximum_delta_drift = maximum_score_drift = 0.0
    numeric_count = 0
    for entry in rows:
        row = entry["result"]
        family = row["family"]
        family_counts[family] += 1
        if not row["valid"]:
            assert row["score"] == 0
            continue
        prediction = json.loads(row["raw_prediction"])
        target = items[row["task_id"]]["groundTruth"]
        if family in CHOICE_FAMILIES:
            correct = prediction["choice"].strip().upper() == target["choice"]
            assert correct == row["correct"]
            assert row["score"] == (100 if correct else 0)
            choice_correct[family] += correct
        else:
            distance = independent_distance(family, prediction, target["rgb"])
            numeric_count += 1
            maximum_delta_drift = max(maximum_delta_drift, abs(distance - row["delta_e_ok"]))
            for cap, field in [(0.2, "score"), (0.05, "tight_score")]:
                score = max(0, 100 * (1 - distance / cap))
                maximum_score_drift = max(maximum_score_drift, abs(score - row[field]))
                assert math.isclose(score, row[field], rel_tol=0, abs_tol=1e-10)
            assert math.isclose(distance, row["delta_e_ok"], rel_tol=0, abs_tol=1e-12)
            assert all((distance <= float(band)) == value for band, value in row["within_bands"].items())
    attempts = [json.loads(line) for line in (directory / "attempts.jsonl").read_text().splitlines()]
    configs = {model["model_id"]: model["model_config"] for model in report["models"]}
    metered = 0.0
    unknown_usage = 0
    for attempt in attempts:
        row, model = attempt["result"], configs[attempt["model_id"]]
        if any(row.get(k) is None for k in ("input_tokens", "output_tokens")):
            unknown_usage += 1
        metered += ((row.get("input_tokens") or 0) * model["input_per_m"] +
                    (row.get("output_tokens") or 0) * model["output_per_m"]) / 1_000_000
    missing_request_counts = sum(a["result"].get("request_attempts") is None for a in attempts)
    missing_unmetered_counts = sum(a["result"].get("unmetered_attempts") is None for a in attempts)
    request_count = sum(a["result"].get("request_attempts") or 0 for a in attempts)
    unmetered_count = sum(a["result"].get("unmetered_attempts") or 0 for a in attempts)
    ledger_total = sum(a["cost_usd"] for a in attempts)
    execution = dict(
        runner_attempt_count=len(attempts), http_request_count=None if missing_request_counts else request_count,
        rows_missing_request_counts=missing_request_counts,
        rows_missing_unmetered_counts=missing_unmetered_counts,
        internal_retry_count=None if missing_request_counts else sum(max(0, (a["result"].get("request_attempts") or 0) - 1) for a in attempts),
        unmetered_http_request_count=None if missing_unmetered_counts else unmetered_count,
        rows_missing_usage_count=unknown_usage,
        recorded_usage_subtotal_usd=metered,
        ledger_spending_usd=ledger_total,
        unmetered_reserve_allowance_usd=ledger_total - metered,
        usage_complete=not any((unmetered_count, unknown_usage, missing_request_counts, missing_unmetered_counts)),
        invalid_final_response_count=sum(not a["result"]["valid"] for a in rows),
        final_response_count=len(rows),
        limitation="Catalog-price estimates, not provider invoices. Retry errors and bodies are not preserved individually inside an aggregated runner attempt.",
    )
    groups = defaultdict(list)
    order_control = defaultdict(lambda: {"question_count": 0, "expected_correct": 0.0})
    for item in manifest:
        if item["family"] not in ("matching", "binding", "hue", "gradient", "context", "smallmatch"):
            continue
        with Image.open(repository / report["dataset_path"] / item["imageFilename"]) as source:
            image = source.convert("RGB")
        if item["family"] in ("matching", "binding", "context", "smallmatch"):
            colors = [image.getpixel((r["x"], r["y"])) for r in item["rendered"]["regions"] if r["role"] == "option"]
            candidates = ordered_distractor_candidates(colors)
            count = order_control[item["family"]]
            count["question_count"] += 1
            count["expected_correct"] += ("ABCD".index(item["groundTruth"]["choice"]) in candidates) / len(candidates)
        draw = ImageDraw.Draw(image)
        region = next(r for r in item["rendered"]["regions"] if r["role"] == "target")
        x, y, w, h = (region[k] for k in ("x", "y", "width", "height"))
        draw.rectangle((x, y, x + w - 1, y + h - 1), fill=(0, 0, 0))
        key = (item["family"], item["prompt"], hashlib.sha256(image.tobytes()).hexdigest())
        groups[key].append(item["groundTruth"]["choice"])
    controls = {}
    for family in sorted({key[0] for key in groups}):
        selected = [answers for key, answers in groups.items() if key[0] == family]
        balanced = all(sorted(answers) == list("ABCD") for answers in selected)
        controls[family] = dict(masked_image_group_count=len(selected),
                                all_groups_cover_every_answer=balanced,
                                deterministic_reference_free_accuracy=0.25 if balanced else None)
    for value in order_control.values():
        value["expected_accuracy"] = value["expected_correct"] / value["question_count"]
    return dict(release=report["release"], run_id=report["run_id"],
                source_final_results_sha256=hashlib.sha256((directory / "final_results.json").read_bytes()).hexdigest(),
                execution=execution, reference_controls=controls, reference_free_order_control=dict(order_control),
                independent_grading=dict(response_count=len(rows), numeric_response_count=numeric_count,
                    choice_correct_counts=dict(choice_correct), family_response_counts=dict(family_counts),
                    maximum_delta_e_drift=maximum_delta_drift, maximum_score_drift=maximum_score_drift,
                    distance_tolerance=1e-12, score_tolerance=1e-10))


if __name__ == "__main__":
    result = audit(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2))
