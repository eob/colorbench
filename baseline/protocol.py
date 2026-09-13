"""Frozen family-specific answer contracts for the ColorBench perception pilot."""

import json
import math
from pathlib import Path

CHOICE_FAMILIES = ("matching", "lightness", "chroma", "hue", "binding", "gradient",
                   "samediff", "context", "smallmatch")
NUMERIC_FAMILIES = ("rgb", "hsl", "oklch")
FAMILIES = CHOICE_FAMILIES + NUMERIC_FAMILIES
NUMERIC_SCORING = {
    "distance": "euclidean-oklab",
    "score_ceiling": 0.2,
    "score_formula": "100 * (1 - min(delta_e_ok / 0.2, 1))",
    "tight_ceiling": 0.05,
    "tight_formula": "100 * (1 - min(delta_e_ok / 0.05, 1))",
    "exact_bands": [0.005, 0.01, 0.02, 0.05],
    "hue_chroma_threshold": 0.02,
    "interpretation": "Engineering normalization; not a just-noticeable-difference threshold.",
}


def choice_labels(family: str) -> list[str]:
    if family not in CHOICE_FAMILIES:
        raise ValueError(f"Not a choice family: {family}")
    return list("AB" if family in ("lightness", "chroma", "samediff") else "ABCD")


def prediction_schema(family: str) -> dict:
    if family in CHOICE_FAMILIES:
        properties = {"choice": {"type": "string", "enum": choice_labels(family)}}
    elif family == "rgb":
        properties = {key: {"type": "integer", "minimum": 0, "maximum": 255} for key in "rgb"}
    elif family == "hsl":
        properties = {"h": {"type": "number"}, **{key: {"type": "number", "minimum": 0, "maximum": 100} for key in "sl"}}
    elif family == "oklch":
        properties = {"l": {"type": "number", "minimum": 0, "maximum": 1},
                      "c": {"type": "number", "minimum": 0}, "h": {"type": "number"}}
    else:
        raise ValueError(f"Unknown task family: {family}")
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def wire_prediction_schema(family: str) -> dict:
    """Keep raw HTTP schemas within every provider's supported subset."""
    schema = prediction_schema(family)
    schema["properties"] = {name: {key: value for key, value in field.items() if key not in ("minimum", "maximum")}
                            for name, field in schema["properties"].items()}
    return schema


def _object(pairs: list[tuple[str, object]]) -> dict:
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"Duplicate prediction key: {key}")
        value[key] = item
    return value


def parse_prediction(raw_text: str, family: str) -> dict:
    schema = prediction_schema(family)
    try:
        parsed = json.loads(raw_text, object_pairs_hook=_object)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError("Prediction must be one JSON object") from error
    if not isinstance(parsed, dict) or set(parsed) != set(schema["required"]):
        raise ValueError("Prediction must have exactly the expected family keys")
    if family in CHOICE_FAMILIES:
        choice = parsed["choice"]
        if not isinstance(choice, str) or choice.strip().upper() not in choice_labels(family):
            raise ValueError("Prediction choice is not an available option")
        return {"choice": choice.strip().upper()}
    result = {}
    for key, bounds in schema["properties"].items():
        value = parsed[key]
        if family == "rgb" and type(value) is not int:
            raise ValueError("RGB channels require strict integers")
        if type(value) not in (int, float):
            raise ValueError("Numeric coordinates require numbers")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite or value < bounds.get("minimum", -math.inf) or value > bounds.get("maximum", math.inf):
            raise ValueError("Numeric coordinate is nonfinite or outside its defined range")
        result[key] = value if family == "rgb" else float(value)
    if "h" in result:
        result["h"] %= 360
    return result


def get_prompt(family: str, direction: str | None = None) -> str:
    prediction_schema(family)
    prompts = json.loads(Path(__file__).with_name("prompts.json").read_text())
    key = f"{family}-{direction}" if family in ("lightness", "chroma", "samediff") else family
    if key not in prompts:
        raise ValueError(f"Unknown task prompt: {key}")
    return prompts[key]
