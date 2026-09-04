#!/usr/bin/env python3
"""Install this checkout's skills for Codex or Claude Code without overwriting."""

import argparse
import os
from pathlib import Path
import re
import shutil
import sys


def install(agent, destination=None):
    source = Path(__file__).resolve().parents[1] / "skills"
    destination = Path(destination).expanduser().resolve() if destination else (
        Path.home() / (".agents" if agent == "codex" else ".claude") / "skills"
    ).resolve()
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("The destination must not overlap this checkout's skills directory.")

    skills = sorted(path for path in source.iterdir() if path.is_dir())
    if not skills:
        raise ValueError("No skill directories found.")
    for skill in skills:
        entry = skill / "SKILL.md"
        if not entry.is_file():
            raise ValueError(f"Missing SKILL.md: {skill.name}")
        content = entry.read_text(encoding="utf-8")
        header = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", content, re.S)
        if not header or not re.search(rf"^name:\s*{re.escape(skill.name)}\s*$", header[1], re.M):
            raise ValueError(f"Skill name must match its directory: {skill.name}")
        if not re.search(r"^description:\s*\S", header[1], re.M):
            raise ValueError(f"Missing description: {skill.name}")

    # Check all conflicts before copying any files, including broken symlinks.
    conflicts = [skill.name for skill in skills
                 if os.path.lexists(destination / skill.name)]
    if conflicts:
        raise FileExistsError("Nothing installed. Existing skills: " + ", ".join(conflicts))

    destination.mkdir(parents=True, exist_ok=True)
    for skill in skills:
        shutil.copytree(skill, destination / skill.name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return destination, [skill.name for skill in skills]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=("codex", "claude"), required=True)
    parser.add_argument("--dest", type=Path,
                        help="Override the user-level skills directory, e.g. .agents/skills")
    args = parser.parse_args()
    try:
        destination, names = install(args.agent, args.dest)
    except (OSError, ValueError) as error:
        print(f"Install failed: {error}", file=sys.stderr)
        return 1
    print(f"Installed {len(names)} skills for {args.agent} into {destination}")
    print("Start a new turn/session. If skills do not appear, restart your agent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
