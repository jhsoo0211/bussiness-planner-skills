# bizplan 20초 소개 모션그래픽

`bizplan-20s.mp4` — 1920×1080, 30fps, 20초, 무음.

| 시간 | 장면 | 메시지 |
|------|------|--------|
| 0–2.6초 | 후킹 | 아이디어는 있는데, 사업계획서가 막막할 때 |
| 2.6–4.6초 | 로고 | 아이디어에서 완성 문서까지, 사업계획서 작성 스킬 · Claude Code / Codex |
| 4.6–8.6초 | 01 큰틀 (NEW) | 제목 → 중제목 → 소제목 → 한두 줄 요약 |
| 8.6–12.5초 | 02 작성 | PSST 순서, 문제와 해결 1:1 대응 |
| 12.5–15.6초 | 03 검토 | TAM·SAM·SOM 도식, 100점 채점, 예상 질문 |
| 15.6–18.2초 | 04 문서 (NEW) | 한글(HWPX)·워드·발표 슬라이드 |
| 18.2–20초 | 마무리 | 막막한 사업계획서, 큰틀부터 완성 문서까지 · 저장소 주소 |

## 파일

| 파일 | 용도 |
|------|------|
| `bizplan-20s.src.html` | 편집용 원본(문구·타이밍 수정은 여기서) |
| `bizplan-20s.html` | 글꼴을 넣은 단일 파일. 브라우저로 열면 반복 재생, 스페이스바로 일시정지 |
| `build.py` | 원본에 Pretendard 서브셋 글꼴을 넣어 `bizplan-20s.html` 생성 |
| `render.cjs` | Playwright로 프레임 PNG 추출 |

## 다시 만들기

```bash
pip install fonttools brotli
python build.py --fonts <pretendard>/dist/web/static/woff2   # npm 패키지 pretendard
node render.cjs 30 /tmp/frames                                # playwright 필요
ffmpeg -y -framerate 30 -i /tmp/frames/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart bizplan-20s.mp4
```

문구를 바꾸면 `build.py`를 다시 실행해야 새 글자가 글꼴에 포함된다.
