#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""발표·문서 파일을 PDF로 내보낸다.

    python3 -B export_pdf.py 발표.pptx            # LibreOffice(soffice) 사용 — .pptx/.docx/.hwp 등
    python3 -B export_pdf.py 슬라이드.html        # Chromium(Playwright, Node) 사용 — 1280×720 장 단위
    [--out 출력.pdf] [--size 1280x720]

LibreOffice 렌더는 설치된 글꼴로 그린다. 템플릿 글꼴(예: 맑은 고딕)이 없으면 대체 글꼴로 바뀌어
줄바꿈·넘침이 PowerPoint와 다를 수 있다 — 최종 제출 PDF는 템플릿 글꼴이 있는 환경에서 다시 내보낸다.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def office_to_pdf(src, out):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice(soffice)가 없다 — 설치하거나 PowerPoint/Keynote에서 PDF로 내보낸다")
    with tempfile.TemporaryDirectory() as tmp:
        # 사용자 프로필을 임시 폴더로 분리해 동시 실행·첫 실행 대화상자를 피한다
        cmd = [soffice, f"-env:UserInstallation=file://{tmp}/profile", "--headless",
               "--convert-to", "pdf", "--outdir", tmp, os.path.abspath(src)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        made = os.path.join(tmp, os.path.splitext(os.path.basename(src))[0] + ".pdf")
        if not os.path.exists(made):
            raise RuntimeError(f"변환 실패: {r.stderr.strip() or r.stdout.strip()}")
        shutil.move(made, out)
    return out


def html_to_pdf(src, out, size):
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node가 없다 — 브라우저 인쇄(배경 그래픽 켬, 여백 없음, 용지 1280×720px)로 PDF를 만든다")
    w, h = size.split("x")
    r = subprocess.run([node, os.path.join(HERE, "html_to_pdf.cjs"), os.path.abspath(src), os.path.abspath(out), w, h],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "html_to_pdf.cjs 실패 — Playwright 설치 여부 확인")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("--out")
    ap.add_argument("--size", default="1280x720", help="HTML 슬라이드 한 장 크기(px)")
    args = ap.parse_args()
    out = args.out or os.path.splitext(args.src)[0] + ".pdf"
    try:
        if args.src.lower().endswith((".html", ".htm")):
            html_to_pdf(args.src, out, args.size)
        else:
            office_to_pdf(args.src, out)
    except (RuntimeError, subprocess.TimeoutExpired) as e:
        print(f"PDF 변환 실패: {e}", file=sys.stderr)
        return 1
    print(f"PDF: {out}")
    try:
        info = subprocess.run(["pdfinfo", out], capture_output=True, text=True).stdout
        print("  " + " / ".join(l.strip() for l in info.splitlines() if l.startswith(("Pages", "Page size"))))
    except FileNotFoundError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
