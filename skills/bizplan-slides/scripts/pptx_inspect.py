#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""발표 템플릿(.pptx/.potx)을 분석해 채우기 계획에 필요한 정보를 출력한다.

출력: 슬라이드 크기, 테마 색·글꼴, 레이아웃별 자리표시자, 기존 슬라이드의 도형·글자, 경고.
    python3 -B pptx_inspect.py 템플릿.pptx [--json 프로필.json]
경고 예: 16:9 슬라이드에 4:3 크기 자리표시자, 동아시아(한글) 글꼴 미지정, 레이아웃 없이 샘플 슬라이드만 있는 템플릿.
"""
import argparse
import io
import json
import sys
import zipfile
import re

from pptx import Presentation
from pptx.util import Emu

NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
DEFAULT_LAYOUTS = {"Title Slide", "Title and Content", "Section Header", "Two Content", "Comparison",
                   "Title Only", "Blank", "Content with Caption", "Picture with Caption",
                   "Title and Vertical Text", "Vertical Title and Text"}


def open_presentation(path):
    """.pptx는 그대로, .potx(서식 파일)는 내용 형식만 프레젠테이션으로 바꿔 메모리에서 연다."""
    with zipfile.ZipFile(path) as z:
        ct = z.read("[Content_Types].xml").decode("utf-8")
        if "presentationml.template.main+xml" not in ct:
            return Presentation(path)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
            for item in z.infolist():
                data = z.read(item.filename)
                if item.filename == "[Content_Types].xml":
                    data = ct.replace("presentationml.template.main+xml",
                                      "presentationml.presentation.main+xml").encode("utf-8")
                out.writestr(item, data)
    buf.seek(0)
    return Presentation(buf)


def _box(shape, sw, sh):
    """도형 위치·크기를 슬라이드 대비 %로."""
    if shape.left is None or shape.width is None:
        return None
    return [round(shape.left / sw * 100, 1), round(shape.top / sh * 100, 1),
            round(shape.width / sw * 100, 1), round(shape.height / sh * 100, 1)]


def _theme(path):
    """테마 XML에서 색(dk1·lt1·accent1~6)과 글꼴(major/minor의 latin·ea)을 읽는다."""
    colors, fonts = {}, {}
    with zipfile.ZipFile(path) as z:
        names = sorted(n for n in z.namelist() if re.match(r"ppt/theme/theme\d+\.xml$", n))
        if not names:
            return colors, fonts
        xml = z.read(names[0]).decode("utf-8", "ignore")
    for key in ["dk1", "lt1", "dk2", "lt2"] + [f"accent{i}" for i in range(1, 7)]:
        m = re.search(rf"<a:{key}>.*?(?:srgbClr val=\"([0-9A-Fa-f]{{6}})\"|lastClr=\"([0-9A-Fa-f]{{6}})\")", xml, re.S)
        if m:
            colors[key] = "#" + (m.group(1) or m.group(2)).upper()
    for kind in ("major", "minor"):
        m = re.search(rf"<a:{kind}Font>(.*?)</a:{kind}Font>", xml, re.S)
        if m:
            block = m.group(1)
            latin = re.search(r'<a:latin typeface="([^"]*)"', block)
            ea = re.search(r'<a:ea typeface="([^"]*)"', block)
            hang = re.search(r'<a:font script="Hang" typeface="([^"]*)"', block)
            fonts[kind] = {"latin": latin.group(1) if latin else "",
                           "ea": ea.group(1) if ea else "",
                           "Hang": hang.group(1) if hang else ""}
    return colors, fonts


def inspect(path):
    prs = open_presentation(path)
    sw, sh = prs.slide_width, prs.slide_height
    ratio = sw / sh
    profile = {
        "file": path,
        "slide_size_in": [round(Emu(sw).inches, 3), round(Emu(sh).inches, 3)],
        "aspect": "16:9" if abs(ratio - 16 / 9) < 0.02 else "4:3" if abs(ratio - 4 / 3) < 0.02 else f"{ratio:.3f}",
        "layouts": [], "slides": [], "warnings": [],
    }
    profile["theme_colors"], profile["theme_fonts"] = _theme(path)

    narrow = []
    for li, layout in enumerate(prs.slide_layouts):
        phs = []
        for ph in layout.placeholders:
            phs.append({"idx": ph.placeholder_format.idx, "type": str(ph.placeholder_format.type).split(".")[-1].split(" ")[0],
                        "name": ph.name, "box_pct": _box(ph, sw, sh)})
        profile["layouts"].append({"index": li, "name": layout.name, "placeholders": phs})
        # 16:9인데 본문 자리표시자들의 오른쪽 끝이 80%에 못 미치면 4:3에서 늘리지 않은 레이아웃일 가능성
        rights = [p["box_pct"][0] + p["box_pct"][2] for p in phs
                  if p["box_pct"] and p["type"] not in ("DATE", "FOOTER", "SLIDE_NUMBER")]
        if profile["aspect"] == "16:9" and rights and max(rights) < 80:
            narrow.append(layout.name)
    if narrow:
        profile["warnings"].append(
            f"16:9 슬라이드인데 자리표시자가 왼쪽 80% 안에 몰린 레이아웃: {', '.join(narrow)} (4:3 잔재 의심) — "
            "pptx_build.py --stretch-placeholders로 가로를 맞추거나 템플릿을 수정")

    for si, slide in enumerate(prs.slides):
        shapes = []
        for sp in slide.shapes:
            item = {"id": sp.shape_id, "name": sp.name, "kind": sp.shape_type and str(sp.shape_type).split(".")[-1].split(" ")[0],
                    "box_pct": _box(sp, sw, sh)}
            if sp.is_placeholder:
                item["placeholder_idx"] = sp.placeholder_format.idx
            if sp.has_text_frame and sp.text_frame.text.strip():
                item["text"] = sp.text_frame.text.strip()[:120]
            if getattr(sp, "has_table", False) and sp.has_table:
                t = sp.table
                item["table"] = [len(t.rows), len(t.columns)]
            shapes.append(item)
        profile["slides"].append({"index": si + 1, "layout": slide.slide_layout.name, "shapes": shapes})

    custom = [l["name"] for l in profile["layouts"] if l["name"] not in DEFAULT_LAYOUTS]
    if profile["slides"] and not custom:
        profile["warnings"].append(
            "사용자 정의 레이아웃이 없다 — 디자인이 샘플 슬라이드에 들어 있을 가능성이 높다. "
            "spec에서 from_slide(샘플 슬라이드 복제 + 글자 교체)를 우선 사용")
    fonts = profile["theme_fonts"]
    if fonts and not any(f.get("ea") or f.get("Hang") for f in fonts.values()):
        profile["warnings"].append("테마에 한글(동아시아) 글꼴이 없다 — pptx_build.py가 --ea-font(기본 '맑은 고딕')로 지정한다")
    return profile


def _print(profile):
    print(f"파일: {profile['file']}")
    print(f"크기: {profile['slide_size_in'][0]}×{profile['slide_size_in'][1]}in ({profile['aspect']})")
    if profile["theme_colors"]:
        print("테마 색: " + ", ".join(f"{k}={v}" for k, v in profile["theme_colors"].items()))
    if profile["theme_fonts"]:
        print("테마 글꼴: " + "; ".join(f"{k}: latin={v['latin']} ea={v['ea'] or v['Hang'] or '-'}"
                                      for k, v in profile["theme_fonts"].items()))
    print("\n[레이아웃]")
    for l in profile["layouts"]:
        phs = ", ".join(f"{p['idx']}:{p['type']}{p['box_pct']}" for p in l["placeholders"])
        print(f"  {l['index']:>2} {l['name']} — {phs or '자리표시자 없음'}")
    print("\n[기존 슬라이드]")
    for s in profile["slides"]:
        print(f"  #{s['index']} (레이아웃: {s['layout']})")
        for sp in s["shapes"]:
            extra = f" \"{sp['text']}\"" if sp.get("text") else ""
            if sp.get("table"):
                extra += f" 표{sp['table'][0]}×{sp['table'][1]}"
            ph = f" ph{sp['placeholder_idx']}" if "placeholder_idx" in sp else ""
            print(f"     - [{sp['id']}] {sp['name']} ({sp['kind']}{ph}) {sp['box_pct']}{extra}")
    if profile["warnings"]:
        print("\n[경고]")
        for w in profile["warnings"]:
            print("  ! " + w)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template")
    ap.add_argument("--json", help="프로필을 JSON으로 저장할 경로")
    args = ap.parse_args()
    profile = inspect(args.template)
    _print(profile)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
        print(f"\nJSON 저장: {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
