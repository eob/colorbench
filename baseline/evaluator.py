"""Evaluation logic and scorecard generation for ColorBench."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, Dict, List

from baseline.providers import (
    ErrorKind,
    PredictionClient,
    PredictionResponse,
    ColorPrediction,
)


def load_manifest(manifest_path: str | Path) -> list[dict]:
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "tasks" in data:
        return data["tasks"]
    if isinstance(data, list):
        return data
    raise ValueError("Manifest must be a JSON object with 'tasks' or a JSON array")


@dataclass
class TaskEvaluationResult:
    task_id: str
    semantic_role_gt: str
    surface_role_gt: str
    contrast_tier_gt: str
    fill_type_gt: str
    theme: str
    image_path: str
    raw_prediction: str
    predicted_semantic_role: str
    predicted_surface_role: str
    predicted_contrast_tier: str
    predicted_fill_type: str
    predicted_theme: str
    semantic_role_correct: bool
    surface_role_correct: bool
    contrast_tier_correct: bool
    fill_type_correct: bool
    theme_correct: bool
    all_correct: bool
    latency_sec: float
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
    overall_exact_match: float
    semantic_role_accuracy: float
    surface_role_accuracy: float
    contrast_tier_accuracy: float
    fill_type_accuracy: float
    theme_accuracy: float
    avg_latency_sec: float
    accuracy_by_role: Dict[str, Dict[str, float]]
    accuracy_by_contrast: Dict[str, Dict[str, float]]
    accuracy_by_fill: Dict[str, Dict[str, float]]
    accuracy_by_theme: Dict[str, Dict[str, float]]
    model_name: str
    timestamp: str
    expected_task_count: int = 0
    grading_version: str = "1"
    provider: str = "google"
    task_results: List[TaskEvaluationResult] = field(default_factory=list)


class BaselineEvaluator:
    def __init__(
        self,
        model_name: str = "gemini-3.5-flash",
        mock: bool = False,
        provider: str = "google",
        api_key_env: str | None = None,
        base_url: str | None = None,
        max_output_tokens: int = 1024,
    ):
        self.model_name = model_name
        self.provider = provider
        self.mock = mock
        self._client = None if mock else PredictionClient(
            provider, model_name, api_key_env=api_key_env,
            base_url=base_url, max_output_tokens=max_output_tokens,
        )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()

    def predict_image(self, image_path: str, prompt: str) -> PredictionResponse:
        if self.mock:
            prediction = {
                "semantic_role": "primary",
                "surface_role": "brand-fill",
                "contrast_tier": "aa-standard",
                "fill_type": "solid",
                "theme": "light",
            }
            return PredictionResponse(json.dumps(prediction), prediction, input_tokens=0, output_tokens=0)
        return self._client.predict(image_path, prompt)

    def _eval_single_task(self, item: dict, prompt_default: str) -> TaskEvaluationResult:
        image_path = item["imagePath"]
        prompt = item.get("prompt", prompt_default)

        start_t = time.perf_counter()
        response = self.predict_image(image_path, prompt)
        latency = time.perf_counter() - start_t
        raw_pred = response.raw_text
        parsed_pred = response.parsed if not response.error else {}

        pred_role = str(parsed_pred.get("semantic_role", "")).strip().lower()
        pred_surf = str(parsed_pred.get("surface_role", "")).strip().lower()
        pred_contrast = str(parsed_pred.get("contrast_tier", "")).strip().lower()
        pred_fill = str(parsed_pred.get("fill_type", "")).strip().lower()
        pred_theme = str(parsed_pred.get("theme", "")).strip().lower()

        gt = item.get("groundTruth", {})
        gt_role = str(gt.get("semantic_role", "")).strip().lower()
        gt_surf = str(gt.get("surface_role", "")).strip().lower()
        gt_contrast = str(gt.get("contrast_tier", "")).strip().lower()
        gt_fill = str(gt.get("fill_type", "")).strip().lower()
        gt_theme = str(gt.get("theme", "light")).strip().lower()

        role_correct = pred_role == gt_role
        surf_correct = pred_surf == gt_surf
        contrast_correct = pred_contrast == gt_contrast
        fill_correct = pred_fill == gt_fill
        theme_correct = pred_theme == gt_theme

        all_correct = (
            not response.error
            and role_correct
            and surf_correct
            and contrast_correct
            and fill_correct
            and theme_correct
        )

        return TaskEvaluationResult(
            task_id=item["taskId"],
            semantic_role_gt=gt_role,
            surface_role_gt=gt_surf,
            contrast_tier_gt=gt_contrast,
            fill_type_gt=gt_fill,
            theme=gt_theme,
            image_path=image_path,
            raw_prediction=raw_pred,
            predicted_semantic_role=pred_role,
            predicted_surface_role=pred_surf,
            predicted_contrast_tier=pred_contrast,
            predicted_fill_type=pred_fill,
            predicted_theme=pred_theme,
            semantic_role_correct=role_correct,
            surface_role_correct=surf_correct,
            contrast_tier_correct=contrast_correct,
            fill_type_correct=fill_correct,
            theme_correct=theme_correct,
            all_correct=all_correct,
            latency_sec=latency,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            request_attempts=response.request_attempts,
            unmetered_attempts=response.unmetered_attempts,
            error=response.error,
            error_kind=response.error_kind,
            model_name=self.model_name,
            provider=self.provider,
        )

    def score_results(self, results: list[TaskEvaluationResult], expected_task_count: int = 0) -> ColorBenchScorecard:
        total = len(results)
        denom = float(expected_task_count) if expected_task_count > 0 else float(total or 1)

        exact_matches = sum(1 for r in results if r.all_correct)
        role_matches = sum(1 for r in results if r.semantic_role_correct)
        surf_matches = sum(1 for r in results if r.surface_role_correct)
        contrast_matches = sum(1 for r in results if r.contrast_tier_correct)
        fill_matches = sum(1 for r in results if r.fill_type_correct)
        theme_matches = sum(1 for r in results if r.theme_correct)

        avg_latency = (sum(r.latency_sec for r in results) / total) if total > 0 else 0.0

        def build_slice(key_fn) -> Dict[str, Dict[str, float]]:
            buckets: Dict[str, Dict[str, int]] = {}
            for r in results:
                k = key_fn(r)
                if k not in buckets:
                    buckets[k] = {"total": 0, "exact": 0, "role": 0}
                buckets[k]["total"] += 1
                if r.all_correct:
                    buckets[k]["exact"] += 1
                if r.semantic_role_correct:
                    buckets[k]["role"] += 1
            out = {}
            for k, b in buckets.items():
                tot = b["total"]
                out[k] = {
                    "total": tot,
                    "exact_accuracy": round((b["exact"] / tot) * 100, 1) if tot > 0 else 0.0,
                    "role_accuracy": round((b["role"] / tot) * 100, 1) if tot > 0 else 0.0,
                }
            return out

        by_role = build_slice(lambda r: r.semantic_role_gt)
        by_contrast = build_slice(lambda r: r.contrast_tier_gt)
        by_fill = build_slice(lambda r: r.fill_type_gt)
        by_theme = build_slice(lambda r: r.theme)

        return ColorBenchScorecard(
            total_tasks=total,
            overall_exact_match=round((exact_matches / denom) * 100, 2),
            semantic_role_accuracy=round((role_matches / denom) * 100, 2),
            surface_role_accuracy=round((surf_matches / denom) * 100, 2),
            contrast_tier_accuracy=round((contrast_matches / denom) * 100, 2),
            fill_type_accuracy=round((fill_matches / denom) * 100, 2),
            theme_accuracy=round((theme_matches / denom) * 100, 2),
            avg_latency_sec=round(avg_latency, 3),
            accuracy_by_role=by_role,
            accuracy_by_contrast=by_contrast,
            accuracy_by_fill=by_fill,
            accuracy_by_theme=by_theme,
            model_name=self.model_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            expected_task_count=expected_task_count or total,
            provider=self.provider,
            task_results=results,
        )
