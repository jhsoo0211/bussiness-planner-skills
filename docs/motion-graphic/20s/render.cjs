// bizplan-20s.html -> PNG 프레임 -> MP4
// 사용: node render.cjs [fps=30] [outDir=frames]
//       ffmpeg -y -framerate 30 -i frames/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart bizplan-20s.mp4
const { chromium } = require('playwright');
const { mkdirSync } = require('node:fs');
const { pathToFileURL } = require('node:url');
const path = require('node:path');

(async () => {
  const fps = Number(process.argv[2] || 30);
  const outDir = path.resolve(process.argv[3] || path.join(__dirname, 'frames'));
  mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(pathToFileURL(path.join(__dirname, 'bizplan-20s.html')).href + '?render=1');
  await page.evaluate(() => document.fonts.ready);

  const duration = await page.evaluate(() => window.__duration);
  const total = Math.round(duration * fps);
  for (let i = 0; i <= total; i++) {
    await page.evaluate(t => window.__seek(t), i / fps);
    await page.screenshot({ path: path.join(outDir, `f${String(i).padStart(4, '0')}.png`) });
  }
  await browser.close();
  console.log(`${total + 1} frames -> ${outDir}`);
})();
