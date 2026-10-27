#!/usr/bin/env python3
"""Offline installation smoke test. Does not call a model or change user skills."""

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"bizplan", "bizplan-quick", "bizplan-item", "bizplan-outline", "bizplan-problem",
            "bizplan-research", "bizplan-solution", "bizplan-growth", "bizplan-team",
            "bizplan-summary", "bizplan-visual", "bizplan-review", "bizplan-pitch",
            "bizplan-slides", "bizplan-export", "bizplan-analyze"}


def snapshot(root):
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"}


def run(agent, destination):
    return subprocess.run([sys.executable, str(ROOT / "scripts/install_skills.py"),
                           "--agent", agent, "--dest", str(destination)],
                          capture_output=True, text=True, encoding="utf-8")


def main():
    assert {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()} == EXPECTED
    with tempfile.TemporaryDirectory(prefix="bizplan-install-") as temporary:
        for agent in ("codex", "claude"):
            destination = Path(temporary) / agent / "skills"
            result = run(agent, destination)
            assert result.returncode == 0, result.stderr
            assert snapshot(destination) == snapshot(ROOT / "skills"), "Installed content differs"
            # A user's edit must survive a second install; no silent merge or overwrite.
            marker = destination / "bizplan" / "user-note.md"
            marker.write_text("Keep this user edit.\n", encoding="utf-8")
            before = snapshot(destination)
            result = run(agent, destination)
            assert result.returncode != 0 and "Existing skills" in result.stderr
            assert snapshot(destination) == before, "Repeated install changed existing files"
            print(f"PASS {agent}: {len(EXPECTED)} skills, exact resource copies, no overwrite on repeat")

        # Even a late-name collision must be caught before any earlier skills are copied.
        partial = Path(temporary) / "partial"
        (partial / "bizplan-visual").mkdir(parents=True)
        result = run("codex", partial)
        assert result.returncode != 0
        assert {path.name for path in partial.iterdir()} == {"bizplan-visual"}
        print("PASS conflict preflight: no partial install")

    result = run("codex", ROOT / "skills")
    assert result.returncode != 0 and "overlap" in result.stderr
    print("PASS source overlap guard")
    print("Static installation checks only; agent discovery and output quality are separate tests.")


if __name__ == "__main__":
    main()
