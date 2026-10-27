#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF를 장별 PNG와 한눈에 보는 모아보기(contact sheet)로 렌더해 눈 검수를 돕는다.

    python3 -B preview.py 발표.pdf [--out 미리보기폴더] [--dpi 60] [--cols 3]
필요: pdftoppm(poppler-utils), Pillow.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--out")
    ap.add_argument("--dpi", type=int, default=60)
    ap.add_argument("--cols", type=int, default=3)
    args = ap.parse_args()
    out = args.out or os.path.splitext(args.pdf)[0] + "_미리보기"
    os.makedirs(out, exist_ok=True)
    if not shutil.which("pdftoppm"):
        print("pdftoppm이 없다 — poppler-utils를 설치하거나 PDF 뷰어로 장마다 확인한다", file=sys.stderr)
        return 1
    subprocess.run(["pdftoppm", "-r", str(args.dpi), "-png", args.pdf, os.path.join(out, "slide")], check=True)
    pages = sorted(glob.glob(os.path.join(out, "slide-*.png")))
    from PIL import Image, ImageDraw
    ims = [Image.open(p) for p in pages]
    if not ims:
        print("렌더된 쪽이 없다", file=sys.stderr)
        return 1
    w, h = ims[0].size
    cols = min(args.cols, len(ims))
    rows = (len(ims) + cols - 1) // cols
    pad = 8
    sheet = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad + 16) + pad), "#94a3b8")
    draw = ImageDraw.Draw(sheet)
    for i, im in enumerate(ims):
        x = pad + (i % cols) * (w + pad)
        y = pad + (i // cols) * (h + pad + 16)
        draw.text((x, y), f"{i + 1}", fill="white")
        sheet.paste(im, (x, y + 14))
    path = os.path.join(out, "_모아보기.png")
    sheet.save(path)
    print(f"{len(ims)}장 렌더: {out}\n모아보기: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
