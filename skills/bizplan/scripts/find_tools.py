#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""이 환경에 설치된 스킬을 읽어 도구 지도(references/tool-map.md)의 작업별로 지금 쓸 수 있는 것을 보여 준다.

    python3 -B find_tools.py                 # 작업별 표
    python3 -B find_tools.py --task 조사      # 작업 이름·쓰는 스킬에 '조사'가 든 행만
    python3 -B find_tools.py --json
    python3 -B find_tools.py --all           # 찾은 스킬 전체 목록

후보 이름은 도구 지도 표의 '있으면 부를 스킬' 칸에서 읽는다(지도가 단일 기준).
찾는 위치: ~/.claude/skills, ~/.claude/plugins, 작업 폴더와 상위의 .claude/skills, ~/.agents/skills, ~/.codex/skills, --root.
플러그인 이름은 가장 가까운 상위 폴더의 .claude-plugin/plugin.json에서 읽는다. bizplan 자체 스킬과 휴지통은 뺀다.
모델이 시스템의 스킬 목록을 이미 보고 있으면 이 스크립트는 필요 없다.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = HERE.parent / "references" / "tool-map.md"
SKIP = ("/.trash/", "/node_modules/", "/.git/")


def roots(extra):
    home = Path.home()
    out = [home / ".claude" / "skills", home / ".claude" / "plugins", home / ".agents" / "skills", home / ".codex" / "skills"]
    cwd = Path.cwd()
    for d in [cwd, *cwd.parents]:
        out.append(d / ".claude" / "skills")
    out += [Path(p).expanduser() for p in extra]
    seen, uniq = set(), []
    for r in out:
        r = r.resolve() if r.exists() else r
        if r not in seen and r.is_dir():
            seen.add(r)
            uniq.append(r)
    return uniq


def plugin_name(path, cache):
    for d in path.parents:
        if d in cache:
            return cache[d]
        meta = d / ".claude-plugin" / "plugin.json"
        if meta.is_file():
            try:
                name = json.loads(meta.read_text(encoding="utf-8")).get("name")
            except (OSError, ValueError):
                name = None
            cache[d] = name
            return name
        if d.name in ("plugins", "skills") and d.parent.name in (".claude", ".agents", ".codex"):
            break
    return None


def front(text):
    m = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return None, ""
    name = re.search(r"^name:\s*(.+)$", m.group(1), re.M)
    desc = re.search(r"^description:\s*(.+)$", m.group(1), re.M)
    clean = lambda s: s.group(1).strip().strip("'\"") if s else ""
    return clean(name) or None, clean(desc)


def installed(extra):
    found, cache = {}, {}
    for root in roots(extra):
        for p in root.rglob("SKILL.md"):
            sp = str(p)
            if any(s in sp for s in SKIP):
                continue
            try:
                name, desc = front(p.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
            name = name or p.parent.name
            plug = plugin_name(p, cache)
            if name.startswith("bizplan") or (plug or "").startswith("bizplan"):
                continue
            key = f"{plug}:{name}" if plug else name
            found.setdefault(key, {"name": name, "dir": p.parent.name, "plugin": plug, "path": sp, "desc": desc[:120]})
    return found


def tool_rows(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("|---") or "있으면 부를 스킬" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        cands = re.findall(r"`([^`]+)`", cells[2])
        rows.append({"task": cells[0], "users": cells[1], "candidates": cands, "fallback": cells[5]})
    return rows


def match(cand, found):
    plug, _, name = cand.rpartition(":")
    hits = []
    for key, s in found.items():
        if name not in (s["name"], s["dir"]):
            continue
        if plug and s["plugin"] and s["plugin"] != plug:
            continue
        hits.append(key)
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--task", help="작업 이름이나 쓰는 bizplan 스킬에 이 말이 든 행만")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--all", action="store_true", help="찾은 스킬 전체를 출력")
    ap.add_argument("--root", action="append", default=[], help="더 찾아볼 폴더")
    ap.add_argument("--map", default=str(MAP), help="도구 지도 경로")
    a = ap.parse_args()

    found = installed(a.root)
    if a.all:
        if a.json:
            print(json.dumps(found, ensure_ascii=False, indent=1))
        else:
            for key, s in sorted(found.items()):
                print(f"{key}\t{s['desc']}")
        return
    rows = tool_rows(Path(a.map))
    if a.task:
        rows = [r for r in rows if a.task in r["task"] or a.task in r["users"]]
    result = []
    for r in rows:
        avail = sorted({h for c in r["candidates"] for h in match(c, found)})
        result.append({**r, "available": avail})
    if a.json:
        print(json.dumps({"installed": len(found), "rows": result}, ensure_ascii=False, indent=1))
        return
    print(f"설치된 스킬 {len(found)}개(bizplan 제외) · 도구 지도 {len(rows)}행")
    print("| 작업 | 지금 쓸 수 있는 스킬 | 없으면 |")
    print("|------|----------------------|--------|")
    for r in result:
        print(f"| {r['task']} | {', '.join(r['available']) or '—'} | {r['fallback']} |")
    sys.exit(0)


if __name__ == "__main__":
    main()
