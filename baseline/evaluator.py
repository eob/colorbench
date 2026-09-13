"""Evaluate color perception without pooling choice and numeric reconstruction."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import time

from baseline.color_math import hsl_to_rgb, oklab_to_linear_rgb, oklch_to_oklab, rgb_to_hsl, rgb_to_oklab, rgb_to_oklch
from baseline.protocol import CHOICE_FAMILIES, FAMILIES, NUMERIC_SCORING, get_prompt, parse_prediction, prediction_schema
from baseline.providers import PredictionClient, PredictionResponse

GRADING_VERSION = "2"


def evaluation_protocol_fingerprint() -> str:
    digest = hashlib.sha256(json.dumps({"grading_version": GRADING_VERSION, "numeric_scoring": NUMERIC_SCORING,
                                      "schemas": {family: prediction_schema(family) for family in FAMILIES}}, sort_keys=True).encode())
    for filename in ("evaluator.py", "providers.py", "protocol.py", "color_math.py", "statistics.py", "prompts.json"):
        digest.update(Path(__file__).with_name(filename).read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def cohort_fingerprint(ids: list[str]) -> str:
    return hashlib.sha256(json.dumps(sorted(ids)).encode()).hexdigest()


def load_manifest(manifest_path: str | Path) -> list[dict]:
    manifest = Path(manifest_path).resolve()
    data = json.loads(manifest.read_text())
    if not isinstance(data, list) or not data:
        raise ValueError("Manifest must be a nonempty array")
    seen = set()
    for item in data:
        if not isinstance(item, dict) or item.get("family") not in FAMILIES:
            raise ValueError("Manifest item has an unknown family")
        for key in ("taskId", "groupId"):
            if not isinstance(item.get(key), str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", item[key]):
                raise ValueError(f"Manifest requires an opaque {key}")
        if item["taskId"] in seen:
            raise ValueError("Duplicate task identity")
        seen.add(item["taskId"])
        filename = item.get("imageFilename")
        if (not isinstance(filename, str) or PurePosixPath(filename).name != filename
                or "\\" in filename or not filename.endswith(".png")):
            raise ValueError("Images must be PNG basenames beside the manifest")
        image = manifest.parent / filename
        if image.is_symlink() or not image.is_file():
            raise ValueError("Manifest image is missing or a symlink")
        item["imagePath"] = str(image)
        family = item["family"]
        ground_truth = item.get("groundTruth")
        if family in CHOICE_FAMILIES:
            if parse_prediction(json.dumps(ground_truth), family) != ground_truth:
                raise ValueError("Ground truth must use canonical option labels")
        elif (not isinstance(ground_truth, dict) or set(ground_truth) != {"rgb"}
              or not isinstance(ground_truth["rgb"], list) or len(ground_truth["rgb"]) != 3
              or any(type(value) is not int or not 0 <= value <= 255 for value in ground_truth["rgb"])):
            raise ValueError("Numeric ground truth requires exactly three decoded integer RGB channels")
        if not isinstance(item.get("design"), dict):
            raise ValueError("Missing design evidence")
        if item.get("prompt") != get_prompt(family, item["design"].get("direction")):
            raise ValueError("Item prompt differs from its canonical family prompt")
    return data


def grade_prediction(family: str, prediction: dict | None, ground_truth: dict) -> dict:
    prediction_schema(family)
    choice = family in CHOICE_FAMILIES
    if prediction is None:
        return dict(valid=False, correct=False if choice else None, score=0.0,
                    tight_score=None if choice else 0.0, delta_e_ok=None, component_errors=None,
                    within_bands=None, out_of_srgb=None)
    prediction = parse_prediction(json.dumps(prediction, allow_nan=False), family)
    if choice:
        correct = prediction["choice"] == ground_truth["choice"]
        return dict(valid=True, correct=correct, score=100.0 if correct else 0.0,
                    tight_score=None, delta_e_ok=None, component_errors=None,
                    within_bands=None, out_of_srgb=None)
    target_rgb = ground_truth["rgb"]
    target_lab = rgb_to_oklab(target_rgb)
    target_lch = rgb_to_oklch(target_rgb)
    if family == "rgb":
        predicted_lab = rgb_to_oklab([prediction[key] for key in "rgb"])
        components = {key: abs(prediction[key] - target) for key, target in zip("rgb", target_rgb)}
        outside = False
    else:
        if family == "hsl":
            target = rgb_to_hsl(target_rgb)
            predicted_lab = rgb_to_oklab(hsl_to_rgb(prediction["h"], prediction["s"], prediction["l"]))
            outside = False
        else:
            target = target_lch
            predicted_lab = oklch_to_oklab(prediction["l"], prediction["c"], prediction["h"])
            try:
                outside = any(not -1e-7 <= channel <= 1 + 1e-7 for channel in oklab_to_linear_rgb(predicted_lab))
            except OverflowError:
                outside = True
        components = {key: abs(prediction[key] - target[key]) for key in prediction}
        components["h"] = (abs((prediction["h"] - target["h"] + 180) % 360 - 180)
                           if target_lch["c"] >= NUMERIC_SCORING["hue_chroma_threshold"] else None)
        if family == "hsl" and target["l"] in (0, 100):
            components["s"] = None
    distance = math.dist(predicted_lab, target_lab)
    return dict(valid=True, correct=None, score=100 * (1 - min(distance / NUMERIC_SCORING["score_ceiling"], 1)),
                tight_score=100 * (1 - min(distance / NUMERIC_SCORING["tight_ceiling"], 1)),
                delta_e_ok=distance, component_errors=components,
                within_bands={str(band): distance <= band for band in NUMERIC_SCORING["exact_bands"]},
                out_of_srgb=outside)


@dataclass
class TaskEvaluationResult:
    task_id: str
    family: str
    group_id: str
    ground_truth: dict
    prompt_sha256: str
    image_path: str
    raw_prediction: str
    prediction: dict
    valid: bool
    correct: bool | None
    score: float
    tight_score: float | None
    delta_e_ok: float | None
    component_errors: dict | None
    within_bands: dict | None
    out_of_srgb: bool | None
    latency_sec: float | None
    input_tokens: int | None = None
    output_tokens: int | None = None
    request_attempts: int | None = None
    unmetered_attempts: int | None = None
    error: str | None = None
    error_kind: str | None = None
    model_name: str = ""
    provider: str = ""


@dataclass
class ColorBenchScorecard:
    total_tasks: int
    expected_task_count: int
    families: dict
    avg_latency_sec: float | None
    model_name: str
    provider: str
    timestamp: str
    grading_version: str
    evaluation_protocol: str
    cohort_sha256: str
    status: str
    task_results: list[TaskEvaluationResult] = field(default_factory=list)


class BaselineEvaluator:
    def __init__(self, model_name="gemini-3.5-flash-lite", mock=False, provider="google",
                 api_key_env=None, base_url=None, max_output_tokens=1024):
        self.model_name, self.mock, self.provider = model_name, mock, provider
        self._client = None if mock else PredictionClient(provider, model_name, api_key_env=api_key_env,
                                                          base_url=base_url, max_output_tokens=max_output_tokens)

    def close(self):
        if self._client is not None:
            self._client.close()

    def predict_image(self, image_path: str, prompt: str, family: str = "matching") -> PredictionResponse:
        if self.mock:
            prediction = {"choice": "A"} if family in CHOICE_FAMILIES else (
                {"r": 128, "g": 128, "b": 128} if family == "rgb" else
                {"h": 0., "s": 0., "l": 50.} if family == "hsl" else {"l": .5, "c": 0., "h": 0.})
            return PredictionResponse(json.dumps(prediction), prediction, input_tokens=0, output_tokens=0)
        return self._client.predict(image_path, prompt, family)

    def _eval_single_task(self, item: dict, prompt_default: str = "") -> TaskEvaluationResult:
        prompt = item.get("prompt", prompt_default)
        start = time.perf_counter()
        response = self.predict_image(item["imagePath"], prompt, item["family"])
        latency = time.perf_counter() - start
        parsed = None
        if not response.error:
            try:
                parsed = parse_prediction(response.raw_text, item["family"])
            except ValueError as error:
                response.error, response.error_kind = str(error), "invalid_response"
        return TaskEvaluationResult(task_id=item["taskId"], family=item["family"], group_id=item["groupId"],
                                    ground_truth=item["groundTruth"], prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                                    image_path=item["imagePath"], raw_prediction=response.raw_text, prediction=parsed or {},
                                    **grade_prediction(item["family"], parsed, item["groundTruth"]), latency_sec=latency,
                                    input_tokens=response.input_tokens, output_tokens=response.output_tokens,
                                    request_attempts=response.request_attempts, unmetered_attempts=response.unmetered_attempts,
                                    error=response.error, error_kind=response.error_kind,
                                    model_name=self.model_name, provider=self.provider)

    def score_results(self, results: list[TaskEvaluationResult], expected_task_count: int = 0) -> ColorBenchScorecard:
        from baseline.statistics import metrics
        observed = [result for result in results if not result.error or result.error_kind == "invalid_response"]
        total = len(observed)
        expected = expected_task_count or total
        latencies = [row.latency_sec for row in observed]
        latency = sum(latencies) / total if total and all(value is not None for value in latencies) else None
        return ColorBenchScorecard(total_tasks=total, expected_task_count=expected, families=metrics([asdict(row) for row in observed]),
                                   avg_latency_sec=latency, model_name=self.model_name, provider=self.provider,
                                   timestamp=datetime.now(timezone.utc).isoformat(), grading_version=GRADING_VERSION,
                                   evaluation_protocol=evaluation_protocol_fingerprint(),
                                   cohort_sha256=cohort_fingerprint([row.task_id for row in observed]),
                                   status="complete" if total == expected else "partial", task_results=observed)
