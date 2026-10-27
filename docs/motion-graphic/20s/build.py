#!/usr/bin/env python3
"""bizplan-20s.src.html -> bizplan-20s.html (Pretendard 서브셋을 base64로 인라인한 단일 파일).

필요: pip install fonttools brotli
폰트: Pretendard 정적 woff2 폴더 (npm 패키지 pretendard의 dist/web/static/woff2)

    python build.py --fonts /path/to/pretendard/dist/web/static/woff2
"""

import argparse
import base64
import io
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
WEIGHTS = {500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold"}


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
    parser.add_argument("--fonts", required=True, help="Pretendard static woff2 folder")
    parser.add_argument("--src", default=HERE / "bizplan-20s.src.html")
    parser.add_argument("--out", default=HERE / "bizplan-20s.html")
    args = parser.parse_args()

    source = Path(args.src).read_text(encoding="utf-8")
    text = "".join(sorted(set(source) | {chr(c) for c in range(32, 127)}))

    faces = []
    for weight, name in WEIGHTS.items():
        data = subset_woff2(Path(args.fonts) / f"Pretendard-{name}.woff2", text)
        encoded = base64.b64encode(data).decode("ascii")
        faces.append(
            "@font-face{font-family:'BP';font-weight:%d;font-style:normal;"
            "src:url(data:font/woff2;base64,%s) format('woff2')}" % (weight, encoded)
        )

    Path(args.out).write_text(source.replace("/*@FONTS@*/", "\n".join(faces)), encoding="utf-8")
    print(f"wrote {args.out} ({Path(args.out).stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
