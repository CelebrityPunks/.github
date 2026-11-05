// Rasterise the AINTIA SVGs to PNG and build a brand-sheet preview.
// Usage: node export_brand.js   (run make_brand.py first)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const dir = __dirname;
const read = (p) => fs.readFileSync(path.join(dir, p), 'utf8');
const size = (svg) => svg.match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/).slice(1).map(Number);

// [svg, png, output width in px, background or null]
const jobs = [
  ['logo/aintia_mark_white.svg', 'png/aintia_mark_white_4096.png', 4096],
  ['logo/aintia_mark_black.svg', 'png/aintia_mark_black_4096.png', 4096],
  ['logo/aintia_mark_sage.svg', 'png/aintia_mark_sage_4096.png', 4096],
  ['logo/aintia_primary_on_dark.svg', 'png/aintia_primary_on_dark_3000.png', 3000],
  ['logo/aintia_primary_white.svg', 'png/aintia_primary_white_3000.png', 3000],
  ['logo/aintia_primary_black.svg', 'png/aintia_primary_black_3000.png', 3000],
  ['logo/aintia_horizontal_white.svg', 'png/aintia_horizontal_white_4000.png', 4000],
  ['logo/aintia_horizontal_black.svg', 'png/aintia_horizontal_black_4000.png', 4000],
  ['logo/aintia_wordmark_white.svg', 'png/aintia_wordmark_white_4000.png', 4000],
  ['logo/aintia_wordmark_black.svg', 'png/aintia_wordmark_black_4000.png', 4000],
  ['icons/aintia_icon_dark.svg', 'png/aintia_icon_dark_1024.png', 1024],
  ['icons/aintia_icon_cream.svg', 'png/aintia_icon_cream_1024.png', 1024],
  ['icons/aintia_icon_sage.svg', 'png/aintia_icon_sage_1024.png', 1024],
  ['logo/aintia_mark_white.svg', 'png/youtube_avatar_800.png', 800, '#0D0D0D'],
  ['logo/aintia_mark_white.svg', 'png/youtube_watermark_150.png', 150],
  ['banner/aintia_youtube_banner.svg', 'png/aintia_youtube_banner_2560x1440.png', 2560],
];

async function shot(browser, html, w, h, out, transparent) {
  // big outputs: small CSS viewport + high device scale (Chromium caps capture size)
  const scale = w <= 2560 && h <= 1440 ? 1 : Math.max(1, Math.ceil(Math.max(w, h) / 1400));
  const page = await browser.newPage({ viewport: { width: Math.round(w / scale), height: Math.round(h / scale) },
                                       deviceScaleFactor: scale });
  await page.setContent(html);
  await page.screenshot({ path: out, omitBackground: transparent });
  await page.close();
}

(async () => {
  fs.mkdirSync(path.join(dir, 'png'), { recursive: true });
  const browser = await chromium.launch();
  for (const [src, out, outW, bg] of jobs) {
    const svg = read(src);
    const [vw, vh] = size(svg);
    const outH = Math.round(outW * vh / vw);
    const scale = outW <= 2560 && outH <= 1440 ? 1 : Math.max(1, Math.ceil(Math.max(outW, outH) / 1400));
    const cw = outW / scale, ch = outH / scale;
    const body = svg.replace(/width="[\d.]+" height="[\d.]+"/, `width="${cw}" height="${ch}"`);
    const html = `<html><body style="margin:0;background:${bg || 'transparent'}">${body}</body></html>`;
    await shot(browser, html, outW, outH, path.join(dir, out), !bg);
    console.log('wrote', out);
  }

  // brand sheet preview
  const inl = (p, w) => read(p).replace(/width="[\d.]+" height="[\d.]+"/, `style="width:${w};height:auto;display:block"`);
  const sw = (hex, name) => `<div class="sw"><div class="dot" style="background:${hex}"></div><b>${hex}</b><span>${name}</span></div>`;
  const font = fs.readFileSync(path.join(dir, 'fonts/Montserrat-500.ttf')).toString('base64');
  const html = `<html><head><style>
    @font-face{font-family:M;src:url(data:font/ttf;base64,${font})}
    body{margin:0;background:#0D0D0D;color:#fff;font-family:M,sans-serif;width:2400px}
    .grid{display:grid;grid-template-columns:1.2fr 1fr 1fr 1.4fr;border-bottom:1px solid #333}
    .cell{padding:36px;border-right:1px solid #333;display:flex;flex-direction:column;gap:24px}
    .cell:last-child{border-right:0}
    h6{margin:0;font-size:15px;letter-spacing:.3em;font-weight:500;color:#ddd}
    .c{flex:1;display:flex;align-items:center;justify-content:center;gap:28px}
    .sw{display:flex;flex-direction:column;align-items:center;gap:8px;font-size:15px}
    .dot{width:110px;height:110px;border-radius:50%;border:1px solid #333}
    .sw span{color:#aaa}
    .row2{display:grid;grid-template-columns:1.6fr 1fr;border-bottom:1px solid #333}
  </style></head><body>
    <div class="grid">
      <div class="cell"><h6>PRIMARY LOCKUP</h6><div class="c">${inl('logo/aintia_primary_white.svg', '420px')}</div></div>
      <div class="cell"><h6>LOGO ONLY</h6><div class="c">${inl('logo/aintia_mark_white.svg', '300px')}</div></div>
      <div class="cell"><h6>WORDMARK</h6><div class="c">${inl('logo/aintia_wordmark_white.svg', '380px')}</div></div>
      <div class="cell"><h6>ICON VARIATIONS</h6><div class="c">
        ${inl('icons/aintia_icon_dark.svg', '170px')}${inl('icons/aintia_icon_cream.svg', '170px')}${inl('icons/aintia_icon_sage.svg', '170px')}</div></div>
    </div>
    <div class="row2">
      <div class="cell"><h6>ALTERNATE LOCKUP</h6><div class="c">${inl('logo/aintia_horizontal_white.svg', '620px')}</div></div>
      <div class="cell"><h6>COLOR PALETTE</h6><div class="c">
        ${sw('#FFFFFF', 'Primary')}${sw('#0D0D0D', 'Background')}${sw('#2F2F2F', 'Surface')}${sw('#747F67', 'Accent')}${sw('#F2EFE8', 'Light')}</div></div>
    </div>
    <div class="cell" style="border:0"><h6>YOUTUBE CHANNEL BANNER</h6>${inl('banner/aintia_youtube_banner.svg', '100%')}</div>
  </body></html>`;
  const page = await browser.newPage({ viewport: { width: 2400, height: 800 } });
  await page.setContent(html);
  await page.screenshot({ path: path.join(dir, 'png/aintia_brand_sheet.png'), fullPage: true });
  console.log('wrote png/aintia_brand_sheet.png');
  await browser.close();
})();
