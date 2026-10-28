#!/usr/bin/env python3
"""Offline installation smoke test. Does not call a model or change user skills."""

import hashlib
from pathlib import Path
import json
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"bizplan", "bizplan-interview", "bizplan-quick", "bizplan-item", "bizplan-outline", "bizplan-problem",
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

    themes = ROOT / "skills/bizplan-slides/assets/themes"
    keys = {"name", "fonts", "colors", "chrome", "layout", "sizes", "styles"}
    for path in sorted(themes.glob("*.json")):
        if path.name.startswith("sample"):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        assert keys <= set(data), f"{path.name}: missing {keys - set(data)}"
    print("PASS theme files")
    with tempfile.TemporaryDirectory(prefix="bizplan-visuals-") as temporary:
        script = ROOT / "skills/bizplan-visual/scripts/html_visuals.py"
        sample = Path(temporary) / "sample.json"
        visuals = None
        for mode in ([], ["--print"], ["--slide"]):          # 화면·문서(인쇄)·발표 세 크기 모두 빌드되는지
            out = Path(temporary) / (mode[0].lstrip("-") if mode else "screen")
            for args in (["--sample", str(sample)], [str(sample), "--out", str(out), "--no-png", *mode]):
                result = subprocess.run([sys.executable, "-B", str(script), *args], capture_output=True, text=True)
                assert result.returncode == 0, result.stdout + result.stderr
            html = (out / "visuals.html").read_text(encoding="utf-8")
            visuals = visuals or [v for v in json.loads(sample.read_text(encoding="utf-8"))["visuals"] if v.get("type") != "chapter"]
            assert html.count('<section class="viz"') == len(visuals), mode
    print("PASS HTML visual sample build")
    try:
        import pptx  # noqa: F401
    except ImportError:
        print("SKIP sample deck spec check (python-pptx not installed)")
    else:
        result = subprocess.run([sys.executable, "-B", str(ROOT / "skills/bizplan-slides/scripts/theme_deck.py"),
                                 "--check", "--sample"], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
        print("PASS sample deck spec check")
    print("Static installation checks only; agent discovery and output quality are separate tests.")


if __name__ == "__main__":
    main()
