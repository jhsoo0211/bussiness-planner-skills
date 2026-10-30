#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""완성 문서 서식(--style form)의 공통 부분 — md_to_docx.py · md_to_hwpx.py가 같이 쓴다.

개요 양식 블록(```개요 … ```)을 읽어 표 배치로 바꾸고, 불릿을 서식 기호(- ·)로 바꾼다.

    ```개요
    명칭: 서비스 이름
    범주: 사업 범주
    소개:
      ○ 굵게 보일 헤드라인 한 줄
      - 사실 한 줄
    진출 목표시장:
      ○ …
    이미지: 시각자료/a.png = 캡션 | 시각자료/b.png = 캡션
    ```

키는 줄 맨 앞에 `키: 값`으로 쓰고, 여러 줄 값은 들여 써서 잇는다. 명칭·범주는 한 줄에 나란히, 나머지 키는 쓴 순서대로
한 줄씩, 이미지는 2개씩 그림 줄 + 캡션 줄로 놓인다.
"""
import re

FORM_KINDS = ("개요",)
MARK = "@@FORM-{}@@"
MARK_RE = re.compile(r"^@@FORM-(\d+)@@$")
OVERVIEW_MM = (27.0, 71.0, 24.0, 48.0)     # 이름표 · 값 · 이름표 · 값 (합 170mm — 그림 2칸이 71 / 72로 고르게)
PAIR = ("명칭", "범주")
FORM_MARKS = ["-", "·", "·", "·"]           # 완성 문서 서식의 불릿 기호(○는 주제구에 쓴다)


def split_forms(md):
    """```개요``` 블록을 꺼내 표지 문단(@@FORM-n@@)으로 바꾼다 → (바꾼 md, 양식 목록)."""
    out, forms = [], []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^```\s*(\S+)\s*$", lines[i].strip())
        if m and m.group(1) in FORM_KINDS:
            body, j = [], i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                body.append(lines[j])
                j += 1
            forms.append(parse_form(m.group(1), body))
            out += ["", MARK.format(len(forms) - 1), ""]
            i = j + 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out), forms


def parse_form(kind, body):
    rows = []
    for ln in body:
        if not ln.strip():
            continue
        m = re.match(r"^([^\s\-○·][^:：]{0,24})[:：]\s*(.*)$", ln)
        if m:
            rows.append([m.group(1).strip(), [m.group(2).strip()] if m.group(2).strip() else []])
        elif rows:
            rows[-1][1].append(ln.strip())
    images, keep = [], []
    for key, vals in rows:
        if key == "이미지":
            for part in " ".join(vals).split("|"):
                path, _, cap = part.strip().partition("=")
                if path.strip():
                    images.append((path.strip(), cap.strip()))
        else:
            keep.append((key, vals))
    return {"kind": kind, "rows": keep, "images": images}


def layout(form):
    """표 행 배치 목록: ('pair', (키, 값), (키, 값)) · ('full', 키, 값) · ('img', [(경로, 캡션), …]) · ('cap', […])."""
    rows = dict(form["rows"])
    out, used = [], set()
    for key, vals in form["rows"]:
        if key in used:
            continue
        if key in PAIR and all(k in rows for k in PAIR):
            out.append(("pair", (PAIR[0], rows[PAIR[0]]), (PAIR[1], rows[PAIR[1]])))
            used.update(PAIR)
        else:
            out.append(("full", key, vals))
            used.add(key)
    imgs = form["images"]
    for k in range(0, len(imgs), 2):
        out.append(("img", imgs[k:k + 2]))
        out.append(("cap", imgs[k:k + 2]))
    return out


def label_text(key):
    """두 글자 이름표는 글자 사이를 띄운다(양식 표의 '명  칭' 모양)."""
    return "  ".join(key) if len(key) == 2 else key


NOTE_LINE = re.compile(r"^\s*(※|\((출처|확인|참고)\s*[:：])")


def note_breaks(md):
    """'※ 주석'·'(출처: …)'·'(확인 경로: …)'·'(참고: …)' 줄 앞에 빈 줄을 넣는다.
    마크다운은 이웃한 줄을 한 문단으로 합쳐, 주석과 출처가 작은 글씨 한 줄로 섞여 찍히던 것을 막는다."""
    out, fence = [], False
    for line in md.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
        if not fence and NOTE_LINE.match(line) and out and out[-1].strip() and not out[-1].lstrip().startswith("|"):
            out.append("")
        out.append(line)
    return "\n".join(out)


def form_bullets(md, escape=True):
    """불릿을 서식 기호 문단으로 바꾼다: 1단 '-', 2단 이하 '·'. 표·코드 블록 안은 그대로.
    escape=True면 1단 '-'를 '\\-'로 적어 pandoc이 목록으로 다시 읽지 않게 한다."""
    out, fence = [], False
    indents = [len(m.group(1)) for m in re.finditer(r"^( *)[-*+] ", md, re.M) if m.group(1)]
    unit = min(indents) if indents else 2
    for line in md.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
        m = re.match(r"^( *)[-*+] (.*)$", line)
        if m and not fence and not line.lstrip().startswith("|"):
            level = min(len(m.group(1)) // unit, len(FORM_MARKS) - 1)
            text = m.group(2)
            mark = FORM_MARKS[level]
            if re.match(r"^[□○◦·■●▪-] ", text):        # 이미 기호로 시작하면 겹쳐 붙이지 않는다
                mark = ""
            if level == 0 and mark == "-" and escape:
                mark = "\\-"
            out.append("")
            out.append("　" * level + (f"{mark} " if mark else "") + text)
            out.append("")
        else:
            out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out))


def heading_kind(level, text):
    """제목 줄의 서식 종류: title · square · chapter · section · sub · topic · subtopic."""
    t = text.strip()
    if level == 1:
        return "title"
    if level == 2:
        return "square" if t.startswith("□") else "chapter"
    if level == 3:
        return "section"
    if level == 4:
        return "topic" if t.startswith("○") else "sub"
    return "subtopic"
