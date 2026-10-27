// bizplan-reel.html -> PNG 프레임 + 사운드 이벤트(events.json)
// 사용: node render.cjs [fps=30] [outDir=frames] [--stills 1.2,4.5,...]
const { chromium } = require('playwright');
const { mkdirSync, writeFileSync } = require('node:fs');
const { pathToFileURL } = require('node:url');
const path = require('node:path');

(async () => {
  const args = process.argv.slice(2);
  const stillsArg = args.indexOf('--stills');
  const stills = stillsArg >= 0 ? args.splice(stillsArg, 2)[1].split(',').map(Number) : null;
  const ra = args.indexOf('--range'); if (ra >= 0) args.splice(ra, 2);
  const fps = Number(args[0] || 30);
  const outDir = path.resolve(args[1] || path.join(__dirname, 'frames'));
  mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errors.push(m.text()); });
  await page.goto(pathToFileURL(path.join(__dirname, 'bizplan-reel.html')).href + '?render=1');
  await page.evaluate(() => window.__ready);

  const duration = await page.evaluate(() => window.__duration);
  writeFileSync(path.join(outDir, 'events.json'), JSON.stringify({ duration, events: await page.evaluate(() => window.__events), music: await page.evaluate(() => window.__music) }));
  const canvas = await page.$('canvas');
  const times = stills || Array.from({ length: Math.round(duration * fps) }, (_, i) => i / fps);
  // optional --range a,b renders frames a..b-1 (to split work across processes)
  const rangeArg = process.argv.indexOf('--range');
  const [from, to] = rangeArg >= 0 ? process.argv[rangeArg + 1].split(',').map(Number) : [0, times.length];
  for (let i = from; i < Math.min(to, times.length); i++) {
    await page.evaluate(t => window.__seek(t), times[i]);
    const name = stills ? `s_${times[i]}.png` : `f${String(i).padStart(4, '0')}.png`;
    await canvas.screenshot({ path: path.join(outDir, name) });
  }
  await browser.close();
  if (errors.length) console.log('page errors:', errors);
  console.log(`frames ${from}..${Math.min(to, times.length) - 1} -> ${outDir}`);
})();
