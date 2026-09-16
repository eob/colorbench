"""CI freezes all previously registered versions while allowing new releases."""

import json
import subprocess

import pytest

from scripts.check_frozen_artifacts import check_frozen_artifacts


def test_every_existing_release_is_protected_but_new_releases_are_allowed(tmp_path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, capture_output=True, text=True, check=True).stdout.strip()

    git("init", "-q")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "Fixture")
    (tmp_path / "releases").mkdir()

    def release(version):
        directory = tmp_path / f"dataset/{version}"
        directory.mkdir(parents=True)
        (directory / "manifest.json").write_text("{}")
        (tmp_path / f"releases/{version}.json").write_text(json.dumps({"dataset_path": f"dataset/{version}"}))

    release("1.0.0")
    release("1.1.0")
    git("add", ".")
    git("commit", "-qm", "Initial frozen releases")
    base = git("rev-parse", "HEAD")
    release("1.2.0")
    git("add", ".")
    git("commit", "-qm", "Add new release")
    assert "dataset/1.1.0" in check_frozen_artifacts(base, root=tmp_path)
    (tmp_path / "dataset/1.1.0/manifest.json").write_text('{"changed":true}')
    git("add", ".")
    git("commit", "-qm", "Change previously frozen release")
    with pytest.raises(ValueError, match="Frozen artifacts changed"):
        check_frozen_artifacts(base, root=tmp_path)


@pytest.fixture
def published_run(tmp_path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, capture_output=True, text=True, check=True).stdout.strip()

    git("init", "-q")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "Fixture")
    files = {
        "releases/1.0.0.json": '{"dataset_path":"dataset/1.0.0"}',
        "dataset/1.0.0/manifest.json": "[]",
        "results/colorbench-pilot-1.0.0.json": "{}",
        "results/colorbench-pilot-1.0.0-analysis.json": "{}",
        "results/colorbench-pilot-1.0.0-audit.json": "{}",
        "results/colorbench_summary.json": "{}",
        "results/first-pilot.md": "Initial report\n",
        "results/runs/1.0.0/unsealed/attempts.jsonl": "{}\n",
    }
    for name in ("run.json", "summary.json", "scorecard_model.json", "attempts.jsonl",
                 "state.sqlite3", "final_results.json", "finalization.json"):
        files[f"results/runs/1.0.0/published/{name}"] = "original bytes\n"
    for name, content in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    git("add", ".")
    git("commit", "-qm", "Publish a sealed run and exports")
    return tmp_path, git, git("rev-parse", "HEAD")


@pytest.mark.parametrize("name,remove", [
    ("runs/1.0.0/published/run.json", False),
    ("runs/1.0.0/published/summary.json", False),
    ("runs/1.0.0/published/scorecard_model.json", False),
    ("runs/1.0.0/published/attempts.jsonl", False),
    ("runs/1.0.0/published/state.sqlite3", False),
    ("runs/1.0.0/published/final_results.json", False),
    ("runs/1.0.0/published/finalization.json", True),
    ("runs/1.0.0/published/extra-response.json", False),
    ("colorbench-pilot-1.0.0.json", False),
    ("colorbench-pilot-1.0.0-analysis.json", False),
    ("colorbench-pilot-1.0.0-audit.json", True),
    ("colorbench_summary.json", False),
])
def test_published_evidence_cannot_change_after_its_seal(published_run, name, remove):
    root, git, base = published_run
    path = root / "results" / name
    if remove:
        path.unlink()
    else:
        path.write_text("changed evidence\n")
    git("add", ".")
    git("commit", "-qm", "Attempt to change published evidence")
    with pytest.raises(ValueError, match="Frozen artifacts changed") as error:
        check_frozen_artifacts(base, root=root)
    assert f"results/{name}" in str(error.value)


def test_new_publications_and_unsealed_checkpoints_remain_writable(published_run):
    root, git, base = published_run
    updates = {
        "results/runs/1.0.0/unsealed/attempts.jsonl": "{}\n{}\n",
        "results/runs/1.0.0/unsealed/finalization.json": "{}",
        "results/runs/1.0.0/new-run/run.json": "{}",
        "results/colorbench-pilot-1.1.0.json": "{}",
        "results/first-pilot.md": "Report with clarified limitations\n",
    }
    for name, content in updates.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    git("add", ".")
    git("commit", "-qm", "Complete an unsealed run and publish new results")
    check_frozen_artifacts(base, root=root)
