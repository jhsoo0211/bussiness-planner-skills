#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사업계획서(.md)를 정보 단위로 나누고 단위마다 관계 유형·추천 패턴·스펙 초안을 뽑는다(파싱 도우미).

    python3 -B suggest_patterns.py 사업계획서.md [--out 슬라이드/파싱표.md] [--json 슬라이드/단위.json]
                                   [--deck 슬라이드/초안덱.json] [--outline 발표구성안.md]

- 단위: 소제목 아래의 표 하나·목록 하나·그림 자리 하나·문단 묶음 하나.
- 관계 유형(R1~R23)·패턴은 bizplan-visual/references/info-patterns.md 기준이다. 신호로 고른 '초안'이다 — 파싱표를 보고 확정한다.
- 스펙 초안은 원문 글을 줄이지 않고 그대로 옮긴다(내용이 빠지지 않게). 제목은 소제목을 넣어 두니 결론형으로 다시 쓴다.
- --deck: 모든 단위 초안을 표지·마무리와 묶어 theme_deck.py로 바로 그릴 수 있는 덱으로 쓴다(자료 미리보기용).
- --outline: bizplan-pitch 구성안(B 표)을 읽어 장마다 추천 패턴과 끌어올 단위를 짝짓는다.
메타 절(보강 제안·요청 자료·조사용 프롬프트·자체 일관성 점검·심화 안내)과 인용(>)·코드 블록은 건너뛴다.
"""
import argparse
import json
import os
import re
import sys

SKIP_HEADINGS = ("보강 제안", "요청 자료", "조사용 프롬프트", "자체 일관성", "심화 안내", "작성 기준", "있으면 좋을")
DATE = r"(\d{4}[.\-/]\d{1,2}|\d{1,2}월|M\d+|\d+Q|[1-4]분기|\d{4}년)"
NUM_UNIT = r"[+\-~약]?\s*\d[\d,.]*\s*(%|조|억|만|천|원|명|건|개|배|점|회|곳|종|대|년|개월|시간|분|초|p|pt|MPa|t|kg)"
MARKER = re.compile(r"^\s*(?:[-*+]|\d+[.)]|[□○◦·▪■●◆①-⑳])\s+")


def clean(t):
    return re.sub(r"\s+", " ", t).strip()


def split_title(text):
    """'**제목** — 설명' / '제목: 설명' 을 (제목, 설명)으로. 못 나누면 (글, None)."""
    m = re.match(r"^\*\*(.+?)\*\*\s*[:：—–-]?\s*(.*)$", text)
    if m and len(m.group(1)) <= 40:
        return m.group(1).strip(), (m.group(2).strip() or None)
    for sep in (" — ", " – ", ": ", "：", " - "):
        if sep in text:
            a, b = text.split(sep, 1)
            if 1 <= len(a.strip()) <= 30:
                return a.strip(), b.strip()
    return text, None


# ---------------------------------------------------------------- 마크다운 → 단위

def parse_md(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    units, path_ = [], []
    skip_level = None
    block, kind = [], None
    in_code = False

    def flush():
        nonlocal block, kind
        if block and kind and skip_level is None:
            where = " > ".join(path_[1:] if len(path_) > 1 else path_) or "(머리)"
            units.append({"where": where, "kind": kind, "lines": block[:]})
        block, kind = [], None

    for raw in lines:
        if raw.strip().startswith("```"):
            in_code = not in_code
            flush()
            continue
        if in_code:
            continue
        h = re.match(r"^(#{1,6})\s+(.*)$", raw)
        if h:
            flush()
            level, text = len(h.group(1)), clean(h.group(2))
            path_ = path_[:level - 1] + [text]
            if skip_level is not None and level <= skip_level:
                skip_level = None
            if any(k in text for k in SKIP_HEADINGS):
                skip_level = level
            continue
        s = raw.rstrip()
        if not s.strip():
            if kind == "para":
                flush()
            continue
        if s.lstrip().startswith(">"):
            continue
        if s.lstrip().startswith("|"):
            k = "table"
        elif re.match(r"^\s*\[(이미지|그림|사진|도식)[:：]", s) or re.match(r"^\s*!\[", s):
            k = "image"
        elif MARKER.match(s) or (kind == "list" and s.startswith("  ")):
            k = "list"
        else:
            k = "para"
        if k != kind or k == "image":
            flush()
            kind = k
        block.append(s)
    flush()
    # 목록 바로 뒤 문단은 결론 후보로 붙인다
    out = []
    for u in units:
        if u["kind"] == "para" and out and out[-1]["kind"] == "list" and out[-1]["where"] == u["where"]:
            out[-1]["after"] = " ".join(clean(l) for l in u["lines"])
            continue
        out.append(u)
    for i, u in enumerate(out, 1):
        u["id"] = f"U{i:02d}"
    return out


def table_rows(lines):
    rows = []
    for l in lines:
        cells = [clean(c) for c in l.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append(cells)
    return (rows[0], rows[1:]) if rows else ([], [])


def list_items(lines):
    items = []
    for l in lines:
        indent = len(l) - len(l.lstrip())
        text = clean(MARKER.sub("", l, count=1))
        if indent >= 2 and items:
            items[-1]["sub"].append(text)
        else:
            items.append({"text": text, "sub": []})
    return items


# ---------------------------------------------------------------- 기간 해석(간트)

def parse_period(cell):
    c = cell.replace(" ", "")
    m = re.search(r"M(\d+)[-~–]M?(\d+)", c)
    if m:
        return int(m.group(1)), int(m.group(2)), "M"
    m = re.search(r"M(\d+)", c)
    if m:
        return int(m.group(1)), int(m.group(1)), "M"
    m = re.search(r"(\d{4})\.(\d{1,2})[-~–](?:(\d{4})\.)?(\d{1,2})", c)
    if m:
        y1, m1 = int(m.group(1)), int(m.group(2))
        y2 = int(m.group(3) or y1)
        m2 = int(m.group(4))
        return (y1, m1), (y2, m2), "YM"
    m = re.search(r"(\d{1,2})월[-~–](\d{1,2})월", c)
    if m:
        return int(m.group(1)), int(m.group(2)), "월"
    m = re.search(r"(\d{1,2})[-~–](\d{1,2})개월", c)
    if m:
        return int(m.group(1)), int(m.group(2)), "M"
    m = re.search(r"([1-4])Q[-~–]([1-4])Q|([1-4])분기[-~–]([1-4])분기", c)
    if m:
        a, b = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        return int(a), int(b), "Q"
    m = re.search(r"([1-4])Q|([1-4])분기", c)
    if m:
        q = int(m.group(1) or m.group(2))
        return q, q, "Q"
    return None


def gantt_from(header, rows):
    pc = next((j for j, h in enumerate(header) if re.search(r"기간|일정|시기|월|분기", h)), None)
    if pc is None:
        return None
    parsed = [parse_period(r[pc]) if pc < len(r) else None for r in rows]
    ok = [p for p in parsed if p]
    if len(ok) < max(2, 0.6 * len(rows)):
        return None
    unit = ok[0][2]
    if unit == "YM":
        y0, m0 = min(p[0] for p in ok)
        idx = lambda ym: (ym[0] - y0) * 12 + ym[1] - m0 + 1
        span = max(idx(p[1]) for p in ok)
        periods = []
        for k in range(span):
            mm = (m0 - 1 + k) % 12 + 1
            periods.append(f"{mm}월")
        conv = lambda p: (idx(p[0]), idx(p[1]))
    else:
        span = max(p[1] for p in ok)
        lab = {"M": "M{}", "월": "{}월", "Q": "{}Q"}[unit]
        periods = [lab.format(k) for k in range(1, span + 1)]
        conv = lambda p: (p[0], p[1])
    others = [j for j in range(len(header)) if j != pc]
    task_c = others[0] if others else pc
    label_c = others[-1] if len(others) > 1 else None
    out = []
    for r, p in zip(rows, parsed):
        if not p:
            continue
        a, b = conv(p)
        row = {"task": r[task_c], "start": a, "end": b}
        if label_c is not None and label_c < len(r) and r[label_c]:
            row["label"] = r[label_c]
        out.append(row)
    return {"periods": periods, "rows": out}


# ---------------------------------------------------------------- 관계 판별

def classify(u, doc_dir="."):
    """(관계 코드, 패턴, 판별 신호, 대안) 과 스펙 초안을 돌려준다."""
    head = u["where"].split(" > ")[-1]
    title = re.sub(r"^[\dⅠ-Ⅹ]+(-\d+)*[.)]?\s*", "", head).split("(")[0].strip() or head
    ctx = u["where"]
    base = {"title": title}

    if u["kind"] == "image":
        t = clean(u["lines"][0])
        m = re.search(r"→\s*제작됨[:：]\s*(\S+)", t) or re.search(r"!\[[^\]]*\]\(([^)]+)\)", t)
        img = m.group(1) if m else re.sub(r"\s*→.*$", "", t)
        if not img.startswith("["):
            full = img if os.path.isabs(img) else os.path.join(doc_dir, img)
            img = os.path.abspath(full) if os.path.isfile(full) else f"[이미지: {img} — 파일 없음]"
        return ("R22", "image", "그림 자리·그림 링크", "", dict(base, type="image", image=img))

    if u["kind"] == "table":
        header, rows = table_rows(u["lines"])
        hs = " ".join(header)
        ncol = len(header)
        first = [r[0] for r in rows if r]
        if re.search(r"강점|약점|기회|위협|SWOT", hs + " ".join(first)):
            return ("R18", "swot", "SWOT 표", "table", dict(base, type="table", header=header, rows=rows))
        if any(re.match(r"(TAM|SAM|SOM)", f) for f in first):
            items = [{"value": (r[1] if len(r) > 1 else ""), "desc": " / ".join(r[2:]) or None} for r in rows[:3]]
            items = [{k: v for k, v in it.items() if v} for it in items]
            return ("R9", "tam", "첫 열 TAM·SAM·SOM", "table", dict(base, type="tam", items=items))
        g = gantt_from(header, rows) if re.search(r"기간|일정|시기|월|분기", hs) else None
        if g:
            return ("R15", "gantt", f"기간 열 + 행 {len(rows)}개가 기간으로 읽힘", "table",
                    dict(base, type="gantt", periods=g["periods"], rows=g["rows"]))
        if re.search(r"성명|이름", hs) and re.search(r"역할|직위|담당|직책", hs):
            nc = next(j for j, h in enumerate(header) if re.search(r"성명|이름", h))
            rc = next(j for j, h in enumerate(header) if re.search(r"역할|직위|담당|직책", h))
            items = []
            for r in rows[:4]:
                career = [f"{header[j]}: {r[j]}" for j in range(ncol) if j not in (nc, rc) and j < len(r) and r[j]]
                it = {"name": r[nc], "role": r[rc] if rc < len(r) else ""}
                if career:
                    it["career"] = career
                items.append(it)
            return ("R21", "team", "성명·역할 열", "table", dict(base, type="team", items=items))
        if re.search(r"금액|비목|예산|산출", hs) and not re.search(r"정부지원|자기부담", hs + " ".join(first)):
            total = bool(first and re.match(r"합계|총계|소계", first[-1]))
            return ("R16", "table", f"예산·금액 표 {len(rows)}행 — check_tables.py로 검산", "",
                    dict(base, type="table", header=header, rows=rows, total=total))
        if re.search(r"정부지원|자기부담|수입|지출", hs) or any(re.fullmatch(r"(정부지원금?|자기부담금?|수입|지출)(\s*합계)?", f) for f in first):
            return ("R17", "table", "정부지원·자기부담(수입·지출) 구분", "tables 2개로 나누기",
                    dict(base, type="table", header=header, rows=rows, total=bool(first and re.match(r"합계|총계|소계", first[-1]))))
        if re.search(r"리스크|위험|약점|문제|질문|Pain", hs) and re.search(r"대응|해결|답|보완|솔루션|기능", hs):
            items = []
            for r in rows[:6]:
                cells = [c for c in r if c]
                lab = r[0]
                ttl = r[1] if len(r) > 1 else r[0]
                body = " · ".join(c for c in r[2:] if c) or None
                it = {"label": lab, "title": ttl}
                if body:
                    it["body"] = body
                items.append(it)
            return ("R19", "rows", "문제·리스크 열 ↔ 대응·해결 열", "table", dict(base, type="rows", items=items))
        years = [h for h in header if re.fullmatch(r"(19|20)\d\d(년)?", h)]
        if len(years) >= 3 and all(re.fullmatch(r"[\d,.\-]+", c.replace(" ", "")) for r in rows for c in r[1:] if c):
            series = [{"name": r[0], "values": [float(c.replace(",", "")) if c else 0 for c in r[1:]]} for r in rows]
            return ("R6", "chart", "연도 열 3개 이상 + 숫자", "table",
                    dict(base, type="chart", chart={"kind": "line" if len(rows) > 1 else "column",
                                                    "categories": years, "series": series}))
        if ncol == 2 and 2 <= len(rows) <= 4 and all(re.search(NUM_UNIT, r[1]) for r in rows if len(r) > 1):
            items = [{"value": re.search(NUM_UNIT + r".*", r[1]).group(0), "label": r[0]} for r in rows]
            return ("R5", "kpi", "이름 + 수치 2열", "table", dict(base, type="kpi", items=items))
        if re.search(r"기존|경쟁|자사|비교|대비|vs", hs, re.I) or re.search(r"(^|\s)[O△X○×](\s|$)", " ".join(c for r in rows for c in r)):
            return ("R10", "table", "비교 열(기존·경쟁·자사) 또는 O/△/X", "compare(criteria)",
                    dict(base, type="table", header=header, rows=rows))
        if ncol == 2 and len(rows) <= 6:
            items = [{"label": r[0], "title": r[1] if len(r) > 1 else ""} for r in rows]
            return ("R19", "rows", "2열(라벨 → 내용)", "table", dict(base, type="rows", items=items))
        total = bool(first and re.match(r"합계|총계|소계", first[-1]))
        note = "행이 8개 넘음 → 본문엔 핵심 행만, 전체는 부록" if len(rows) > 8 else ""
        return ("R16", "table", f"다속성 표 {len(rows)}행×{ncol}열" + (f" — {note}" if note else ""), "",
                dict(base, type="table", header=header, rows=rows, total=total))

    if u["kind"] == "list":
        items = list_items(u["lines"])
        texts = [it["text"] for it in items]
        joined = " ".join(texts + [ctx])
        n = len(items)
        after = u.get("after", "")
        marks = sum(bool(re.search(r"\[(작성 필요|산정 예정|미확보)", t)) for t in texts)
        if marks and marks >= n - 0:
            return ("—", "(미확보)", f"항목 {n}개 모두 미확보 표기", "슬라이드엔 자리 표시로", None)
        pairs = [split_title(t) for t in texts]
        if re.search(r"TAM|SAM|SOM", joined):
            vals = [re.search(r"(TAM|SAM|SOM)[^\d]*(" + NUM_UNIT[0:] + r")", t) for t in texts]
            items_ = [{"value": (m.group(2) if m else "[작성 필요: 값]"), "desc": t} for m, t in zip(vals, texts)][:3]
            if len(items_) == 3:
                return ("R9", "tam", "TAM·SAM·SOM 언급", "", dict(base, type="tam", items=items_))
        if re.search(r"강점|약점|기회|위협", joined) and n >= 4:
            return ("R18", "swot", "강점·약점·기회·위협", "", None)
        if sum(bool(re.search(DATE, t)) for t in texts) >= max(3, 0.6 * n) and 3 <= n <= 6:
            its = []
            for t in texts:
                m = re.search(DATE + r"[^\s,)]*", t)
                rest = clean(t.replace(m.group(0), "", 1)).strip(" :—-·") if m else t
                its.append({"when": m.group(0) if m else "", "title": rest})
            return ("R14", "timeline", "항목마다 날짜", "gantt(기간이면)", dict(base, type="timeline", items=its))
        stepish = sum(bool(re.match(r"(\d+\s*단계|STEP\s*\d|\d+\)|①|②|③)", t) or "→" in t) for t in texts)
        if (stepish >= max(2, 0.6 * n) or (re.search(r"절차|흐름|프로세스|단계", ctx) and re.match(r"\s*\d+[.)]", u["lines"][0]))) \
                and 3 <= n <= 6:
            its = [{"title": a, **({"body": b} if b else {})} for a, b in pairs]
            return ("R13", "process", "단계·흐름 신호", "cards(순서 없으면)", dict(base, type="process", items=its))
        nums = [re.search(NUM_UNIT, t) for t in texts]
        if 2 <= n <= 4 and all(nums) and all(len(t) <= 50 for t in texts):
            its = [{"value": m.group(0).strip(), "label": clean(t.replace(m.group(0), "", 1)).strip(" :—-·")} for m, t in zip(nums, texts)]
            return ("R5", "kpi", "짧은 항목마다 수치+단위", "", dict(base, type="kpi", items=its))
        if re.search(r"기존에는|도입 전|도입 후|As-?Is|To-?Be|이전|이후", joined, re.I) and n >= 2:
            return ("R11", "before_after", "전·후 신호", "compare", None)
        if re.search(r"리스크|위험", joined) and re.search(r"대응|→|보완", joined):
            its = [{"label": a, "title": b or a} for a, b in pairs][:6]
            return ("R19", "rows", "리스크 → 대응", "", dict(base, type="rows", items=its))
        labeled = sum(1 for a, b in pairs if b)
        if labeled >= max(2, 0.7 * n):
            short = all(len(a) <= 14 for a, b in pairs if b)
            if 2 <= n <= 4 and not short:
                its = [{"title": a, "body": b or ""} for a, b in pairs]
                its = [{k: v for k, v in it.items() if v} for it in its]
                conv = bool(re.search(r"따라서|이에|이를 위해|결론|즉", after))
                spec = dict(base, type="cards", items=its)
                if conv:
                    spec.update(converge=True, callout=after)
                return ("R3" if conv else "R2", "cards", "형제 항목 + '제목 — 설명'" + (" + 뒤에 결론 문장" if conv else ""),
                        "rows", spec)
            its = [{"label": a, "title": b or ""} for a, b in pairs][:6]
            return ("R19", "rows", "'라벨: 내용' 쌍", "cards", dict(base, type="rows", items=its))
        if re.search(r"요인|원인|이해관계자|니즈", ctx + joined) and 3 <= n <= 6:
            its = [{"title": a, **({"body": b} if b else {})} for a, b in pairs]
            return ("R4", "radial", "요인·니즈 + 형제 항목", "cards", dict(base, type="radial", center=title, items=its))
        bl = []
        for it in items:
            bl.append(it["text"])
            if it["sub"]:
                bl.append(it["sub"])
        if after:
            bl.append(after)
        return ("R2" if 2 <= n <= 4 else "—", "bullets", f"목록 {n}개(관계 신호 없음)", "cards" if 2 <= n <= 4 else "rows",
                dict(base, type="bullets", bullets=bl))

    text = " ".join(clean(l) for l in u["lines"])
    nums = re.findall(NUM_UNIT, text)
    if len(nums) >= 2:
        return ("R5?", "bullets", f"문단 속 수치 {len(nums)}개 — kpi로 꺼낼지 검토", "kpi", dict(base, type="bullets", bullets=[text]))
    return ("R1", "statement" if len(text) <= 60 else "bullets", "문단", "",
            dict(base, type="statement", title=text) if len(text) <= 60 else dict(base, type="bullets", bullets=[text]))


# ---------------------------------------------------------------- 구성안 짝짓기

VISUAL_HINTS = [
    (r"간트|일정표|추진 일정", "gantt"), (r"타임라인|연혁|이정표", "timeline"), (r"포지셔닝", "positioning"),
    (r"TAM|SAM|SOM|시장 ?규모", "tam"), (r"SWOT", "swot"), (r"비교표|O/△/X|대조|비교", "compare"),
    (r"그래프|차트|추이|막대", "chart"), (r"숫자|KPI|지표|수치", "kpi"), (r"흐름도|프로세스|단계|STEP|흐름", "process"),
    (r"팀|역할 카드|팀원", "team"), (r"표지", "cover"), (r"클로징|마무리|Q&A", "closing"),
    (r"캡처|화면|사진|데모", "image"), (r"개념도|도식|구성도|4분면", "image"), (r"카드|\d칸|아이콘", "cards"),
    (r"표\b|표\(", "table"),
]


def tokens(t):
    return set(re.findall(r"[가-힣A-Za-z0-9]{2,}", t))


def outline_map(path, units):
    lines = [l for l in open(path, encoding="utf-8").read().splitlines() if l.strip().startswith("|")]
    rows = [[clean(c) for c in l.strip().strip("|").split("|")] for l in lines]
    rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c) for c in r if c)]
    header_i = next((i for i, r in enumerate(rows) if any("슬라이드" in c for c in r) and any("시각" in c for c in r)), None)
    if header_i is None:
        sys.exit("구성안에서 '슬라이드 … 시각자료' 머리가 있는 표를 찾지 못했다")
    head = rows[header_i]
    col = lambda key: next((j for j, h in enumerate(head) if key in h), None)
    cs, ct, cm, cv = col("슬라이드"), col("제목"), col("메시지"), col("시각")
    out = []
    for r in rows[header_i + 1:]:
        if len(r) < len(head) or not re.match(r"\d", r[cs]):
            continue
        vis = r[cv] if cv is not None else ""
        ttl = r[ct] if ct is not None else ""
        if re.search(r"표지", ttl):
            kind = "cover"
        elif re.search(r"클로징|마무리|Q&A", ttl):
            kind = "closing"
        else:       # 시각자료 칸에서 가장 먼저 나온 형식이 주인공이다
            hits = [(m.start(), k) for pat, k in VISUAL_HINTS for m in [re.search(pat, vis)] if m]
            kind = min(hits)[1] if hits else "bullets"
        tk = tokens(" ".join(r[j] for j in (ct, cm, cv) if j is not None))
        scored = []
        for u in units:
            body = u["where"] + " " + " ".join(u["lines"])
            s = len(tk & tokens(body))
            if s:
                scored.append((s, u["id"]))
        scored.sort(reverse=True)
        out.append({"slide": r[cs], "title": r[ct] if ct is not None else "", "message": r[cm] if cm is not None else "",
                    "visual": vis, "pattern": kind, "units": [i for _, i in scored[:3]]})
    return out


# ---------------------------------------------------------------- 실행

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("doc")
    ap.add_argument("--out")
    ap.add_argument("--json")
    ap.add_argument("--deck")
    ap.add_argument("--outline")
    a = ap.parse_args()

    units = parse_md(a.doc)
    rows = []
    for u in units:
        code, pat, why, alt, spec = classify(u, os.path.dirname(os.path.abspath(a.doc)))
        u.update(code=code, pattern=pat, signal=why, alt=alt, spec=spec)
        n = len(spec.get("items") or spec.get("rows") or spec.get("bullets") or []) if spec else 0
        rows.append(f"| {u['id']} | {u['where']} | {u['kind']} | {code} | {why} | `{pat}` | {alt or '—'} | {n or '—'} |")
    md = ["# 파싱표 (suggest_patterns 초안 — 확인 후 확정)", "",
          f"원문: `{a.doc}` · 단위 {len(units)}개. 관계 코드는 bizplan-visual/references/info-patterns.md.", "",
          "| 단위 | 원문 위치 | 형태 | 관계 | 판별 신호 | 추천 패턴 | 대안 | 항목 |",
          "|------|-----------|------|------|-----------|-----------|------|------|"] + rows
    if a.outline:
        om = outline_map(a.outline, units)
        md += ["", "## 구성안 ↔ 단위 짝", "", "| 장 | 제목 | 시각자료(구성안) | 추천 패턴 | 끌어올 단위 |",
               "|----|------|------------------|-----------|-------------|"]
        for o in om:
            md.append(f"| {o['slide']} | {o['title']} | {o['visual']} | `{o['pattern']}` | {', '.join(o['units']) or '—'} |")
    text = "\n".join(md) + "\n"
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
        print(f"파싱표: {a.out}")
    else:
        print(text)
    if a.json:
        json.dump([{k: u[k] for k in ("id", "where", "kind", "code", "pattern", "signal", "alt", "spec")} for u in units],
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"단위 초안: {a.json}")
    if a.deck:
        title = next((l[2:].strip() for l in open(a.doc, encoding="utf-8") if l.startswith("# ")), "사업계획서")
        slides = [{"type": "cover", "title": title, "eyebrow": "자료 미리보기(초안)"}]
        slides += [dict(u["spec"], eyebrow=u["id"]) for u in units if u["spec"]]
        slides.append({"type": "closing"})
        json.dump({"meta": {}, "slides": slides}, open(a.deck, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"초안 덱: {a.deck} ({len(slides)}장) — theme_deck.py --check 로 검사 후 렌더")


if __name__ == "__main__":
    main()
