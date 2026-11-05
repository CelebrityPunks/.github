// Rasterise the SVG logos to high-res PNGs with headless Chromium.
// Usage: node export_logo.js   (run make_logo_svg.py first)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const dir = path.join(__dirname, 'logo');
const jobs = [
  // [svg, png, size, background, padding fraction]
  ['ouroboros.svg', 'ouroboros_4096.png', 4096, null, 0],
  ['ouroboros_on_dark.svg', 'ouroboros_on_dark_4096.png', 4096, null, 0],
  ['ouroboros_white.svg', 'ouroboros_white_4096.png', 4096, null, 0],
  ['ouroboros_black.svg', 'ouroboros_black_4096.png', 4096, null, 0],
  ['ouroboros.svg', 'youtube_avatar_800.png', 800, '#08080A', 0.06],
  ['ouroboros.svg', 'watermark_150.png', 150, null, 0],
];

(async () => {
  const browser = await chromium.launch();
  for (const [svgName, out, size, bg, pad] of jobs) {
    // render big sizes as a smaller CSS viewport at a higher device scale (crisp vector output)
    const scale = size > 1024 ? size / 1024 : 1;
    const css = size / scale;
    const inner = css * (1 - 2 * pad);
    const svg = fs.readFileSync(path.join(dir, svgName), 'utf8')
      .replace('width="1000" height="1000"', `width="${inner}" height="${inner}"`);
    const page = await browser.newPage({ viewport: { width: css, height: css }, deviceScaleFactor: scale });
    await page.setContent(`<html><body style="margin:0;background:${bg || 'transparent'}">
      <div style="width:${css}px;height:${css}px;display:flex;align-items:center;justify-content:center">${svg}</div>
      </body></html>`);
    await page.screenshot({ path: path.join(dir, out), omitBackground: !bg });
    await page.close();
    console.log('wrote', out);
  }
  await browser.close();
})();
