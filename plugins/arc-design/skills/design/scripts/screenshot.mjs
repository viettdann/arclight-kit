#!/usr/bin/env node
// Screenshot a page in headless Chrome over the DevTools protocol, at any width (the --screenshot flag clamps windows to ~500px).
// Usage: node screenshot.mjs <url|file> <out.png> [--width 1280,390] [--height 900] [--full] [--scheme light,dark] [--media list]
//          [--wait-for css] [--eval "js"] [--focus css] [--hover css] [--selector css] [--wait 500] [--root dir]
//   --width     one or more comma-separated widths; widths under 700 emulate a mobile device.
//   --scheme    prefers-color-scheme per shot, one or both of light,dark (default light, whatever the OS uses). Several widths or schemes name the files out-<width>-<scheme>.png.
//   --media     media features for every shot: reduced-motion, contrast-more, reduced-transparency, forced-colors.
//   --full      capture the whole page instead of one viewport.
//   --wait-for  wait until this element exists and has a size (async chart, fetched data); exit 2 after 10s.
//   --eval      JS run after load, before the shot (reveal a step, set a data-theme class, stub fetch). Awaited if it returns a promise.
//   --focus     focus this element as a keyboard user would, so :focus-visible applies.
//   --hover     move the real pointer over this element (a script can't trigger :hover).
//   --selector  capture only this element's box instead of the viewport.
//   --wait      extra ms after load and fonts (default 500).
//   --root      a local file is served over http from this directory (default: the file's directory), so root-relative assets (href="/style.css") load.
// Prints one line per width: file, page size, and "overflow" when the page is wider than the viewport.
// Exit 0 ok, 1 shots written but some width overflows horizontally, 2 no shot (usage, no Chrome, Node < 22, navigation or HTTP error, eval error, timeout).
import { writeFileSync } from 'node:fs';
import { MEDIA, emulate, fail, launch, load, parseArgs, resolveTarget, sleep, waitFor } from './cdp.mjs';

const USAGE = 'Usage: node screenshot.mjs <url|file> <out.png> [--width 1280,390] [--height 900] [--full] [--scheme light,dark] [--media list]'
  + ' [--wait-for css] [--eval "js"] [--focus css] [--hover css] [--selector css] [--wait 500] [--root dir]';
const opt = { width: '1280', height: '900', wait: '500', eval: '', root: '', full: false,
  scheme: '', media: '', 'wait-for': '', focus: '', hover: '', selector: '' };
const pos = await parseArgs(process.argv.slice(2), opt, ['full'], USAGE);
if (pos.length !== 2) await fail(USAGE);
const widths = [...new Set(opt.width.split(',').map(Number))];
const height = Number(opt.height);
const wait = Number(opt.wait);
if (widths.some((w) => !(w > 0)) || !(height > 0) || !(wait >= 0)) await fail('--width and --height take positive numbers, --wait a number of ms');
const schemes = [...new Set((opt.scheme || 'light').split(','))];
if (schemes.some((c) => c !== 'light' && c !== 'dark')) await fail('--scheme takes light, dark, or light,dark');
const media = opt.media ? opt.media.split(',') : [];
for (const m of media) if (!Object.hasOwn(MEDIA, m)) await fail(`unknown --media ${m}; use ${Object.keys(MEDIA).join(', ')}`);

const [target, out] = pos;
const url = await resolveTarget(target, opt.root);
const cdp = await launch(20000 + widths.length * schemes.length * 30000);
const { send, evaluate } = cdp;
await send('Page.enable');

// Selectors go into page JS as JSON strings, so quotes in them can't break the expression.
const q = (css) => `document.querySelector(${JSON.stringify(css)})`;
// scroll: bring it into view first (focus, hover); the capture box doesn't scroll, so a hover above it stays under the pointer.
const box = async (css, what, scroll = true) => {
  const r = await evaluate(`(() => { const el = ${q(css)}; if (!el) return null; ${scroll ? "el.scrollIntoView({ block: 'center', inline: 'center' });" : ''}
    const b = el.getBoundingClientRect(); return { x: b.left, y: b.top, w: b.width, h: b.height, sx: scrollX, sy: scrollY }; })()`);
  if (!r) await fail(`${what}: no element matches ${css}`);
  if (!(r.w > 0 && r.h > 0)) await fail(`${what}: ${css} has no size (hidden?)`);
  return r;
};

let overflow = false;
for (const width of widths) for (const scheme of schemes) {
  const mobile = width < 700;
  await emulate(cdp, { width, height, scheme, media });
  await load(cdp, url);
  for (const m of media) {
    const [name, value] = MEDIA[m];
    if (!(await evaluate(`matchMedia('(${name}: ${value})').matches`))) await fail(`this Chrome can't emulate --media ${m}`);
  }
  if (opt['wait-for']) await waitFor(cdp, opt['wait-for']);
  if (opt.eval) {
    const v = await evaluate(opt.eval);
    if (v !== undefined) console.log(`eval: ${JSON.stringify(v)}`);
  }
  if (opt.focus) {
    await box(opt.focus, '--focus');
    // A Tab press marks the last input as keyboard, so the focus() below matches :focus-visible.
    for (const type of ['rawKeyDown', 'keyUp']) await send('Input.dispatchKeyEvent', { type, key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
    await evaluate(`${q(opt.focus)}.focus({ preventScroll: true })`);
  }
  if (opt.hover) {
    const b = await box(opt.hover, '--hover');
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: b.x + b.w / 2, y: b.y + b.h / 2 });
  }
  await sleep(wait);
  const [sw, sh, hasViewport] = await evaluate("[document.documentElement.scrollWidth, document.documentElement.scrollHeight, !!document.querySelector('meta[name=viewport]')]");
  let clip = { x: 0, y: 0, width, height: opt.full ? sh : height, scale: 1 };
  if (opt.selector) {
    const b = await box(opt.selector, '--selector', false);
    const x = Math.max(0, Math.floor(b.x + b.sx)), y = Math.max(0, Math.floor(b.y + b.sy));
    clip = { x, y, width: Math.ceil(b.x + b.sx + b.w) - x, height: Math.ceil(b.y + b.sy + b.h) - y, scale: 1 };
  }
  const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: opt.full || !!opt.selector, clip });
  const base = out.replace(/\.[^./\\]+$/, '');
  const file = base + (widths.length > 1 ? `-${width}` : '') + (schemes.length > 1 ? `-${scheme}` : '') + '.png';
  writeFileSync(file, Buffer.from(shot.data, 'base64'));
  const wide = sw > width;
  overflow ||= wide;
  const note = mobile && !hasViewport ? '  no <meta name=viewport>: phones lay this page out at 980px' : '';
  console.log(`${file}  ${clip.width}x${clip.height}  page ${sw}x${sh}${wide ? `  overflow: ${sw - width}px wider than viewport` : ''}${note}`);
}
await cdp.close();
process.exit(overflow ? 1 : 0);
