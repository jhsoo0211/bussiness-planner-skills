#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사업계획서 .md 사본에 소제목마다 '디벨롭 가이드' 상자를 끼운 코칭본 골격을 만든다.

    python3 -B coach_draft.py 사업계획서.md --out 사업계획서_코칭본.md [--review 검토리포트.md]

상자마다 미리 채우는 칸:
  - 작성법 기준: PSST 작성법(docs/psst.md)의 그 절 항목과 있음(✓)·없음(✗) 자동 판정 — 단어로 짐작한 것이라 본문을 읽고 고친다
  - 심사 관점: judge-insights·case-insights 요지
  - 지금 초안: 그 절의 [작성 필요]·[산정 예정]·[공고 확인 필요]·(팀 가설)·(계획안) 표기
  - 점수 영향: --review의 하위 항목 판정(△·X)을 O로 바꾸면 오르는 점수
  - 있으면 넣어 주세요: 그 절을 강하게 만들 사용자 자산 목록
비워 두는 칸(디벨롭 방법·초안 문장·말로 할 것·근거 확보)은 모델이 이 초안을 읽고 채운다.
기준 문서: bizplan/references/coaching.md (항목을 바꾸면 아래 CHECKS도 같이 바꾼다).
"""
import argparse
import re

FILL = "✍ (이 초안을 읽고 채운다)"
SKIP = ("보강 제안", "있으면 좋을", "요청 자료", "참고 자료", "조사용 프롬프트", "자체 일관성", "심화 안내", "작성 기준")
MARK = re.compile(r"\[(작성 필요|산정 예정|공고 확인 필요|미확보)[^\]]*\]|\((?:팀 )?가설[^)]*\)|\(계획안[^)]*\)|\(가정[^)]*\)|팀 판단")

# (이름, 소제목 신호, [(작성법 항목, 있음 판정 정규식)], 심사 관점, 부탁할 자산, 검토 하위 항목 신호)
CHECKS = [
    ("개요", r"개요|요약", [
        ("아이템명 공식(기술이 적용된, 혜택을 제공하는, 제품/서비스)", r"적용된|혜택"),
        ("사업 범주", r"범주"),
        ("핵심 요약 5줄(문제·솔루션·타겟·차별점·BM)", r"문제.{0,40}\|[\s\S]*솔루션|솔루션[\s\S]*차별|실현 가능성[\s\S]*성장 전략")],
     "10초 안에 문제 실재성·해결 대응·실행 증거가 보이는가(C 가장 먼저 보는 것 1·2·3·9)",
     "대표 이미지(앱 화면·시제품 사진 1장), 서비스 로고·이름", r"$^"),
    ("배경", r"시장 배경|배경 및 필요성|배경", [
        ("시장 배경 수치", r"\d[\d,.]*\s*(%|억|만|조|개|명|원|달러)"),
        ("출처 표기", r"출처|\((?:[^)]*?)(19|20)\d\d[.)]"),
        ("고객 상황(SPIN-S)", r"고객|이용자|사용자")],
     "거시 통계에서 우리 고객의 고통으로 좁혀 들어가는가(C 문제인식)",
     "관련 기사·통계 원문 캡처, 현장 사진", r"근거 수치"),
    ("문제", r"Pain|문제 인식|고객 문제|문제$", [
        ("Pain Point 3개", r"P3|③|3\."),
        ("발생 빈도·심각도", r"빈도|심각|하루|매일|매주|매월|주 ?\d+회|월 ?\d+회|\d+\s*(초|분|시간)"),
        ("해결되지 않을 때 손실(시간·비용·기회비용)", r"손실|기회비용|낭비|피해|비용이 들|재보정|다시"),
        ("실제 사례·인용·통계", r"인터뷰|설문|응답|“|”|\"[^\"]+\"|사례|\d+\s*명")],
     "직접 근거(인터뷰·관찰·민원)가 통계 인용보다 강하다, 자체 설문만이면 약하다(C 1)",
     "고객 인터뷰 메모·녹취 요약(표), 설문 결과(응답 수·기간), 불편 장면 사진·리뷰 캡처", r"문제 정의|근거 수치"),
    ("경쟁", r"한계|경쟁", [
        ("한계 2개 이상", r"한계"),
        ("경쟁사 비교표(회사명·주력·타겟·가격대·강점·약점·점유율)", r"\|.*\|.*\|"),
        ("가격대", r"원|달러|가격"),
        ("차별화(기능·가격·서비스·기술)·경쟁 우위 방안", r"차별|우위")],
     "경쟁사 한계를 우리가 어떻게 해소하는지까지, 실명 비교(review 체크포인트 4)",
     "경쟁 서비스 화면·가격표 캡처, 직접 써 본 비교 메모, 사용 후기", r"$^"),
    ("필요성", r"필요성|왜 지금", [
        ("필요성 2개", r"필요"),
        ("해결 시 이점(Need-payoff)", r"이점|효과|해결되면|줄인|높인"),
        ("니즈 증거(성장률·성공 사례·인터뷰)", r"성장|사례|인터뷰|설문"),
        ("지원사업비로 해결할 핵심 기능", r"지원|사업비|협약")],
     "규제·정책·시장 변화와 연결한 타이밍(C 문제인식)",
     "정책·규제 변화 문서, 시장 성장 통계 원문", r"시급성"),
    ("타겟", r"타겟|고객 현황|페르소나|목표 시장 고객", [
        ("1차·2차 타겟(연령·직업·소득·특징·구매 동기)", r"1차|2차|연령"),
        ("페르소나", r"페르소나"),
        ("니즈·트렌드", r"니즈|트렌드")],
     "세분화가 측정·접근·구매력·니즈 동질성 기준으로 타당한가(review 체크포인트 9)",
     "고객 설문 응답 분포, 페르소나 근거 인터뷰", r"문제 정의"),
    ("실행 증거", r"실행 증거|현황|준비 정도|증빙 자산|한 일", [
        ("시제품·MVP·데모(링크·사진)", r"MVP|시제품|데모|https?://|운영 중|출시"),
        ("사용자·매출 지표(기간·수치)", r"\d+\s*(명|건|원|%)|가입|리텐션|매출"),
        ("LOI·MOU·PoC(상대·상태)", r"LOI|MOU|PoC|의향|협약"),
        ("수상·언론·선정·웹/SNS", r"수상|언론|선정|출품|SNS|블로그")],
     "만들어 실행한 것은 문서에 실물로(링크·캡처), 없으면 협약기간 내 제작 일정으로(C 가장 먼저 보는 것 3·9)",
     "서비스·시제품 화면 캡처와 링크, 운영 지표 캡처(기간 명시), LOI·PoC 메일, 수상·출품 확인서", r"증빙"),
    ("기능", r"핵심 기능|기술|구현|솔루션 개요", [
        ("핵심 기술 3개(난이도·확보 방안)", r"S3|③|기술"),
        ("기술 리스크 2개와 대응", r"리스크|위험"),
        ("기능마다 푸는 문제", r"P\d|문제"),
        ("성능 정량치·검증 경로", r"정확도|성능|측정|테스트|검증")],
     "성능 정량치·제3자 검증 경로, 분야 필수 인증·규제(C 실현가능성)",
     "프로토타입·MVP 화면/영상(1분), 기술 구조도, 성능 테스트 결과, 특허 출원서(번호·상태)",
     r"기능·구현|대응 구조|증빙"),
    ("일정", r"일정|로드맵|마일스톤", [
        ("월차별 활동·산출물", r"산출물"),
        ("마일스톤", r"마일스톤|M\d"),
        ("예산 연결", r"예산|금액|비용"),
        ("협약일 기준 명시", r"협약")],
     "이미 검증된 것과 앞으로 확인할 것을 구분(author-insights solution)",
     "이미 한 일의 기록(개발 일지·커밋 로그·회의록)", r"일정"),
    ("사업비", r"사업비|예산|자금", [
        ("비목 표(세부 내용·금액)", r"비목|\|.*금액"),
        ("비율", r"비율|%"),
        ("항목별 산출 근거(단가 × 수량)", r"산출 근거|×"),
        ("1단계·2단계 구분", r"1단계|2단계")],
     "산출 근거·합계 검산(check_tables)·공고 비목 기준",
     "장비·외주 견적서, 단가 근거(가격표 캡처)", r"예산"),
    ("BM", r"비즈니스 모델|수익|BM", [
        ("주요 수익원·과금 방식", r"수익원|과금|구독|이용료"),
        ("예상 객단가", r"객단가|단가|\d[\d,]*\s*원|달러"),
        ("비용 구조(고정비·변동비)", r"고정비|변동비|원가|비용 구조"),
        ("가격 전략(초기·프리미엄·근거)", r"가격")],
     "매출 가정을 채널·판매량·단가·전환율로 분해(C 가장 먼저 보는 것 8)",
     "가격 테스트·지불 의향 설문 결과, 사전 예약·대기 명단, 구매의향서(LOI)", r"BM"),
    ("시장 규모", r"시장 규모|TAM|SAM|SOM", [
        ("TAM·SAM·SOM 층위", r"TAM[\s\S]*SAM[\s\S]*SOM"),
        ("층위별 산식", r"×|산식"),
        ("출처", r"출처|\((?:[^)]*?)(19|20)\d\d|QY|리포트|Research"),
        ("가장 큰 경쟁자 벤치마크", r"벤치마크|1위|경쟁자")],
     "TAM→SAM→SOM으로 좁히고 층위마다 산식·출처, SOM 200억 권장선은 예창패 노하우(공식 기준 아님)(J §4)",
     "통계·리포트 원문(표 캡처), 상향식 산정 근거(고객 수 출처)", r"시장 규모"),
    ("진입", r"진입|마케팅", [
        ("초기 고객 확보(0~6개월) 전략", r"초기"),
        ("성장기(6~12개월) 전략", r"성장기|확장|1~2년"),
        ("구체성(접촉·견적·예산·기대성과)", r"접촉|LOI|견적|\d+\s*(곳|건|명)")],
     "범용 계획(홈페이지·SNS·인플루언서)은 감점 — 접촉 완료·견적·예산·기대성과로(J §4)",
     "고객사·파트너 접촉 기록(메일·회의록), PoC 일정 확약 메일, 랜딩 페이지·SNS 링크와 반응 지표",
     r"마케팅"),
    ("목표", r"목표", [
        ("단·중·장기 구분", r"단기[\s\S]*중기[\s\S]*장기"),
        ("핵심 지표(수치)", r"지표|KPI|\d+\s*(건|명|곳|%|원)"),
        ("확장 계획(제품·시장·파트너십)", r"확장")],
     "시장진입 계획 뒤에 비전을 잇는다 — 비전 생략 금지(J §4)",
     "이미 측정한 지표(가입·사용·만족도), 목표치 산정 근거", r"목표"),
    ("SWOT", r"SWOT", [
        ("강점·약점·기회·위협", r"강점[\s\S]*약점[\s\S]*기회[\s\S]*위협"),
        ("교차 전략(SO·WO·ST·WT)", r"SO|WO|ST|WT")],
     "약점을 숨기지 않고 WO·WT로 보완 경로를 보인다",
     "(SWOT 근거가 된 조사·인터뷰 자료)", r"$^"),
    ("대표자", r"대표자", [
        ("관련 경력 2개", r"경력|경험|\d+\s*년"),
        ("핵심 역량 3개", r"역량"),
        ("창업 동기", r"동기")],
     "스펙 나열이 아니라 핵심 리스크를 맡을 수 있는가(J §4, C 팀 구성)",
     "이력 요약(블라인드: 학교·직장명 ○○), 포트폴리오·결과물 링크, 수상·자격·공모전 기록", r"대표자"),
    ("팀", r"팀 현황|팀원|팀 구성", [
        ("구분·담당·보유 역량·확정/예정 표", r"\|.*\|"),
        ("확정/예정 표기", r"확정|예정"),
        ("리스크 ↔ 담당자", r"리스크")],
     "핵심 리스크와 담당자 매핑, 공백은 확보 계획으로",
     "팀원 이력 요약·합류 확약, 채용 공고·후보", r"구성·보완"),
    ("협력", r"협력", [
        ("기관명·협력 내용", r"기관|협력"),
        ("협력 시기", r"(19|20)\d\d|M\d|시기"),
        ("기대 효과", r"효과")],
     "협력 단계를 증빙 범위 안에서 최상위 격식 표현으로(J §4 사다리)",
     "MOU·협약서·자문 확약 메일·공문(단계 그대로)", r"협력"),
]


def sections(lines):
    """(제목 줄 번호, 수준, 제목) 목록."""
    out = []
    for i, l in enumerate(lines):
        m = re.match(r"^(#{2,4})\s+(.*)$", l)
        if m:
            out.append((i, len(m.group(1)), m.group(2).strip()))
    return out


def review_items(path):
    """검토 리포트 득점표 → [(섹션, 하위 항목, 판정, 득점, 배점)]."""
    out = []
    text = open(path, encoding="utf-8").read()
    for row in re.findall(r"^\|\s*([^|]+?)\s*\|\s*\d+\s*\|\s*\d+\s*\|(.+)\|\s*$", text, re.M):
        sec, body = row
        # 하위 항목은 " · "(띄운 가운뎃점)로 나뉜다. 이름 안의 붙은 가운뎃점(근거 수치·출처)은 살린다
        for chunk in re.split(r"\s+·\s+", body):
            m = re.match(r"\s*(.+?)\s*([OX△])\s*\((\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)\)", chunk)
            if m:
                out.append((sec.strip(), m.group(1).strip(), m.group(2), float(m.group(3)), float(m.group(4))))
    score = re.search(r"점수[:：]?\s*\**\s*(\d+)\s*점", text)
    return out, (int(score.group(1)) if score else None)


def pick(title):
    for c in CHECKS:
        if re.search(c[1], title):
            return c
    return None


def box(title, body, check, items):
    text = "\n".join(body)
    marks = sorted(set(m.group(0) for m in MARK.finditer(text)))
    lines = [f"> **디벨롭 가이드 — {title}** *(제출 전 삭제)*", ">"]
    if check:
        plain = MARK.sub(" ", re.sub(r"\*\*\[[^\]]*\]\*\*", " ", text))   # 빈칸 표기 속 낱말('[작성 필요: 경력]')은 있음으로 세지 않는다
        got = [f"{'✓' if re.search(rx, plain) else '✗'} {label}" for label, rx in check[2]]
        lines.append(f"> - **작성법 기준**(자동 판정 — 확인 필요): {' / '.join(got)}")
        lines.append(f"> - **심사 관점**: {check[3]}")
    else:
        lines.append("> - **작성법 기준**: (해당 체크리스트 없음 — coaching.md 3절에서 가까운 항목을 고른다)")
    lines.append(f"> - **지금 초안**: {'채울 칸 ' + str(len(marks)) + '곳 — ' + ' · '.join(marks) if marks else '미확보·가설 표기 없음'}"
                 f" / {FILL}")
    lines.append(f"> - **디벨롭 방법**: {FILL}")
    lines.append(f"> - **초안 문장** *(사실 확인 후 ○○를 채워 쓴다)*: {FILL}")
    lines.append(f"> - **말로 할 것** *(발표·질의응답)*: {FILL}")
    gains = []
    if check and items:
        for sec, name, mark, got, mx in items:
            if mark != "O" and re.search(check[5], name):
                gains.append(f"{sec} '{name}' {mark}→O +{mx - got:g}점")
    lines.append(f"> - **점수 영향**: {' · '.join(gains) if gains else ('—' if items else '검토 후 계산')}")
    lines.append(f"> - **근거 확보**: {FILL}")
    if check:
        lines.append(f"> - **있으면 넣어 주세요**: {check[4]}")
    return lines, marks, gains


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("doc")
    ap.add_argument("--out", required=True)
    ap.add_argument("--review")
    a = ap.parse_args()
    lines = open(a.doc, encoding="utf-8").read().splitlines()
    items, score = review_items(a.review) if a.review else ([], None)
    secs = sections(lines)
    inserts, all_marks, all_gains, assets = {}, [], [], []
    for k, (i, lvl, title) in enumerate(secs):
        nxt = secs[k + 1][0] if k + 1 < len(secs) else len(lines)
        has_child = k + 1 < len(secs) and secs[k + 1][1] > lvl and secs[k + 1][0] < nxt + 1
        parent = next((t for j, (_, l2, t) in reversed(list(enumerate(secs[:k]))) if l2 < lvl), "")
        if any(s in title or s in parent for s in SKIP):
            continue
        body = lines[i + 1:nxt]
        if has_child and not any(l.strip() for l in body):
            continue
        check = pick(title) or pick(parent)
        b, marks, gains = box(title, body, check, items)
        end = nxt
        while end > i + 1 and not lines[end - 1].strip():
            end -= 1
        inserts[end] = [""] + b
        all_marks += marks
        all_gains += [(float(g.rsplit("+", 1)[1].rstrip("점")), g, title) for g in gains]
        if check:
            assets.append((title, check[4]))
    out = []
    for n, l in enumerate(lines):
        if n in inserts:
            out += inserts[n]
            out.append("")
        out.append(l)
    if len(lines) in inserts:
        out += inserts[len(lines)]
    seen, top = set(), []
    for pts, g, t in sorted(all_gains, reverse=True):
        key = g.split(" ", 2)[1] if " " in g else g
        if key not in seen:
            seen.add(key)
            top.append(f"{len(top) + 1}. ✍ (행동) — (기한) — {g} — {t}")
        if len(top) == 3:
            break
    head = ["# 코칭본 — 제출본이 아니다", "",
            "> 초안 사본에 소제목마다 **디벨롭 가이드** 상자를 넣었다. 제출본은 `사업계획서.md`다. "
            "기준: PSST 작성법(docs/psst.md) · 심사 성향(judge-insights) · 사례 체크포인트(case-insights) — 형식은 bizplan/references/coaching.md.",
            "", "## 한눈에 — 제출 수준까지 남은 것", "",
            "| 지금 | 목표 | 가장 큰 공백 |", "|------|------|--------------|",
            f"| {f'{score}점(검토 리포트) · ' if score is not None else ''}채울 칸 {len(all_marks)}곳 | ✍ (과락선·목표 점수) | ✍ |", "",
            "**점수가 가장 많이 오르는 행동 3개**", ""] + (top or ["1. ✍ (검토 리포트를 주면 점수 영향순으로 뽑는다)"]) + [
            "", "**모아 주실 자료**(있는 것만 — 받으면 반영할 절)", ""] + \
           [f"- [ ] {asset} → {t}" for t, asset in assets] + [
            "", "**제출 전 지울 것**: 디벨롭 가이드 상자 전부, 작성 기준 인용 블록, 섹션별 심화 안내, 보강 제안, "
            "[작성 필요] 표기(0개가 될 때까지)", "", "---", ""]
    open(a.out, "w", encoding="utf-8").write("\n".join(head + out) + "\n")
    print(f"코칭본 골격: {a.out} — 상자 {len(inserts)}개, 채울 칸 {len(all_marks)}곳, "
          f"점수 영향 {len(all_gains)}건{'' if a.review else '(검토 리포트 없음)'}")
    print(f"남은 빈칸(✍): {sum(1 for l in head + out if '✍' in l)}줄 — 이 초안을 읽고 채운다")


if __name__ == "__main__":
    main()
