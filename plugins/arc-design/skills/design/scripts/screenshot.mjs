#!/usr/bin/env node
// Screenshot a page in headless Chrome over the DevTools protocol, at any width (the --screenshot flag clamps windows to ~500px).
// Usage: node screenshot.mjs <url|file> <out.png> [--width 1280,390] [--height 900] [--full] [--scheme light,dark] [--media list]
//          [--wait-for css] [--eval "js"] [--click css]... [--ax-diff] [--focus css] [--hover css] [--selector css] [--wait 500] [--root dir]
//          [--cookie name=value]... [--header "Name: value"]...
//   --width     one or more comma-separated widths; widths under 700 emulate a mobile device.
//   --scheme    prefers-color-scheme per shot, one or both of light,dark (default light, whatever the OS uses). Several widths or schemes name the files out-<width>-<scheme>.png.
//   --media     media features for every shot: reduced-motion, contrast-more, reduced-transparency, forced-colors.
//   --full      capture the whole page instead of one viewport.
//   --wait-for  wait until this element exists and has a size (async chart, fetched data); exit 2 after 10s.
//   --eval      JS run after load, before the shot (reveal a step, set a data-theme class, stub fetch). Awaited if it returns a promise.
//   --click     click this element with the real pointer after --eval; repeat to click several in order.
//   --ax-diff   print how the accessibility tree changed across the clicks (+ added, - removed node lines), or "no accessibility-tree change".
//   --cookie    cookie for the target's origin, name=value; repeat it or give a comma list (a page behind login).
//   --header    request header for the target's origin, "Name: value"; repeatable (Authorization: Bearer ...).
//   --focus     focus this element as a keyboard user would, so :focus-visible applies.
//   --hover     move the real pointer over this element (a script can't trigger :hover).
//   --selector  capture only this element's box instead of the viewport.
//   --wait      extra ms after load and fonts (default 500).
//   --root      a local file is served over http from this directory (default: the file's directory), so root-relative assets (href="/style.css") load.
// Prints one line per width: file, page size, and "overflow" when the page is wider than the viewport.
// Exit 0 ok, 1 shots written but some width overflows horizontally, 2 no shot (usage, no Chrome, Node < 22, navigation or HTTP error, eval error, timeout).
import { writeFileSync } from 'node:fs';
import { MEDIA, applyAuth, box as boxOf, emulate, fail, launch, load, parseArgs, q, realClick, resolveTarget, sleep, waitFor } from './cdp.mjs';

const USAGE = 'Usage: node screenshot.mjs <url|file> <out.png> [--width 1280,390] [--height 900] [--full] [--scheme light,dark] [--media list]'
  + ' [--wait-for css] [--eval "js"] [--click css]... [--ax-diff] [--focus css] [--hover css] [--selector css] [--wait 500] [--root dir]'
  + ' [--cookie name=value]... [--header "Name: value"]...';
const opt = { width: '1280', height: '900', wait: '500', eval: '', root: '', full: false,
  scheme: '', media: '', 'wait-for': '', focus: '', hover: '', selector: '', click: [], cookie: [], header: [], 'ax-diff': false };
const pos = await parseArgs(process.argv.slice(2), opt, ['full', 'ax-diff'], USAGE);
if (pos.length !== 2) await fail(USAGE);
const widths = [...new Set(opt.width.split(',').map(Number))];
const height = Number(opt.height);
const wait = Number(opt.wait);
if (widths.some((w) => !(w > 0)) || !(height > 0) || !(wait >= 0)) await fail('--width and --height take positive numbers, --wait a number of ms');
const schemes = [...new Set((opt.scheme || 'light').split(','))];
if (schemes.some((c) => c !== 'light' && c !== 'dark')) await fail('--scheme takes light, dark, or light,dark');
const media = opt.media ? opt.media.split(',') : [];
for (const m of media) if (!Object.hasOwn(MEDIA, m)) await fail(`unknown --media ${m}; use ${Object.keys(MEDIA).join(', ')}`);
if (opt['ax-diff'] && !opt.click.length) await fail('--ax-diff needs at least one --click');

const [target, out] = pos;
const url = await resolveTarget(target, opt.root);
const cdp = await launch(20000 + widths.length * schemes.length * 30000);
const { send, evaluate } = cdp;
await send('Page.enable');
await applyAuth(cdp, url, opt.cookie, opt.header);

const box = (css, what, scroll) => boxOf(cdp, css, what, scroll);

const AX_NOISE = new Set(['generic', 'none', 'presentation', 'InlineTextBox', 'LineBreak', 'RootWebArea', 'WebArea', 'paragraph', 'group', 'Section', 'LayoutTable']);
const AX_STATE = ['expanded', 'checked', 'selected', 'pressed', 'disabled', 'invalid', 'modal', 'busy'];
const TOGGLES = new Set(['expanded', 'checked', 'pressed']);
// One line per meaningful node, indented by meaningful depth; text that repeats its parent's name is dropped.
const axTree = async () => {
  const { nodes } = await send('Accessibility.getFullAXTree');
  const byId = new Map(nodes.map((n) => [n.nodeId, n]));
  const lines = [];
  const walk = (n, depth, parentName) => {
    if (!n) return;
    const role = n.role?.value ?? '';
    const name = String(n.name?.value ?? '').replace(/\s+/g, ' ').trim().slice(0, 80);
    const keep = !n.ignored && !AX_NOISE.has(role) && !(role === 'StaticText' && (!name || parentName.includes(name)));
    if (keep) {
      const props = Object.fromEntries((n.properties ?? []).map((p) => [p.name, p.value?.value]));
      // A false expanded, checked, or pressed is a state the click can flip; a false selected or disabled is just noise.
      const state = AX_STATE.filter((k) => props[k] !== undefined && (TOGGLES.has(k) || String(props[k]) !== 'false'))
        .map((k) => (String(props[k]) === 'true' ? k : `${k}=${props[k]}`));
      const value = n.value?.value;
      if (value !== undefined && value !== '') state.push(`value=${JSON.stringify(String(value).slice(0, 40))}`);
      lines.push(`${'  '.repeat(depth)}${role}${name ? ` ${JSON.stringify(name)}` : ''}${state.length ? ' ' + state.join(' ') : ''}`);
    }
    for (const id of n.childIds ?? []) walk(byId.get(id), keep ? depth + 1 : depth, keep && name ? name : parentName);
  };
  walk(nodes.find((n) => !n.parentId), 0, '');
  return lines;
};
// Longest-common-subsequence line diff; past ~4M cells it falls back to a multiset difference, which loses order but not content.
const lineDiff = (a, b) => {
  if (a.length * b.length > 4e6) {
    const minus = (xs, ys) => {
      const left = ys.reduce((m, y) => m.set(y, (m.get(y) ?? 0) + 1), new Map());
      return xs.filter((x) => { const n = left.get(x) ?? 0; left.set(x, n - 1); return n <= 0; });
    };
    return [...minus(a, b).map((x) => '- ' + x), ...minus(b, a).map((x) => '+ ' + x)];
  }
  const w = b.length + 1, t = new Uint32Array((a.length + 1) * w);
  for (let i = a.length - 1; i >= 0; i--) for (let j = b.length - 1; j >= 0; j--) t[i * w + j] = a[i] === b[j] ? t[(i + 1) * w + j + 1] + 1 : Math.max(t[(i + 1) * w + j], t[i * w + j + 1]);
  const out = [];
  let i = 0, j = 0;
  while (i < a.length || j < b.length) {
    if (i < a.length && j < b.length && a[i] === b[j]) { i++; j++; } else if (j < b.length && (i === a.length || t[i * w + j + 1] >= t[(i + 1) * w + j])) out.push('+ ' + b[j++]); else out.push('- ' + a[i++]);
  }
  return out;
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
  let before;
  if (opt['ax-diff']) { await sleep(wait); before = await axTree(); }
  for (const css of opt.click) {
    const hit = await realClick(cdp, css);
    if (hit) console.log(`click ${css}: the pointer lands on ${hit}, which covers it`);
    await sleep(100);
  }
  if (opt['ax-diff']) {
    await sleep(Math.max(wait, 300));
    const diff = lineDiff(before, await axTree());
    const where = widths.length * schemes.length > 1 ? ` ${width}/${scheme}` : '';
    if (!diff.length) console.log(`ax-diff${where}: no accessibility-tree change after clicking ${opt.click.join(', ')}`);
    else {
      console.log(`ax-diff${where}: ${diff.filter((l) => l[0] === '+').length} added, ${diff.filter((l) => l[0] === '-').length} removed after clicking ${opt.click.join(', ')}`);
      for (const l of diff.slice(0, 80)) console.log('  ' + l);
      if (diff.length > 80) console.log(`  ... ${diff.length - 80} more lines`);
    }
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
