"""Preserve registered datasets, sealed runs, and published JSON snapshots."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path, PurePosixPath


def check_frozen_artifacts(base: str, *, root: Path = Path.cwd()) -> list[str]:
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout

    if not base or set(base) == {"0"}:
        raise ValueError("A real comparison commit is required to protect frozen releases")
    git("rev-parse", "--verify", f"{base}^{{commit}}")
    files = git("ls-tree", "-r", "--name-only", base, "releases").splitlines()
    protected = ["dataset/colorbench-1", "dataset/rendered"]
    for filename in files:
        if not filename.endswith(".json"):
            continue
        descriptor = json.loads(git("show", f"{base}:{filename}"))
        value = descriptor["dataset_path"]
        if not isinstance(value, str) or not value or "\\" in value:
            raise ValueError(f"Invalid dataset path in frozen descriptor {filename}")
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or str(path) != value:
            raise ValueError(f"Invalid dataset path in frozen descriptor {filename}")
        protected.extend([filename, value])
    for filename in git("ls-tree", "-r", "--name-only", base, "results").splitlines():
        path = PurePosixPath(filename)
        if path.parent == PurePosixPath("results") and path.suffix == ".json":
            protected.append(filename)
        elif path.is_relative_to("results/runs") and path.name == "finalization.json":
            # Unsealed checkpoints may advance; sealed run inventories may not.
            protected.append(str(path.parent))
    changed = git("diff", "--name-only", base, "HEAD", "--", *protected).splitlines()
    if changed:
        raise ValueError("Frozen artifacts changed:\n" + "\n".join(changed))
    return protected


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    paths = check_frozen_artifacts(args.base)
    print(f"Verified {len(paths)} frozen dataset/publication paths against {args.base}")
