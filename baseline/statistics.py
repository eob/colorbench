"""Descriptive family metrics on a fixed cohort, without pooling unlike tasks."""

import math

from baseline.protocol import CHOICE_FAMILIES, FAMILIES, choice_labels


def quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    lower = math.floor(index)
    fraction = index - lower
    return ordered[lower] * (1 - fraction) + ordered[min(lower + 1, len(ordered) - 1)] * fraction


def family_metrics(tasks: list[dict], family: str) -> dict:
    if family not in FAMILIES:
        raise ValueError(f"Unknown family: {family}")
    rows = [row for row in tasks if row["family"] == family]
    valid = [row for row in rows if row["valid"]]
    count = len(rows)
    value = dict(kind="choice" if family in CHOICE_FAMILIES else "numeric", count=count,
                 valid_count=len(valid), invalid_count=count - len(valid), validity_rate=len(valid) / count if count else None)
    if family in CHOICE_FAMILIES:
        correct = sum(row["correct"] is True for row in rows)
        labels = choice_labels(family)
        confusion = {label: {} for label in labels}
        for row in rows:
            cells = confusion[row["ground_truth"]["choice"]]
            predicted = row["prediction"]["choice"] if row["valid"] else "invalid"
            cells[predicted] = cells.get(predicted, 0) + 1
        value.update(correct_count=correct, accuracy=correct / count if count else None,
                     chance_accuracy=1 / len(labels), confusion=confusion)
    else:
        errors = [row["delta_e_ok"] for row in valid]
        components = sorted({key for row in valid for key in row["component_errors"]})
        means, known = {}, {}
        for key in components:
            selected = [row["component_errors"][key] for row in valid if row["component_errors"].get(key) is not None]
            means[key] = sum(value / len(selected) for value in selected) if selected else None
            known[key] = len(selected)
        value.update(mean_score=sum(row["score"] for row in rows) / count if count else None,
                     mean_delta_e_ok=sum(error / len(errors) for error in errors) if errors else None,
                     median_delta_e_ok=quantile(errors, .5), p90_delta_e_ok=quantile(errors, .9),
                     out_of_srgb_count=sum(row["out_of_srgb"] is True for row in valid),
                     mean_component_errors=means, component_known_count=known)
    return value


def metrics(tasks: list[dict]) -> dict:
    return {family: family_metrics(tasks, family) for family in FAMILIES}
