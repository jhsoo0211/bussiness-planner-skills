# 테마 (경로 R — `scripts/theme_deck.py`)

테마는 색·글꼴·머리 형식·카드 형식만 정한다. 어떤 정보를 어떤 구조로 보여줄지(패턴 23종)는 테마와 상관없이 같다. 기준은 `bizplan-visual/references/info-patterns.md`다. 같은 `deck.json`을 `--theme`만 바꿔 다시 그릴 수 있다.

| 테마 | 성격 | 원형 | 미리보기 |
|------|------|------|----------|
| `report-blue` | 밝은 회색 바탕 + 선명한 파랑 1색. 작은 영문 머리말·굵은 제목·오른쪽 한 줄 설명, 흰 카드 + 파란 알약 라벨, 점 격자 모티프 | 사용자 제공 PDF 「Annual Business Plan」의 색·여백·머리 문법을 다시 그림 | [previews/report-blue.jpg](previews/report-blue.jpg) |
| `mono-line` | 흰 바탕 · 검정 1색 · 회색 단계. 위쪽 옅은 머리띠(브랜드·태그라인), 아래쪽 가는 선 + 검정 탭, 검정 머리띠 카드 | 사용자 제공 PDF 「초보자를 위한 친절한 프레젠테이션」의 문법을 다시 그림 | [previews/mono-line.jpg](previews/mono-line.jpg) |
| `basic-navy` | 흰 바탕 · 남색 + 호박색 보조. 템플릿이 없을 때 기본값 | 이 저장소 자체 디자인(`bizplan-basic.pptx`와 같은 색) | [previews/basic-navy.jpg](previews/basic-navy.jpg) |

- 원본 PDF의 그림·사진·문구·로고는 넣지 않았다. 원본은 `assets/templates/local/`(비공개)에 두고, 구조 분석은 `references/blueprints.md`(청사진 A·B·C)에 있다.
- 「포인트가 잘 보이는 필수 구성 제안서」(30장)는 색보다 **구조**가 쓸모 있어 테마로 만들지 않았다. 대신 장마다 '전달하는 정보 → 형식 → 패턴'을 청사진 A로 정리했다. 그 형식들(카드 → 결론 수렴, 겹친 시장 규모, 포지셔닝 맵, SWOT, 단계 화살 띠, 간트, 요약 → 결론 띠)은 모든 테마에서 쓸 수 있다.
- 미리보기는 `sample-deck.json`(가상 아이템 '복약메이트', 예시 수치)을 그린 것이다: `theme_deck.py --sample --theme <이름> --out 샘플.pptx`.

## 테마 파일 구조

```json
{
  "name": "report-blue", "label": "리포트 블루", "summary": "…", "derived_from": "…",
  "fonts":  {"head": "Pretendard", "body": "Pretendard", "accent": "Pretendard"},
  "colors": {"bg", "surface", "text", "muted", "faint", "line", "soft", "primary", "neutral", "series": [차트·SWOT 색 4~5개]},
  "chrome": {"header": "split | plain", "band": 머리띠 높이(pt, 선택), "footer_rule": 바닥선 y(pt, 선택)},
  "layout": {"x": 좌우 여백, "title_y": 제목 y, "bottom": 본문 아래 끝, "gap": 머리-본문 간격},
  "sizes":  {"title", "lead", "eyebrow", "body", "small"},
  "styles": {"cover": "dots | center", "section": "full | number", "toc": "list | grid", "card": "pill | head",
             "kpi": "bar | box", "process": "pill-line | chevron", "callout": "soft | solid",
             "table": "soft | solid", "closing": "full | center", "bullet": "•", "radius": 모서리(pt)}
}
```

- 좌표는 pt 단위다(16:9 = 960 × 540).
- `primary`는 강조 1색이다. 자사 막대·머리 띠·숫자·`**강조**`에 쓰인다. 모노 테마는 검정을 `primary`로 둔다.
- 글꼴은 발표 PC에 없으면 대체된다. 없을 것 같으면 `--font "맑은 고딕"`으로 만들고, PDF를 함께 낸다. 넘침 추정은 맑은 고딕 폭 기준이라 두 글꼴 모두에서 안전한 쪽이다.

## 새 테마 넣기

1. 그림 템플릿이면 `scripts/theme_from_pdf.py 템플릿.pdf --out 작업폴더/테마분석/`으로 색 후보와 시작용 JSON을 뽑는다. 아니면 기존 테마를 복사한다.
2. 모아보기와 대조해 `colors`를 고친다. `styles`는 위 선택지 중 원본에 가까운 것을 고른다.
3. `theme_deck.py --sample --theme 경로/새테마.json --out 샘플.pptx` → `export_pdf.py` → `preview.py`로 확인한다.
4. 둘 곳을 고른다.
   - 재배포해도 되는 테마: 이 폴더(공개)
   - 유료·기관 템플릿에서 뽑은 테마: `local/`(`.gitignore` 대상)
   - 원본 구조는 `references/blueprints.md` 형식으로 같은 이름 `.md`에 적는다.
