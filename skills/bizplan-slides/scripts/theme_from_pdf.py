#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""그림뿐인 템플릿(PDF·PNG·JPG)에서 쪽 이미지·모아보기·색 후보를 뽑아 시작용 테마 JSON을 만든다.

    python3 -B theme_from_pdf.py 템플릿.pdf --out 슬라이드/테마분석/ [--base report-blue] [--name my-theme]
    python3 -B theme_from_pdf.py 쪽1.png 쪽2.png --out 슬라이드/테마분석/

산출: <out>/p-01.png …, <out>/_모아보기.png, <out>/<name>.json(시작용 테마), 색 후보 표(화면 출력).
- 색은 근사치다. 모아보기를 보고 primary(강조)·bg(바탕)·text(글자)를 확인해 고친다.
- 구조(어떤 정보를 어떤 형식으로)는 이 도구가 뽑지 않는다. 모아보기를 보며 references/blueprints.md 형식으로 적는다.
- 만든 테마는 공개해도 되면 assets/themes/, 아니면 assets/themes/local/ 에 넣는다.
"""
import argparse
import colorsys
import glob
import json
import math
import os
import subprocess
import sys
from collections import Counter

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
THEME_DIR = os.path.normpath(os.path.join(HERE, "..", "assets", "themes"))


def pages(inputs, out):
    files = []
    for f in inputs:
        if f.lower().endswith(".pdf"):
            stem = os.path.join(out, "p")
            subprocess.run(["pdftoppm", "-r", "40", "-png", f, stem], check=True)
            files += sorted(glob.glob(stem + "-*.png"))
        else:
            files.append(f)
    return files


def sheet(files, out):
    ims = [Image.open(f).convert("RGB") for f in files]
    w = 320
    ims = [im.resize((w, round(im.height * w / im.width))) for im in ims]
    h = max(im.height for im in ims)
    cols = 5
    rows = math.ceil(len(ims) / cols)
    s = Image.new("RGB", (cols * (w + 8) + 8, rows * (h + 8) + 8), (128, 128, 128))
    for i, im in enumerate(ims):
        s.paste(im, (8 + (i % cols) * (w + 8), 8 + (i // cols) * (h + 8)))
    path = os.path.join(out, "_모아보기.png")
    s.save(path)
    return path


def hexc(c):
    return "".join(f"{v:02X}" for v in c)


def hls(c):
    return colorsys.rgb_to_hls(*(v / 255 for v in c))


def analyse(files):
    total, border, page_bg, dark = Counter(), Counter(), [], []
    for f in files:
        im = Image.open(f).convert("RGB")
        big = im.copy()
        big.thumbnail((480, 480))
        for p in list(big.get_flattened_data() if hasattr(big, "get_flattened_data") else big.getdata())[::3]:      # 글자색은 양자화 전 어두운 화소의 평균으로
            l, s_ = hls(p)[1], hls(p)[2]
            if l < 0.3 and s_ < 0.35:
                dark.append(p)
        im.thumbnail((240, 240))
        q = im.quantize(colors=12, method=Image.Quantize.MEDIANCUT).convert("RGB")
        px = list(q.get_flattened_data() if hasattr(q, "get_flattened_data") else q.getdata())
        snap = lambda c: tuple(min(255, round(v / 6) * 6) for v in c)
        cnt = Counter(snap(c) for c in px)
        total.update(cnt)
        W, H = q.size
        edge = [q.getpixel((x, 0)) for x in range(W)] + [q.getpixel((x, H - 1)) for x in range(W)] + \
               [q.getpixel((0, y)) for y in range(H)] + [q.getpixel((W - 1, y)) for y in range(H)]
        e = Counter(snap(c) for c in edge)
        border.update(e)
        page_bg.append(e.most_common(1)[0][0])
    return total, border, page_bg, dark


def pick(total, border, dark):
    bg = border.most_common(1)[0][0]
    allpx = sum(total.values())
    text = tuple(round(sum(p[i] for p in dark) / len(dark)) for i in range(3)) if dark else (17, 17, 17)
    sat = [(n, c) for c, n in total.items() if hls(c)[2] > 0.35 and 0.18 < hls(c)[1] < 0.85 and n > allpx * 0.003]
    primary = max(sat)[1] if sat else text      # 유채색이 거의 없으면(모노 템플릿) 글자색이 강조색
    greys = [(n, c) for c, n in total.items() if hls(c)[2] < 0.2 and 0.3 < hls(c)[1] < 0.7]
    muted = max(greys)[1] if greys else (95, 100, 110)
    lights = [(n, c) for c, n in total.items() if hls(c)[2] < 0.3 and 0.86 < hls(c)[1] < 0.985 and c != bg]
    soft = max(lights)[1] if lights else (238, 240, 244)
    accents = sorted(((n, c) for c, n in total.items() if hls(c)[2] > 0.35 and 0.18 < hls(c)[1] < 0.85
                      and n > allpx * 0.003 and abs(hls(c)[0] - hls(primary)[0]) > 0.04), reverse=True)
    series = [primary] + [c for _, c in accents[:3]]
    for t in (0.55, 0.8):          # 보조색이 모자라면 강조색 옅은 단계로 채운다
        if len(series) < 4:
            series.append(tuple(round(v + (255 - v) * t) for v in primary))
    if len(series) < 4:
        series.append(text)
    return {"bg": bg, "primary": primary, "text": text, "muted": muted, "soft": soft, "series": series}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", default="report-blue", help="머리·카드 형식을 빌려 올 기존 테마")
    ap.add_argument("--name")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    files = pages(a.inputs, a.out)
    if not files:
        sys.exit("쪽 이미지를 만들지 못했다")
    sp = sheet(files, a.out)
    total, border, page_bg, dark = analyse(files)
    c = pick(total, border, dark)
    w, h = Image.open(files[0]).size
    ratio = w / h
    full = sum(1 for b in page_bg if hls(b)[2] > 0.35 and hls(b)[1] < 0.8)
    with open(os.path.join(THEME_DIR, f"{a.base}.json"), encoding="utf-8") as f:
        theme = json.load(f)
    name = a.name or os.path.splitext(os.path.basename(a.inputs[0]))[0]
    theme.update(name=name, label=name, summary="[작성 필요: 바탕·강조색·머리 형식 한 줄]",
                 derived_from=f"{', '.join(os.path.basename(i) for i in a.inputs)} 색 추출(theme_from_pdf) + {a.base} 형식")
    theme["colors"].update(bg=hexc(c["bg"]), primary=hexc(c["primary"]), text=hexc(c["text"]),
                           muted=hexc(c["muted"]), soft=hexc(c["soft"]), series=[hexc(s) for s in c["series"]])
    if full:
        theme["styles"]["section"] = "full"
    jp = os.path.join(a.out, f"{name}.json")
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(theme, f, ensure_ascii=False, indent=2)
    print(f"쪽 {len(files)}장 · 비율 {ratio:.2f}({'16:9' if abs(ratio - 16 / 9) < 0.03 else '4:3' if abs(ratio - 4 / 3) < 0.03 else '기타'})"
          f" · 강조색 전면 쪽 {full}장")
    print(f"모아보기: {sp}")
    print("| 역할 | 색 | 근거 |\n|------|----|------|")
    print(f"| bg | #{hexc(c['bg'])} | 가장자리에 가장 많은 색 |")
    print(f"| primary | #{hexc(c['primary'])} | 채도 높은 색 중 가장 많은 색 |")
    print(f"| text | #{hexc(c['text'])} | 어두운 무채색 화소의 평균 |")
    print(f"| muted | #{hexc(c['muted'])} | 중간 밝기 회색 |")
    print(f"| soft | #{hexc(c['soft'])} | 바탕이 아닌 밝은 면(카드·표 머리) |")
    print(f"| series | {' '.join('#' + hexc(s) for s in c['series'])} | 강조색 + 색상이 다른 보조색 |")
    print(f"시작용 테마: {jp} — 모아보기와 대조해 고친 뒤 assets/themes/(local/)에 넣는다")


if __name__ == "__main__":
    main()
