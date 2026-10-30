#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사업계획서 .md 하나로 제출용 파일을 한 번에 만든다 — 완성 문서 모드(bizplan-document)의 마지막 단계.

    python3 -B build_document.py 사업계획서.md [--visuals 시각자료/spec.json] [--style form|plain]
                                 [--formats docx,hwpx,pdf] [--hwp] [--pages-limit 10] [--accent 2a78d6]
순서: check_tables 검산 → (spec이 있으면) html_visuals.py --print로 그림 PNG → md_to_docx → export_pdf(LibreOffice)
→ preview(쪽 PNG·모아보기) → md_to_hwpx. 없는 도구(soffice·pdftoppm·python-hwpx·Node)는 건너뛰고 알린다.
끝에 보고: 쪽 수(공고 분량 대비) · 그림 수 · 남은 [이미지: …] 자리 · 사진·화면 점선 자리 · ○○ 개수 · 경고.
결과 파일은 .md와 같은 폴더에 같은 이름(.docx · .hwpx · .pdf · _미리보기/)으로 둔다.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.dirname(os.path.dirname(HERE))           # 설치 뒤에도 스킬 폴더는 형제로 놓인다
VISUAL = os.path.join(SKILLS, "bizplan-visual", "scripts", "html_visuals.py")
SLIDES = os.path.join(SKILLS, "bizplan-slides", "scripts")


def run(cmd, cwd=None):
    r = subprocess.run([sys.executable, "-B", *cmd], capture_output=True, text=True, cwd=cwd)
    return r.returncode, (r.stdout + r.stderr).strip()


def placeholders(spec_path):
    """spec에서 실물로 바꿀 자리를 센다 — 사진 점선 틀(photos, src 없음)과 그린 화면 틀(screens, src 없음)
    → [(그림 id, '사진'|'화면', 무엇)]."""
    if not spec_path or not os.path.exists(spec_path):
        return []
    spec = json.load(open(spec_path, encoding="utf-8"))
    out = []
    for v in spec.get("visuals", []):
        kind = {"photos": ("items", "사진"), "screens": ("screens", "화면")}.get(v.get("type"))
        if not kind:
            continue
        for it in v.get(kind[0], []):
            if not it.get("src"):
                out.append((v.get("id", "?"), kind[1], it.get("what") or it.get("title") or it.get("caption", "")))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("md")
    ap.add_argument("--visuals", help="시각자료 spec.json — 주면 --print로 PNG를 먼저 다시 만든다")
    ap.add_argument("--style", choices=("form", "plain"), default="form", help="form = 완성 문서 서식(기본)")
    ap.add_argument("--formats", default="docx,hwpx,pdf", help="쉼표로: docx, hwpx, pdf (pdf는 docx에서 만든다)")
    ap.add_argument("--hwp", action="store_true", help=".hwp도 함께")
    ap.add_argument("--pages-limit", type=int, help="공고 분량(쪽) — 넘어도 줄이지 않고 보고만 한다")
    ap.add_argument("--accent", help="그림 강조색(예: 0B3D91)")
    a = ap.parse_args()

    md = os.path.abspath(a.md)
    folder, stem = os.path.dirname(md), os.path.splitext(os.path.basename(md))[0]
    formats = {f.strip() for f in a.formats.split(",") if f.strip()}
    if "pdf" in formats:
        formats.add("docx")
    report, made = [], []

    code, out = run([os.path.join(HERE, "check_tables.py"), md])
    errors = [l.strip() for l in out.splitlines() if l.strip().startswith("✕")]
    holds = [l.strip() for l in out.splitlines() if l.strip().startswith("△")]
    report.append(f"검산: {'오류 ' + str(len(errors)) + '건' if errors else '오류 없음'}"
                  + (f" · 판단 보류 {len(holds)}건(○○ 칸이 있어 합계를 확인하지 못함 — 값이 들어오면 다시 돌린다)" if holds else ""))
    report += [f"  {e}" for e in errors + holds]

    visual_warn = []
    if a.visuals:
        spec = os.path.abspath(a.visuals)
        cmd = [VISUAL, spec, "--out", os.path.dirname(spec), "--print"] + (["--accent", a.accent] if a.accent else [])
        code, out = run(cmd, cwd=folder)
        visual_warn = [l for l in out.splitlines() if l.startswith("[확인]")]
        png = [l for l in out.splitlines() if l.startswith("PNG")]
        report.append(f"그림: {png[0].split(':')[0] if png else out.splitlines()[-1] if out else '실패'} · 경고 {len(visual_warn)}건")
        report += [f"  {w}" for w in visual_warn]

    docx = os.path.join(folder, stem + ".docx")
    if "docx" in formats:
        cmd = [os.path.join(HERE, "md_to_docx.py"), md, docx, "--style", a.style]
        if a.style == "plain":
            cmd.append("--gov-bullets")
        code, out = run(cmd, cwd=folder)
        report.append(out.splitlines()[0] if code == 0 else f"docx 실패: {out[-400:]}")
        if code == 0:
            made.append(docx)

    pdf = os.path.join(folder, stem + ".pdf")
    if "pdf" in formats and os.path.exists(docx):
        if shutil.which("fc-list"):                  # 문서 글꼴(md_to_docx 기본 '맑은 고딕')이 없으면 LibreOffice가 대체 글꼴로 그린다
            fonts = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True).stdout
            if not re.search(r"맑은 고딕|Malgun Gothic", fonts):
                report.append("PDF 글꼴: 맑은 고딕이 없어 대체 글꼴로 그렸다 — 줄바꿈·쪽 수가 한글·워드와 다를 수 있다")
        if shutil.which("soffice") or shutil.which("libreoffice"):
            code, out = run([os.path.join(SLIDES, "export_pdf.py"), docx, "--out", pdf], cwd=folder)
            if code == 0 and os.path.exists(pdf):
                made.append(pdf)
                if shutil.which("pdftoppm"):
                    run([os.path.join(SLIDES, "preview.py"), pdf, "--dpi", "80"], cwd=folder)
                    made.append(os.path.join(folder, stem + "_미리보기", "_모아보기.png"))
            else:
                report.append(f"pdf 실패: {out[-300:]}")
        else:
            report.append("pdf 건너뜀: LibreOffice(soffice)가 없다 — docx를 워드·한글에서 PDF로 저장한다")

    if "hwpx" in formats:
        hwpx = os.path.join(folder, stem + ".hwpx")
        cmd = [os.path.join(HERE, "md_to_hwpx.py"), md, hwpx] + (["--style", "form"] if a.style == "form" else [])
        cmd += ["--hwp"] if a.hwp else []
        code, out = run(cmd, cwd=folder)
        if "python-hwpx가 없다" in out:
            report.append("hwpx 건너뜀: python-hwpx가 없다(pip install python-hwpx)")
        else:
            report += [l for l in out.splitlines() if l.startswith(("저장", "구조 검증"))]
            if os.path.exists(hwpx):
                made.append(hwpx)

    text = open(md, encoding="utf-8").read()
    pages = None
    if os.path.exists(pdf) and shutil.which("pdfinfo"):
        info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
        m = re.search(r"Pages:\s+(\d+)", info)
        pages = int(m.group(1)) if m else None
    figs = len(re.findall(r"!\[[^\]]*\]\([^)]+\)", text)) + sum(
        len(re.findall(r"=", l)) for l in text.splitlines() if l.startswith("이미지:"))
    slots = re.findall(r"\[이미지:[^\]]*\]", text)
    holes = placeholders(os.path.abspath(a.visuals)) if a.visuals else []
    report.append("")
    if pages is not None:
        limit = f" / 공고 분량 {a.pages_limit}쪽" + (f" (+{pages - a.pages_limit}쪽 — 줄일 후보를 작성가이드에)"
                                                    if a.pages_limit and pages > a.pages_limit else "")
        report.append(f"쪽 수: {pages}쪽" + (limit if a.pages_limit else ""))
    report.append(f"그림: 본문 {figs}개 · 남은 [이미지: …] 자리 {len(slots)}곳 · 실물로 바꿀 사진·화면 자리 {len(holes)}곳 · ○○ {text.count('○○')}개")
    for vid, kind, what in holes:
        report.append(f"  - 교체할 {kind} {vid}: {what}")
    print("\n".join(report))
    print("만든 파일:")
    for f in made:
        print(f"  {os.path.relpath(f, folder)}")
    print("확인: 미리보기를 쪽마다 열어 헤드라인만 쪽 끝에 남은 곳·빈 공간·표 칸 끊김·그림 숫자를 본다. hwpx는 한글에서 1회 연다.")
    print("참고: 이 PDF는 LibreOffice로 그린 미리보기다 — 한국어 줄 끝에서 숫자가 갈라질 수 있다('6 / 11건'). "
          "제출용 PDF는 한글·워드에서 docx·hwpx를 열어 저장한다.")
    return 1 if errors or visual_warn else 0


if __name__ == "__main__":
    sys.exit(main())
