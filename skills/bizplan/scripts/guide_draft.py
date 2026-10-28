#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사업계획서 .md를 읽어 목차 순서대로 '작성 가이드'(별도 산출물) 골격을 만든다.

    python3 -B guide_draft.py 사업계획서.md --out 작성가이드.md [--review 검토리포트.md] [--brief 브리프.md]

사업계획서에 아무것도 끼워 넣지 않는다. 목차(소제목)마다 아래 묶음을 따로 쓴다.
  - 지금 상태: 작성법 항목(PSST 작성법 + 섹션 설계도 블록)의 있음(✓)·없음(✗) 자동 판정,
    주장형 헤드라인·시각자료 수, 그 절의 빈칸·가설 표기, 점수 영향
  - 고려해야 할 점: 심사 관점(judge-insights·case-insights) + 모델이 이 초안을 읽고 더한다
  - 꼭 적어야 할 것: 없는 작성법 항목·빈칸 표기를 "~해야 한다" 체크리스트로
  - 이렇게 써 보세요 · 발표에서는 · 근거 확보: 모델이 채운다(✍)
  - 있으면 넣어 주세요: 그 절을 강하게 만들 사용자 자산
맨 앞에 '한눈에'(점수·행동 3개·모아 주실 자료), 맨 끝에 '제출 전 체크리스트'.
자동 판정은 단어로 짐작한 것이라 본문을 읽고 고친다. 기준 문서: bizplan/references/coaching.md
(항목을 바꾸면 아래 CHECKS도 같이 바꾼다).
"""
import argparse
import re

FILL = "✍ (이 초안을 읽고 채운다)"
SKIP = ("보강 제안", "있으면 좋을", "요청 자료", "참고 자료", "조사용 프롬프트", "자체 일관성", "심화 안내", "작성 기준")
MARK = re.compile(r"\[(작성 필요|산정 예정|공고 확인 필요|미확보)[^\]]*\]|\((?:팀 )?가설[^)]*\)|\(계획안[^)]*\)|\(가정[^)]*\)|팀 판단")

# (이름, 소제목 신호, [(작성법 항목, 있음 판정 정규식)], 심사 관점, 부탁할 자산, 검토 하위 항목 신호)
CHECKS = [
    ("개요", r"개요|요약", [
        ("한 줄 소개(타깃·측정 가능한 문제·해결 방식·결과물)", r"줄이는|을 위한|에게"),
        ("아이템명 공식(기술이 적용된, 혜택을 제공하는, 제품/서비스)", r"적용된|혜택"),
        ("사업 범주", r"범주"),
        ("PSST 요약(문제·실현·성장·팀)", r"문제.{0,40}\|[\s\S]*솔루션|솔루션[\s\S]*차별|실현 가능성[\s\S]*성장 전략|문제[\s\S]*성장[\s\S]*팀")],
     "10초 안에 무엇을 하는 팀인지, 문제 실재성·해결 대응·실행 증거가 보이는가(B2, C 가장 먼저 보는 것 1·2·3·9)",
     "대표 이미지(앱 화면·시제품 사진 1장), 서비스 로고·이름", r"$^"),
    ("배경", r"시장 배경|배경 및 필요성|창업 배경|배경", [
        ("대표·팀의 직접 경험(내부 배경)", r"내부 배경|대표.{0,30}(겪|경험|직접)|직접 겪"),
        ("공적 통계 수치(외부 배경)", r"\d[\d,.]*\s*(%|억|만|조|개|명|원|달러)"),
        ("출처 표기", r"출처|\((?:[^)]*?)(19|20)\d\d[.)]"),
        ("왜 지금(제도·수요·기술 가격 중 하나)", r"왜 지금|제도|규제|정책|가격 하락|수요 변화|최근")],
     "장면 → 확인 행동 → 확산 확인 → 왜 지금. 문제는 크게, 해법은 좁게(B3)",
     "현장 사진(촬영일·장소·대상 수 캡션), 관련 기사·통계 원문 캡처", r"근거 수치|시급성"),
    ("문제", r"Pain|문제 인식|고객 문제|필요성 \d|문제와 필요성|문제$", [
        ("문제 2~3개(우선순위)", r"P2|②|2\.|필요성 2"),
        ("발생 빈도·심각도", r"빈도|심각|하루|매일|매주|매월|주 ?\d+회|월 ?\d+회|\d+\s*(초|분|시간|건)"),
        ("손실 환산(시간·금액)", r"손실|기회비용|낭비|피해|비용이 들|만 원|시간을"),
        ("현재 대처행동과 한계", r"대처|대신|지금은|현재 방식|임시|다시"),
        ("직접 근거(인터뷰·관찰·인용)", r"인터뷰|관찰|설문|응답|“|”|\"[^\"]+\"|\d+\s*명")],
     "직접 근거(인터뷰·관찰·민원)가 통계 인용보다 강하다, 자체 설문만이면 약하다(B4, C 1)",
     "고객 인터뷰 메모·녹취 요약(표), 설문 결과(응답 수·기간), 불편 장면 사진·리뷰 캡처", r"문제 정의|근거 수치"),
    ("경쟁", r"한계|경쟁|차별", [
        ("실명 비교 3곳 이상", r"\|.*\|.*\|.*\|"),
        ("대체재(고객의 현재 대처행동)", r"대체"),
        ("자사가 불리한 축", r"불리|열세|약점|못한다|부족"),
        ("확인 경로(URL·확인 시점)", r"확인 경로|https?://|확인 시점|기준[)]?"),
        ("우위 유지 근거(관계·계약·축적 데이터)", r"우위 유지|관계|계약|축적|데이터")],
     "경쟁사 한계를 우리가 어떻게 해소하는지 + '경쟁사가 같은 기능을 붙이면 무엇이 남나'에 답하는가(B8)",
     "경쟁 서비스 화면·가격표 캡처(확인 날짜), 직접 써 본 비교 메모, 사용 후기", r"$^"),
    ("필요성", r"필요성|왜 지금", [
        ("필요성 2개", r"필요"),
        ("해결 시 이점(Need-payoff)", r"이점|효과|해결되면|줄인|높인"),
        ("니즈 증거(성장률·성공 사례·인터뷰)", r"성장|사례|인터뷰|설문"),
        ("지원사업비로 해결할 핵심 기능", r"지원|사업비|협약")],
     "규제·정책·시장 변화와 연결한 타이밍(C 문제인식)",
     "정책·규제 변화 문서, 시장 성장 통계 원문", r"시급성"),
    ("타겟", r"^(?!.*진입).*(타겟|고객 현황|페르소나|목표 ?시장|목표 고객|시장 현황|1차 고객|고객 특성)", [
        ("1차 고객 수(모집단 × 발생률 × 의향)", r"1차 고객|모집단|×"),
        ("결제자 기준", r"결제|돈을 내|과금|유료"),
        ("페르소나 카드(인용·검증 n/N)", r"페르소나|“|\d+\s*/\s*\d+|\d+명 중"),
        ("세분화 근거", r"세분|세그먼트|1차|2차")],
     "'모든 사람'은 고객이 아니다 — 측정·접근·구매력·니즈 동질성으로 좁혔는가(B5)",
     "고객 설문 응답 분포, 모집단 통계 원문(출처·시점), 페르소나 근거 인터뷰", r"문제 정의"),
    ("실행 증거", r"실행 증거|준비 정도|준비정도|증빙 자산|한 일|^[\d\-. ]*현황$|보유역량|진행역량", [
        ("보유역량(경험 횟수·기간·자산)", r"\d+\s*(회|년|개월|명|건)|보유"),
        ("진행역량(완료·진행·예정 상태)", r"완료|진행 중|예정"),
        ("미확보 공개(되는 것·안 되는 것)", r"미확보|확보하지 못|안 되는|없다"),
        ("실물 증빙(사진·화면·링크·별첨)", r"!\[|\[이미지|https?://|별첨|MVP|시제품|데모")],
     "만들어 실행한 것은 실물로(사진·링크), 없으면 확인 계획(언제·누구·무엇)으로(B6, C 3·9)",
     "서비스·시제품 화면 캡처와 링크, 운영 지표 캡처(기간 명시), LOI·PoC 메일, 수상·출품 확인서", r"증빙"),
    ("기능", r"핵심 기능|기술|구현|솔루션|구체화|개발 계획", [
        ("솔루션 n ↔ 문제 n 번호", r"솔루션 \d|①|P\d|문제 \d|필요성 \d"),
        ("고객 편익 수치(시간·비율·조건)", r"\d+\s*(초|분|%|배|km)"),
        ("기술 리스크와 대응", r"리스크|위험"),
        ("기술 보호·지재권 상태", r"특허|출원|지재권|보호|보안")],
     "기능 나열이 아니라 '문제 n을 이렇게 푼다'는 편익 중심, 동작 안 하는 기능은 계획으로(B7)",
     "프로토타입·MVP 화면/영상(1분), 기술 구조도, 성능 테스트 결과, 특허 출원서(번호·상태)",
     r"기능·구현|대응 구조|증빙"),
    ("일정", r"일정|로드맵|마일스톤", [
        ("월차·분기별 활동·산출물", r"산출물"),
        ("마일스톤", r"마일스톤|M\d|★"),
        ("인과(과업 → KPI → 매출)", r"KPI|→.*→"),
        ("예산 연결", r"예산|금액|비용")],
     "로드맵은 일정표가 아니라 '이 과업을 이 시점에 하기 때문에 이 매출'이 되는 인과 사슬(B13)",
     "이미 한 일의 기록(개발 일지·커밋 로그·회의록)", r"일정"),
    ("사업비", r"사업비|예산|자금", [
        ("비목 표(세부 내용·금액)", r"비목|\|.*금액"),
        ("비율", r"비율|%"),
        ("항목별 산출 근거(단가 × 수량)", r"산출 근거|×"),
        ("검산(합계 = 상한)", r"합계|검산")],
     "산출 근거·합계 검산(check_tables)·공고 비목 기준(B9)",
     "장비·외주 견적서, 단가 근거(가격표 캡처)", r"예산"),
    ("BM", r"비즈니스 모델|수익|BM", [
        ("한 문장 공식(누구에게 무엇을 얼마에)", r"에게.{0,60}(원|달러)|에게.{0,60}○○"),
        ("매출 산식(대상 수 × 전환율 × 단가)", r"×"),
        ("단가 근거(지불 의향·경쟁가·절감분)", r"지불 의향|경쟁가|절감|기준가"),
        ("결제자와 과금 방식", r"결제|과금|구독|이용료|무료")],
     "누가 무엇에 왜 지불하는가가 한눈에 — '사용자 먼저, 수익화는 나중'은 공백으로 읽힌다(B10)",
     "가격 테스트·지불 의향 설문 결과, 사전 예약·대기 명단, 구매의향서(LOI)", r"BM"),
    ("시장 규모", r"시장 규모|TAM|SAM|SOM", [
        ("TAM·SAM·SOM 층위", r"TAM[\s\S]*SAM[\s\S]*SOM"),
        ("층위별 산식(상향식)", r"×|산식"),
        ("1차 고객 수", r"1차 고객|모집단|곳|명"),
        ("출처", r"출처|\((?:[^)]*?)(19|20)\d\d|QY|리포트|Research")],
     "거대한 TAM보다 도달 가능한 1차 고객 수와 산출 근거가 먼저(B5). SOM 200억 권장선은 예창패 노하우(공식 기준 아님)(J §4)",
     "통계·리포트 원문(표 캡처), 상향식 산정 근거(고객 수 출처)", r"시장 규모"),
    ("진입", r"진입|마케팅|퍼널", [
        ("퍼널(단계 인원·구간 전환율)", r"퍼널|전환율|→"),
        ("접촉 완료 수", r"접촉"),
        ("채널별 방식·비용", r"채널|방식|비용|견적")],
     "채널명 나열이 아니라 접촉 대상·방식·완료 수 — 범용 홍보는 접촉·예산이 있을 때만(B11, J §4)",
     "고객사·파트너 접촉 기록(메일·회의록), PoC 일정 확약 메일, 랜딩 페이지·SNS 링크와 반응 지표",
     r"마케팅"),
    ("목표", r"목표|매출·투자|3지표|협약 기간|생존율", [
        ("매출(금액 + 산식)", r"매출"),
        ("투자(LOI·조건 또는 미팅 진행)", r"투자|LOI"),
        ("고용(포지션 × 시기)", r"고용|채용|명"),
        ("이후 3년·흑자 전환 조건", r"흑자|영업이익|3년")],
     "협약 기간 매출·투자·고용을 숫자로 — 수치는 사실·근거로만, 비전은 그 뒤에(B12, J §4)",
     "이미 측정한 지표(가입·사용·만족도), 투자 미팅·LOI 기록, 채용 계획(포지션·시기)", r"목표"),
    ("SWOT", r"SWOT", [
        ("강점·약점·기회·위협", r"강점[\s\S]*약점[\s\S]*기회[\s\S]*위협"),
        ("교차 전략(SO·WO·ST·WT)", r"SO|WO|ST|WT")],
     "약점을 숨기지 않고 WO·WT로 보완 경로를 보인다",
     "(SWOT 근거가 된 조사·인터뷰 자료)", r"$^"),
    ("대표자", r"대표자", [
        ("당사자성(직접 겪거나 처리한 경험)", r"직접|겪|당사자|처리"),
        ("관련 경력·전공", r"경력|경험|전공|\d+\s*년"),
        ("준비 행동(날짜순)", r"(19|20)\d\d|준비|\d+월"),
        ("적임자 한 문장", r"적임|해낼|이유")],
     "스펙 나열이 아니라 문제 ⇄ 역량 ⇄ 역할의 연결(B14, J §4, C 팀 구성)",
     "이력 요약(블라인드: 학교·직장명 ○○), 포트폴리오·결과물 링크, 수상·자격·공모전 기록", r"대표자"),
    ("팀", r"팀 현황|팀원|팀 구성|R&R|보완", [
        ("R&R(책임 범위)", r"책임|R&R|담당"),
        ("상태(확보·예정·협의 중)", r"확보|예정|협의"),
        ("보완 계획(시점·예산·검증)", r"보완|채용|자문|외주"),
        ("협업 구조", r"협업|주간|도구|의사결정")],
     "빈 분야를 먼저 본다 — 비어 있는데 계획이 없는 것만 감점(B14)",
     "팀원 이력 요약·합류 확약, 채용 공고·후보", r"구성·보완"),
    ("협력", r"협력|파트너", [
        ("기관·보유 역량·협력 내용", r"기관|협력|역량"),
        ("협력 시기(조건부 가능)", r"(19|20)\d\d|M\d|시기|후"),
        ("단계(접촉 < 협의 < LOI < MOU < 실적)", r"MOU|LOI|협의|접촉|실적")],
     "협력 단계를 증빙 범위 안에서 최상위 격식 표현으로(J §4 사다리)",
     "MOU·협약서·자문 확약 메일·공문(단계 그대로)", r"협력"),
]

CLAIM = re.compile(r"^\s*(?:[-*]\s*)?(○|◆)\s+\S")
VISUAL = re.compile(r"!\[|\[이미지|\[그림|\[시각자료")


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


def josa(word, pair=("을", "를")):
    """받침에 맞춰 을/를(또는 이/가)을 붙인다."""
    w = re.sub(r"\(.*?\)|\*", "", word).strip()
    ch = w[-1:] if w else ""
    if "가" <= ch <= "힣":
        return word + (pair[0] if (ord(ch) - 0xAC00) % 28 else pair[1])
    return word + f"{pair[0]}({pair[1]})"


def todo(mark):
    """빈칸 표기 하나를 '~해야 한다' 할 일로."""
    m = re.match(r"\[(작성 필요|산정 예정|공고 확인 필요|미확보)[:：]?\s*([^\]]*)\]", mark)
    if m:
        kind, what = m.group(1), m.group(2).strip() or "이 칸"
        verb = {"작성 필요": "채워야 한다", "산정 예정": "산정해 넣어야 한다", "공고 확인 필요": "공고로 확인해야 한다",
                "미확보": "확보해야 한다"}[kind]
        return f"{josa(what)} {verb}"
    if "가설" in mark:
        return "'팀 가설'을 인터뷰·관찰 같은 직접 근거로 바꿔야 한다"
    if "계획안" in mark or "가정" in mark:
        return f"{mark.strip('()')} — 팀이 확정해야 한다"
    return "'팀 판단'의 근거(공개 자료·인터뷰)를 밝혀야 한다"


def section_block(title, body, check, items):
    text = "\n".join(body)
    marks = sorted(set(m.group(0) for m in MARK.finditer(text)))
    plain = MARK.sub(" ", re.sub(r"\*\*\[[^\]]*\]\*\*", " ", text))   # 빈칸 표기 속 낱말('[작성 필요: 경력]')은 있음으로 세지 않는다
    got = [(bool(re.search(rx, plain)), label) for label, rx in check[2]] if check else []
    gains = []
    if check and items:
        for sec, name, mark, g, mx in items:
            if mark != "O" and re.search(check[5], name):
                gains.append(f"{sec} '{name}' {mark}→O +{mx - g:g}점")
    state = " · ".join(f"{'✓' if ok else '✗'} {label}" for ok, label in got) or "(해당 체크리스트 없음 — coaching.md 3절에서 고른다)"
    claims = [l for l in [title] + body if CLAIM.match(l) or (l is title and re.match(r"^\S*\s*\[[^\]]{1,15}\]", l))]
    numbered = sum(1 for l in claims if re.search(r"\d", l))
    visuals = sum(1 for l in body if VISUAL.search(l))
    out = [f"### {title}", "",
           f"**지금 상태** *(자동 판정 — 확인 필요)*: 작성법 {state} / 헤드라인 {len(claims)}개(숫자 {numbered}) · 시각자료 {visuals}개"
           + (f" / 빈칸 {len(marks)}곳" if marks else "")
           + (f" / 점수 영향 {' · '.join(gains)}" if gains else (" / 점수 영향 검토 후 계산" if not items else "")), "",
           "**고려해야 할 점**", ""]
    if check:
        out.append(f"- {check[3]}")
    out += [f"- {FILL}", "", "**꼭 적어야 할 것**", ""]
    for ok, label in got:
        if not ok:
            short = label.split("(")[0].strip()
            out.append(f"- [ ] {josa(short)} 적어야 한다" + (f" (작성법: {label})" if short != label else " (작성법)"))
    if not claims:
        out.append("- [ ] 소제목을 주장 문장(`○ [태그] 결론 문장`)으로 바꿔야 한다 (섹션 설계도 1-1)")
    if not visuals:
        out.append("- [ ] 이 부분을 증명할 시각자료를 하나 이상 두어야 한다 (섹션 설계도 3절)")
    for t in dict.fromkeys(todo(m) for m in marks):      # 같은 할 일은 한 번만
        out.append(f"- [ ] {t}")
    out += [f"- [ ] {FILL}", "", "**이렇게 써 보세요** *(사실을 확인한 뒤 ○○를 채운다)*", "", f"> {FILL}", "",
            "**발표에서는**", "", f"- {FILL}", "", "**근거 확보** *(무엇을 · 어떻게 · 언제)*", "", f"- {FILL}", ""]
    if check:
        out += ["**있으면 넣어 주세요**", ""] + [f"- {a_.strip()}" for a_ in re.split(r",\s*(?![^()]*\))", check[4])] + [""]
    return out, marks, gains, len(claims), visuals


def registry(path):
    """브리프의 '숫자 등록부' 절에서 값이 채워진 행 수."""
    text = open(path, encoding="utf-8").read()
    m = re.search(r"^##[^\n]*숫자 등록부[^\n]*\n([\s\S]*?)(?=^## |\Z)", text, re.M)
    if not m:
        return None
    rows = [r for r in m.group(1).splitlines() if r.startswith("|") and not re.match(r"^\|\s*(값|-)", r)]
    return sum(1 for r in rows if r.strip("| ").replace("|", "").strip())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("doc")
    ap.add_argument("--out", required=True)
    ap.add_argument("--review")
    ap.add_argument("--brief", help="브리프.md — 숫자 등록부 행 수를 '한눈에'에 적는다")
    a = ap.parse_args()
    lines = open(a.doc, encoding="utf-8").read().splitlines()
    doc_title = next((l[2:].strip() for l in lines if l.startswith("# ")), "사업계획서")
    items, score = review_items(a.review) if a.review else ([], None)
    secs = sections(lines)
    body_out, all_marks, all_gains, assets, last_parent, n_blocks = [], [], [], [], None, 0
    n_claims = n_visuals = 0
    for k, (i, lvl, title) in enumerate(secs):
        nxt = secs[k + 1][0] if k + 1 < len(secs) else len(lines)
        has_child = k + 1 < len(secs) and secs[k + 1][1] > lvl
        parent = next((t for _, l2, t in reversed(secs[:k]) if l2 < lvl), "")
        if any(s_ in title or s_ in parent for s_ in SKIP):
            continue
        body = lines[i + 1:nxt]
        if has_child and not any(l.strip() for l in body):
            continue
        if parent and parent != last_parent:
            body_out += [f"## {parent}", ""]
            last_parent = parent
        elif not parent:
            last_parent = None
        check = pick(title) or pick(parent)
        blk, marks, gains, nc, nv = section_block(title, body, check, items)
        n_claims += nc
        n_visuals += nv
        body_out += blk
        n_blocks += 1
        all_marks += marks
        all_gains += [(float(g.rsplit("+", 1)[1].rstrip("점")), g, title) for g in gains]
        if check:
            assets.append((title, check[4]))
    reg = registry(a.brief) if a.brief else None
    seen, top = set(), []
    for pts, g, t in sorted(all_gains, reverse=True):
        key = g.split("'")[1] if "'" in g else g
        if key not in seen:
            seen.add(key)
            top.append(f"{len(top) + 1}. ✍ (행동) — (기한) — {g} — {t}")
        if len(top) == 3:
            break
    head = [f"# 작성 가이드 — {doc_title}", "",
            "> 사업계획서와 **따로 보는** 가이드다. 사업계획서 목차 순서대로 그 부분에서 고려해야 할 점과 적어야 할 것을 정리했다. "
            "기준: PSST 작성법 · 심사 성향 · 사례 체크포인트(bizplan/references/coaching.md).", "",
            "## 한눈에", "",
            "| 지금 | 목표 | 가장 큰 공백 |", "|------|------|--------------|",
            f"| {f'{score}점(검토 리포트) · ' if score is not None else ''}빈칸 {len(all_marks)}곳 | ✍ (과락선·목표 점수) | ✍ |", "",
            f"**구조**: 주장형 헤드라인 {n_claims}개 · 시각자료 {n_visuals}개(문서형 10쪽 기준 12~16개 권장) · "
            + (f"숫자 등록부 {reg}개" if reg is not None else
               "숫자 등록부 없음(브리프에 '숫자 등록부' 절을 만든다)" if a.brief else "숫자 등록부 — 브리프 확인(--brief)"), "",
            "**점수가 가장 많이 오르는 행동 3개**", ""] + (top or ["1. ✍ (검토 리포트를 주면 점수 영향순으로 뽑는다)"]) + [
            "", "**모아 주실 자료** *(있는 것만 — 받으면 반영할 목차)*", ""] + \
           [f"- [ ] {asset} → {t}" for t, asset in assets] + ["", "## 목차별 가이드", ""]
    tail = ["## 제출 전 체크리스트", "",
            f"- [ ] 사업계획서의 [작성 필요]·[산정 예정]·[공고 확인 필요] 표기가 0개인가(지금 {len(all_marks)}곳)",
            "- [ ] 출처를 원문과 대조했는가(검색 색인·기사 요약만으로 쓴 수치가 남아 있지 않은가)",
            "- [ ] 표 합계·비율·곱셈식을 검산했는가(`check_tables.py`)",
            "- [ ] 본문·개요·그림·발표의 숫자가 숫자 등록부와 같은가",
            "- [ ] 헤드라인만 이어 읽어도 문제 → 해결 → 성장 → 팀이 이해되는가",
            "- [ ] 협약 기간 매출·투자·고용이 근거와 함께 숫자로 있는가",
            "- [ ] 공고 양식의 목차·항목 번호·분량을 지켰고 양식 안내 문구를 지웠는가",
            "- [ ] 블라인드 — 성명·학교·직장명·소재지 등 유추 가능한 정보를 가렸는가",
            "- [ ] 협력·실적 표현이 증빙 단계(접촉 < 협의 < LOI < MOU < 실적) 안에 있는가",
            "- [ ] 문제-솔루션 대응표의 '미해결·추가 검증 필요' 표기가 본문과 일치하는가", ""]
    open(a.out, "w", encoding="utf-8").write("\n".join(head + body_out + tail) + "\n")
    print(f"작성 가이드 골격: {a.out} — 목차 {n_blocks}개, 빈칸 {len(all_marks)}곳, "
          f"점수 영향 {len(all_gains)}건{'' if a.review else '(검토 리포트 없음)'}")
    print(f"남은 빈칸(✍): {sum(1 for l in head + body_out if '✍' in l)}줄 — 이 초안을 읽고 채운다")


if __name__ == "__main__":
    main()
