// 시각자료 HTML의 각 <section class="viz" id="…">를 PNG로 찍는다: node html_shot.cjs 입력.html 출력폴더 [배율]
// html_visuals.py가 부른다. 글꼴이 다 실린 뒤(document.fonts.ready) 요소 단위로 캡처한다.
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const [src, outDir, scale = '2'] = process.argv.slice(2);
  if (!src || !outDir) {
    console.error('사용법: node html_shot.cjs 입력.html 출력폴더 [배율]');
    process.exit(2);
  }
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1800, height: 1200 }, deviceScaleFactor: Number(scale) });
  await page.goto('file://' + path.resolve(src), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => window.__fit && window.__fit());   // 발표 장 맞춤(있을 때)
  const ids = await page.$$eval('section.viz[id]', (els) => els.map((e) => e.id));
  for (const id of ids) {
    const el = await page.$(`section.viz[id="${id}"]`);
    const file = path.join(outDir, `${id}.png`);
    await el.screenshot({ path: file });
    console.log(file);
  }
  await browser.close();
})().catch((e) => { console.error(e.message); process.exit(1); });
