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
