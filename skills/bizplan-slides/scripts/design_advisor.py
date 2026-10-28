#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""원문 또는 기존 파싱 결과를 읽어 디자인을 추천한다. 원문·관계·덱은 수정하지 않는다.

    python3 -B design_advisor.py --units 단위.json --context 디자인문맥.json \
        --out 디자인분류.json --md 디자인분류.md --theme-out 선택테마.json
    python3 -B design_advisor.py --doc 사업계획서.md --item '로컬 식품' --tone '따뜻한' \
        --out 디자인분류.json --theme-out 선택테마.json

문맥: item, industry, audience, tone(문자열), theme(선택), brand_primary(6자리 hex),
      fixed_template(true면 지정 양식 보존, 테마 파일을 생성하지 않음).
표현 추천은 참고 정보다. 패턴을 바꾸거나 레퍼런스 파일을 가져오지 않는다.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
THEMES = HERE.parent / "assets/themes"
CATALOG = HERE.parents[1] / "bizplan-visual/assets/design-references.json"

# 업종의 정답 색이 아니라, 사용자가 준 디자인 문맥에 대응하는 후보 신호다.
THEME_HINTS = {
    "forest-mint": ["친환경", "환경", "순환", "재활용", "헬스케어", "돌봄", "건강", "안정", "청결", "민트", "녹색"],
    "warm-sand": ["식품", "음식", "푸드", "로컬", "관광", "여행", "공예", "전통", "따뜻", "내추럴", "오렌지", "베이지"],
    "plum-soft": ["교육", "학습", "문화", "콘텐츠", "창작", "뷰티", "웰니스", "부드러", "보라", "퍼플"],
    "lime-ink": ["실험", "대담", "강렬", "스포츠", "게임", "임팩트", "라임"],
    "report-blue": ["공공", "기관", "제조", "산업", "엔지니어링", "인공지능", "saas", "ai", "파랑", "블루"],
    "mono-line": ["흑백", "모노", "미니멀", "차분", "보수", "흑색"],
}

# 관계나 배치 순서를 새로 추론하지 않고 이미 정해진 패턴의 표현만 설명한다.
TREATMENTS = {
    "cover": "큰 제목·아이템 소개·여백, 보유한 제품 사진만 사용",
    "toc": "기존 목차 순서의 얇은 구획·번호 라벨",
    "section": "기존 섹션명의 큰 번호·여백",
    "closing": "기존 결론 문구와 간결한 강조 영역",
    "statement": "한 문장 대제목·넓은 여백",
    "bullets": "기존 항목의 들여쓰기·행간·강조만 조정",
    "cards": "대등한 카드의 동일 너비·번호 라벨, 기존 수렴 표시 보존",
    "radial": "기존 중심·주변 연결 유지, 중심만 강조",
    "kpi": "값·단위·설명을 구분한 숫자 강조 카드",
    "chart": "기존 축·계열·단위 유지, 자사와 핵심 계열만 강조",
    "tam": "기존 포함 관계·산식 유지, 층위의 농도와 라벨 위계",
    "compare": "기존 비교 기준·좌우 위치 유지, 자사 열만 강조",
    "before_after": "기존 전후 순서 유지, 도입 전은 중립색·도입 후는 강조색",
    "positioning": "기존 축·점 좌표 유지, 자사 점·라벨만 강조",
    "process": "기존 단계·화살표 방향 유지, 번호와 상태 구분",
    "timeline": "기존 시점·상태 유지, 날짜와 사건의 글자 위계",
    "gantt": "기존 과업·기간 유지, 완료·진행·예정의 채움과 선 구분",
    "table": "기존 행·열·합계 유지, 머리행·합계·자사 셀의 강조",
    "swot": "기존 4분면·항목 유지, 구획선과 제목 위계",
    "rows": "기존 라벨·내용 쌍 유지, 행 구분선과 라벨 강조",
    "pillars": "기존 상하 위계·연결 유지, 제목과 기둥의 강조",
    "team": "기존 역할·경력·증빙 유지, 동일 규격 프로필 카드",
    "image": "기존 증거물과 캡션 병치, 보유 자료의 비율 유지",
}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_source(path):
    """기존 파서의 단위 분리·관계 판별을 그대로 호출한다(새 판별 규칙 없음)."""
    from suggest_patterns import classify, parse_md
    units = parse_md(path)
    if not units:
        raise ValueError("원문에서 정보 단위를 찾지 못했다. 읽을 수 있는 본문을 확인한다")
    for unit in units:
        code, pattern, signal, alt, spec = classify(unit, str(Path(path).resolve().parent))
        unit.update(code=code, pattern=pattern, signal=signal, alt=alt, spec=spec)
    return units


def units_from_deck(path):
    """기존 덱의 type을 그대로 읽는다. 관계 코드를 새로 추론하지 않는다."""
    deck = read_json(path)
    slides = deck.get("slides") if isinstance(deck, dict) else None
    if not isinstance(slides, list) or not slides or any(not isinstance(s, dict) for s in slides):
        raise ValueError("덱 JSON에는 기존 슬라이드 객체 배열 slides가 있어야 한다")
    return [{"id": f"S{i:02d}", "code": "기존 패턴", "pattern": slide.get("type", ""),
             "spec": deepcopy(slide)} for i, slide in enumerate(slides, 1)]


def theme_path(name):
    # renderer와 같은 local 우선순위. 임의 경로는 CLI --theme로 명시할 수 있다.
    path = Path(name)
    if path.is_file():
        return path
    for root in (THEMES / "local", THEMES):
        path = root / (name + ".json")
        if path.is_file():
            return path
    raise ValueError(f"테마를 찾지 못했다: {name}")


def signal_in(hint, text):
    if hint.isascii():
        return re.search(r"(?<![a-z0-9])" + re.escape(hint) + r"(?![a-z0-9])", text) is not None
    return hint in text


def choose_theme(context, explicit=None):
    fields = [(context.get(k, "").lower(), weight)
              for k, weight in (("tone", 3), ("item", 2), ("industry", 2), ("audience", 1))]
    candidates = []
    for name, hints in THEME_HINTS.items():
        signals = [h for h in hints if any(signal_in(h, text) for text, _ in fields)]
        score = sum(max((weight for text, weight in fields if signal_in(h, text)), default=0) for h in signals)
        if signals:
            candidates.append({"theme": name, "signals": signals, "score": score})
    # 동률은 위 후보표 순서로 유지한다. 명시적 테마와 브랜드가 항상 우선이다.
    candidates.sort(key=lambda c: -c["score"])
    chosen = explicit or context.get("theme")
    if chosen:
        return chosen, "사용자가 지정한 테마 우선", candidates
    if candidates:
        best = candidates[0]
        return best["theme"], "디자인 문맥의 후보 신호: " + ", ".join(best["signals"]), candidates
    return "mono-line", "디자인 문맥이 부족해 중립 모노를 임시 추천", candidates


def white_contrast(hex_color):
    def linear(c):
        v = c / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    rgb = [linear(int(hex_color[i:i + 2], 16)) for i in (0, 2, 4)]
    return 1.05 / (sum(c * w for c, w in zip(rgb, (0.2126, 0.7152, 0.0722))) + 0.05)


def apply_accent(theme, raw):
    color = raw.lstrip("#").upper()
    if not re.fullmatch(r"[0-9A-F]{6}", color):
        raise ValueError("강조색은 #을 생략할 수 있는 6자리 hex여야 한다")
    original = color
    # 기존 렌더러의 강조면 위 흰 글자를 읽을 수 있는 같은 계열의 색을 쓴다.
    while white_contrast(color) < 4.5:
        color = "".join(f"{int(int(color[i:i + 2], 16) * 0.9):02X}" for i in (0, 2, 4))
    theme["colors"]["primary"] = color
    theme["colors"]["series"][0] = color
    theme["brand_primary"] = original
    return f"브랜드 원색 #{original}, 표현 강조색 #{color}" + (" (흰 글자 대비 조정)" if original != color else "")


def recommend(units, context, explicit_theme=None, accent=None):
    if not isinstance(units, list) or any(not isinstance(u, dict) for u in units):
        raise ValueError("단위.json은 suggest_patterns.py가 출력한 객체 배열이어야 한다")
    if not isinstance(context, dict):
        raise ValueError("디자인 문맥은 JSON 객체여야 한다")
    for key in ("item", "industry", "audience", "tone", "theme", "brand_primary"):
        if key in context and not isinstance(context[key], str):
            raise ValueError(f"문맥의 {key}는 문자열이어야 한다")
    if "fixed_template" in context and not isinstance(context["fixed_template"], bool):
        raise ValueError("fixed_template은 true 또는 false여야 한다")
    catalog = read_json(CATALOG)
    fixed = context.get("fixed_template", False)
    name, reason, candidates = choose_theme(context, explicit_theme)
    theme = None if fixed else deepcopy(read_json(theme_path(name)))
    if fixed:
        reason = "지정 양식의 색·레이아웃·로고 우선. 추천은 참고용으로만 사용"
    elif accent or context.get("brand_primary"):
        reason += " · " + apply_accent(theme, accent or context["brand_primary"])
    result = {"version": 1, "mode": "template-preserve" if fixed else "recommendation",
              "theme": theme["name"] if theme else None, "selection_reason": reason,
              "candidates": candidates, "palette": theme["colors"] if theme else None,
              "reference_researched_at": catalog["researched_at"], "units": []}
    for unit in units:
        pattern, code = unit.get("pattern", ""), unit.get("code", "")
        pending = not code or code == "—" or "?" in code or pattern not in TREATMENTS
        treatment = "확정된 관계·패턴이 없어 표현 추천 보류" if pending else TREATMENTS[pattern]
        refs = [r for r in catalog["references"] if r["status"] == "mapped" and pattern in r["patterns"]]
        refs.sort(key=lambda r: -(theme is not None and theme["name"] in r["themes"]))
        result["units"].append({"id": unit.get("id"), "code": code, "pattern": pattern,
                                "treatment": treatment, "review_required": pending,
                                "reference_keys": [] if pending else [r["template_key"] for r in refs[:3]],
                                "reference_status": "pending" if pending else "mapped" if refs else "existing-pattern"})
    return result, theme


def markdown(result, details=False):
    lines = ["# 디자인 적용", "", result["selection_reason"], "",
             f"테마: `{result['theme'] or '지정 양식 보존'}`", ""]
    if details:
        lines += [f"내부 조사 기준일: {result['reference_researched_at']}", "",
                  "| 단위 | 기존 관계 | 기존 패턴 | 표현 추천 | 참고 식별자 |", "|---|---|---|---|---|"]
    else:
        lines += ["| 단위 | 표현 추천 |", "|---|---|"]
    for u in result["units"]:
        cells = ([u["id"], u["code"], u["pattern"], u["treatment"], ", ".join(u["reference_keys"]) or "—"]
                 if details else [u["id"], u["treatment"]])
        lines.append("| " + " | ".join(str(c or "").replace("|", "\\|").replace("\n", " ") for c in cells) + " |")
    lines += ["", "기존 내용·논리 구조를 유지하고 디자인 적용만 제안했다."]
    return "\n".join(lines) + "\n"


def write(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--units", help="기존 suggest_patterns.py --json 출력(있으면 재사용)")
    source.add_argument("--deck", help="기존 deck.json의 슬라이드 순서·type을 그대로 재사용")
    source.add_argument("--doc", help="파싱 결과가 없을 때 읽을 UTF-8 Markdown 원문")
    ap.add_argument("--context", help="아이템·고객·목적·톤·브랜드 문맥 JSON")
    for key, label in (("item", "아이템"), ("industry", "분야"), ("audience", "고객·청중"), ("tone", "원하는 인상")):
        ap.add_argument("--" + key, help=label + "(에이전트가 대화·브리프에서 확인한 값)")
    ap.add_argument("--fixed-template", action="store_true", default=None, help="지정 양식 보존")
    ap.add_argument("--theme", help="명시적 테마 이름 또는 JSON 경로(문맥보다 우선)")
    ap.add_argument("--accent", help="명시적 브랜드 강조색(문맥보다 우선)")
    ap.add_argument("--out", required=True, help="분류 결과 JSON")
    ap.add_argument("--md", help="분류표 Markdown")
    ap.add_argument("--details", action="store_true", help="Markdown에 내부 관계·참고 식별자도 표시")
    ap.add_argument("--theme-out", help="PPT·HTML에 공통으로 넘길 선택 테마 JSON")
    args = ap.parse_args()
    try:
        # 기존 입력/덱을 결과로 덮어쓰는 실수를 방지한다.
        context = read_json(args.context) if args.context else {}
        if not isinstance(context, dict):
            raise ValueError("디자인 문맥은 JSON 객체여야 한다")
        if args.doc and "item" not in context:
            # 제목을 그대로 재사용한다. 업종·고객·성과를 새로 추론하지 않는다.
            lines = Path(args.doc).read_text(encoding="utf-8").splitlines()
            context["item"] = next((line[2:].strip() for line in lines if line.startswith("# ")), "")
        for key in ("item", "industry", "audience", "tone", "fixed_template"):
            value = getattr(args, key)
            if value is not None:
                context[key] = value
        units = read_json(args.units) if args.units else units_from_deck(args.deck) if args.deck else parse_source(args.doc)
        result, theme = recommend(units, context, args.theme, args.accent)
        inputs = {Path(p).resolve() for p in (args.units, args.deck, args.doc, args.context) if p}
        inputs.add(CATALOG.resolve())
        if not context.get("fixed_template"):
            inputs.add(theme_path(choose_theme(context, args.theme)[0]).resolve())
        outputs = [Path(p).resolve() for p in (args.out, args.md, args.theme_out) if p]
        if inputs.intersection(outputs) or len(set(outputs)) != len(outputs):
            raise ValueError("입력과 출력, 각 출력 파일은 서로 다른 경로여야 한다")
        result["input_mode"] = "units" if args.units else "existing-deck" if args.deck else "source-draft"
        if args.theme_out and theme:
            result["theme_file"] = str(Path(args.theme_out))
            write(args.theme_out, json.dumps(theme, ensure_ascii=False, indent=2) + "\n")
        write(args.out, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        if args.md:
            write(args.md, markdown(result, details=args.details))
        print(f"디자인 분류: {args.out} · {len(result['units'])}개 단위 · {result['theme'] or '지정 양식 보존'}")
        if args.theme_out and theme is None:
            print("지정 양식 보존: --theme-out 파일은 생성하지 않았다")
        if args.doc:
            print("원문 파싱 초안: 기존 관계 기준으로 확인한 뒤 디자인만 적용한다")
    except (ValueError, OSError, KeyError, UnicodeError) as exc:
        ap.error(str(exc))


if __name__ == "__main__":
    main()
