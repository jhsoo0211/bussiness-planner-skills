# bizplan 소개 릴 (34초 · 사운드 포함 · 반복 재생)

`bizplan-reel.mp4` — 1920×1080, 30fps, 34초, AAC 스테레오. 마지막 프레임이 첫 프레임으로 이어지는 루프.

## 연출 원칙

- **120 BPM, 17마디(마디당 2초), 68비트.** 모든 비트에 무언가 일어나고, 움직임은 비트 0.05초 전에 시작해 비트에 착지한다.
- **컷·페이드 없음.** 모든 장면은 앞 장면의 선과 도형이 변형되어 만들어진다.
- **세 가지 잉크**: 종이(연필) → 청사진(흰 선) → 홀로그램(시안 선 + 흰 심). 종이→청사진은 도장 원이 화면을 덮는 경계로, 청사진→홀로그램·홀로그램→종이는 가로 스캔 선 하나로 바뀐다.
- 서체: Geist(라틴·숫자), Geist Mono(명령어), Pretendard(한글). 색: 종이 `#EDE6D5`, 청사진 `#1B3ED2`, 시안 `#45F0DD`, 검정 `#07080A`, 흑연 `#16161A`, 흰색.
- 왼쪽 위 `FIG. 07 — MARKET`(마디 번호·이름), 오른쪽 아래 `BEAT 27 / 68`이 계속 표시된다.

## 구성

| 마디 | 시간 | 잉크 | 내용 |
|------|------|------|------|
| 01 DRAFT | 0–2초 | 종이 | `bizplan` 타이틀, 가이드 캐릭터가 달려 나가고 레일이 글자를 눌러 한 줄로 |
| 02 PROBLEM | 2–4초 | 종이 | "사업계획서, 막막하다면?" → 레일이 닫혔다 열리며 파란 `bizplan` |
| 03–04 OUTLINE (NEW) | 4–8초 | 종이 | 제목 → 중제목 → 소제목 → 한두 줄 요약 큰틀 |
| 05 PSST | 8–10초 | 종이 | P · S · S · T 블록 |
| 06 MATCH | 10–12초 | 종이 → 청사진 | 문제 3 ↔ 해결 3 연결, `1:1` 도장이 화면을 덮음 |
| 07 MARKET | 12–14초 | 청사진 | TAM · SAM · SOM 도식, 산출식 |
| 08 REVIEW | 14–16초 | 청사진 | 84/100 점수 링, 항목별 O · △, 필수 수정 · 예상 질문 |
| 09 PITCH | 16–18초 | 청사진 | 슬라이드 6장 구성 |
| 10 EXPORT (NEW) | 18–20초 | 청사진 → 홀로그램 | `.hwpx` · `.docx` · `.md` · 16:9 |
| 11 CLAUDE | 20–22초 | 홀로그램 | Claude Code 설치 명령 2줄 |
| 12 CODEX | 22–24초 | 홀로그램 | Codex 내려받기 + 설치 스크립트 |
| 13 RUN | 24–26초 | 홀로그램 | `/bizplan` · `$bizplan` 실행 예 |
| 14 SKILLS | 26–28초 | 홀로그램 | 스킬 15종 + outline(NEW) |
| 15–16 LINK · GET | 28–32초 | 홀로그램 → 종이 | 저장소 주소, Claude Code · Codex |
| 17 END | 32–34초 | 종이 | 첫 프레임으로 복귀 |

## 파일

| 파일 | 용도 |
|------|------|
| `bizplan-reel.src.html` | 편집용 원본(캔버스 렌더러, 타이밍·문구·효과음 이벤트) |
| `bizplan-reel.html` | 글꼴을 넣은 단일 파일. 브라우저로 열면 반복 재생, 스페이스바로 일시정지 |
| `build.py` | Geist · Geist Mono · Pretendard 서브셋을 넣어 `bizplan-reel.html` 생성 |
| `render.cjs` | Playwright로 프레임 PNG와 효과음 이벤트(`events.json`) 추출 |
| `sound.py` | numpy로 120 BPM 음악 + 화면 동기 효과음 합성, 루프 이음새 처리, 약 -14 LUFS |

## 다시 만들기

```bash
pip install fonttools brotli numpy
npm pack geist pretendard   # 글꼴 패키지 내려받아 압축 해제
python build.py --geist <geist>/dist/fonts --pretendard <pretendard>/dist/web/static/woff2
node render.cjs 30 /tmp/frames                       # playwright 필요, 프레임 + events.json
python sound.py /tmp/frames/events.json /tmp/reel.wav
ffmpeg -y -framerate 30 -i /tmp/frames/f%04d.png -i /tmp/reel.wav \
  -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -c:a aac -b:a 160k -shortest -movflags +faststart bizplan-reel.mp4
```

문구를 바꾸면 `build.py`를 다시 실행해야 새 글자가 글꼴에 들어간다. 명령어 철자 주의: 저장소 `bussiness-planner-skills`, 마켓플레이스 `business-planner-skills`.
