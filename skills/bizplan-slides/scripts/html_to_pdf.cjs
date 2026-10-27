// HTML 슬라이드를 장 단위 PDF로 내보낸다: node html_to_pdf.cjs 입력.html 출력.pdf [너비px] [높이px]
// 각 슬라이드 섹션은 CSS에서 width×height 고정 + page-break-after: always 여야 한 장씩 끊긴다.
const { chromium } = require('playwright');

(async () => {
  const [src, out, w = '1280', h = '720'] = process.argv.slice(2);
  if (!src || !out) {
    console.error('사용법: node html_to_pdf.cjs 입력.html 출력.pdf [너비px] [높이px]');
    process.exit(2);
  }
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: Number(w), height: Number(h) } });
  await page.goto('file://' + src, { waitUntil: 'networkidle' });
  await page.emulateMedia({ media: 'print' });
  await page.pdf({ path: out, width: `${w}px`, height: `${h}px`, printBackground: true,
                   margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  await browser.close();
})().catch((e) => { console.error(e.message); process.exit(1); });
