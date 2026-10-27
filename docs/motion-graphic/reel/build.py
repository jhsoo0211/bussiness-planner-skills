#!/usr/bin/env python3
"""bizplan-reel.src.html -> bizplan-reel.html (Geist · Geist Mono · Pretendard 서브셋을 base64로 넣은 단일 파일).

필요: pip install fonttools brotli
글꼴: npm 패키지 geist (dist/fonts), pretendard (dist/web/static/woff2)

    python build.py --geist <geist>/dist/fonts --pretendard <pretendard>/dist/web/static/woff2
"""

import argparse
import base64
import io
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent


def faces(geist, pretendard):
    # geist 1.8: 800 = UltraBlack, 900 = Black
    yield "Geist", {w: geist / "geist-sans" / f"Geist-{n}.woff2" for w, n in
                    {600: "SemiBold", 700: "Bold", 800: "UltraBlack", 900: "Black"}.items()}
    yield "Geist Mono", {w: geist / "geist-mono" / f"GeistMono-{n}.woff2" for w, n in
                         {600: "SemiBold", 700: "Bold"}.items()}
    yield "BP", {w: pretendard / f"Pretendard-{n}.woff2" for w, n in
                 {600: "SemiBold", 700: "Bold", 800: "ExtraBold", 900: "Black"}.items()}


def subset_woff2(path, text):
    font = TTFont(path)
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["*"]
    subsetter = subset.Subsetter(options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    buffer = io.BytesIO()
    font.flavor = "woff2"
    font.save(buffer)
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--geist", required=True, type=Path)
    parser.add_argument("--pretendard", required=True, type=Path)
    parser.add_argument("--src", default=HERE / "bizplan-reel.src.html", type=Path)
    parser.add_argument("--out", default=HERE / "bizplan-reel.html", type=Path)
    args = parser.parse_args()

    source = args.src.read_text(encoding="utf-8")
    text = "".join(sorted(set(source) | {chr(c) for c in range(32, 127)}))
    rules = []
    for family, weights in faces(args.geist, args.pretendard):
        for weight, path in weights.items():
            data = base64.b64encode(subset_woff2(path, text)).decode("ascii")
            rules.append("@font-face{font-family:'%s';font-weight:%d;font-style:normal;"
                         "src:url(data:font/woff2;base64,%s) format('woff2')}" % (family, weight, data))
    args.out.write_text(source.replace("/*@FONTS@*/", "\n".join(rules)), encoding="utf-8")
    print(f"wrote {args.out} ({args.out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
