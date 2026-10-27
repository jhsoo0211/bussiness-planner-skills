# bizplan 소개 릴 (50초 · 사운드 포함 · 반복 재생)

`bizplan-reel.mp4`(한국어) · `bizplan-reel-en.mp4`(영어) — 1920×1080, 30fps, 50초, AAC 스테레오. 마지막 프레임이 첫 프레임으로 이어지는 루프.

저장소 README 상단에는 소리 없는 미리보기(`bizplan-reel-preview.webp`, `bizplan-reel-en-preview.webp`, 960px · 12fps 애니메이션 WebP)를 두고, 누르면 원본 mp4로 이동한다.

## 연출 원칙

- **120 BPM, 100비트.** 모든 비트에 무언가 일어나고, 움직임은 비트 0.05초 전에 시작해 비트에 착지한다. 각 기능은 3~5초씩 머물러 읽을 시간을 준다.
- **컷·페이드 없음.** 모든 장면은 앞 장면의 선과 도형이 변형되어 만들어진다.
- **세 가지 잉크**: 모눈 종이(연필) → 청사진(흰 선) → 줄 노트(연필). 모눈→청사진은 `1:1` 도장이 화면을 덮는 경계로, 청사진→노트·노트→모눈은 가로 스캔 선 하나로 바뀐다.
- 서체: Geist(라틴·숫자), Geist Mono(명령어·링크), Pretendard(한글). 색: 종이 `#EDE6D5`, 노트 `#F6F1E6`, 청사진 `#1B3ED2`, 시안 `#45F0DD`, 흑연 `#16161A`, 노트 여백선 `#D2553F`.
- 왼쪽 위 `FIG. 06 — MARKET`(장면 번호·이름), 오른쪽 아래 `BEAT 38 / 100`이 계속 표시된다.

## 구성

| # | 시간 | 잉크 | 내용 |
|---|------|------|------|
| 01 DRAFT | 0–2초 | 모눈 | `bizplan` 타이틀, 가이드 캐릭터가 달려 나가고 레일이 글자를 눌러 한 줄로 |
| 02 PROBLEM | 2–5초 | 모눈 | "사업계획서, 막막하다면?" → 레일이 닫혔다 열리며 파란 `bizplan` |
| 03 OUTLINE (NEW) | 5–10초 | 모눈 | 제목 → 중제목 → 소제목 → 한두 줄 요약 큰틀 |
| 04 PSST | 10–13초 | 모눈 | P · S · S · T 블록 |
| 05 MATCH | 13–16.5초 | 모눈 → 청사진 | 문제 3 ↔ 해결 3 연결, `1:1` 도장이 화면을 덮음 |
| 06 MARKET | 16.5–19.5초 | 청사진 | TAM · SAM · SOM 도식, 산출식 |
| 07 REVIEW | 19.5–23초 | 청사진 | 84/100 점수 링, 항목별 O · △, 필수 수정 · 예상 질문 |
| 08 PITCH | 23–26초 | 청사진 | 슬라이드 6장 구성 |
| 09 EXPORT (NEW) | 26–29.5초 | 청사진 → 노트 | `.hwpx` · `.docx` · `.md` · 16:9 |
| 10 CHAT | 29.5–36초 | 노트 | **설치 1순위**: 채팅창에 깃허브 링크 + "이 스킬 설치해줘" → 설치 완료 → `/bizplan` 시작 |
| 11 TERM | 36–41초 | 노트 | 대안: 터미널 설치(Claude Code 명령 2줄 · Codex 3줄) |
| 12 SKILLS | 41–43.5초 | 노트 | 스킬 15종 + outline(NEW) |
| 13 LINK | 43.5–48초 | 노트 → 모눈 | 저장소 주소, Claude Code · Codex |
| 14 END | 48–50초 | 모눈 | 첫 프레임으로 복귀 |

## 파일

| 파일 | 용도 |
|------|------|
| `bizplan-reel.src.html` | 편집용 원본(캔버스 렌더러, 장면 시작 시각 `SEC`, 한·영 문구 표 `I18N`, 효과음 이벤트, 음악 스타일) |
| `bizplan-reel.html` | 글꼴을 넣은 단일 파일. 브라우저로 열면 반복 재생(`?lang=en`이면 영어), 스페이스바로 일시정지 |
| `build.py` | Geist · Geist Mono · Pretendard 서브셋을 넣어 `bizplan-reel.html` 생성 |
| `render.cjs` | Playwright로 프레임 PNG와 효과음·음악 정보(`events.json`) 추출. `--lang en`으로 영어판, `--range a,b`로 나눠 병렬 렌더 |
| `sound.py` | numpy로 120 BPM 음악 + 화면 동기 효과음 합성, 루프 이음새 처리, 약 -14 LUFS |

## 다시 만들기

```bash
pip install fonttools brotli numpy
npm pack geist pretendard   # 글꼴 패키지 내려받아 압축 해제
python build.py --geist <geist>/dist/fonts --pretendard <pretendard>/dist/web/static/woff2
node render.cjs 30 /tmp/frames                       # playwright 필요, 프레임 + events.json (영어판: --lang en)
python sound.py /tmp/frames/events.json /tmp/reel.wav
ffmpeg -y -framerate 30 -i /tmp/frames/f%04d.png -i /tmp/reel.wav \
  -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -c:a aac -b:a 160k -shortest -movflags +faststart bizplan-reel.mp4
# README 미리보기
ffmpeg -y -i bizplan-reel.mp4 -vf "fps=12,scale=960:-2:flags=lanczos" -an -c:v libwebp_anim -q:v 60 -compression_level 6 -loop 0 bizplan-reel-preview.webp
```

문구는 `I18N.ko` / `I18N.en`에서 고친다. 장면 길이는 원본의 `SEC`(장면 시작 시각)만 바꾸면 그 안의 타이밍·자막·효과음이 함께 따라간다(자막 표시 구간은 `CAPTIONS`에서 조정). 문구를 바꾸면 `build.py`를 다시 실행해야 새 글자가 글꼴에 들어간다. 명령어 철자 주의: 저장소 `bussiness-planner-skills`, 마켓플레이스 `business-planner-skills`.
