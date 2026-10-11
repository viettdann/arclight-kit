#!/usr/bin/env node
// Measure rendering defects on a live page in headless Chrome: what overflows, clips, overlaps, fails contrast, loses focus, or errors.
// Usage: node ui_check.mjs <url|file> [--width 375,768,1280,1920] [--height 900] [--scheme light|dark|light,dark] [--wait-for css]
//          [--eval "js"] [--click css]... [--wait 500] [--root dir] [--tabs 40] [--shot out.png] [--full] [--perf] [--save f.json] [--compare f.json]
//          [--links] [--cookie name=value]... [--header "Name: value"]... [--stress[=text,spacing]] [--json]
//   --click  real-pointer click after --eval, repeatable, in order; with --perf, also its time to the next paint and the shift after it.
//   --tabs   how many Tab presses the focus check walks (0 skips it); it runs once, at the widest width under 1600.
//   --shot   also write a screenshot per width and scheme (out-<width>[-<scheme>].png), taken before the focus check; --full for the whole page.
//   --perf   also report the LCP element and load-time layout shifts, and print load timings, long tasks, and bytes of one uncached load.
//   --save   write those numbers (median of 3 uncached loads at the focus-check width) and the console messages to a baseline file.
//   --compare  as --save; flags timings up >50% and >500ms, JS/CSS bytes up >25% and >1 KB; drops baseline and single-load console messages.
//   --links  request every same-origin link once (HEAD, GET on 405) and report 4xx, 5xx, and failures; only for a local or private host.
//   --cookie, --header  send a cookie (name=value, repeatable or comma list) or a header ("Name: value", repeatable) to the target's origin.
//   --stress  lengthen text ~40%, add long tokens, emoji, and CJK; =spacing applies WCAG 1.4.12 text spacing instead, =text,spacing both.
//   --json   print the findings as JSON instead of text.
//   Other options work as in design/scripts/screenshot.mjs.
// Also reads head metadata once: title, description, canonical, og:url, share images, robots, JSON-LD.
// On a page that links a manifest or sets apple-mobile-web-app-capable, also fetches its same-origin install assets once, without cookies.
// Findings are P1 (breaks use or access), P2 (degrades it), P3 (minor); [review] marks heuristics to confirm in a screenshot.
// Exit 0 nothing at P1 or P2, 1 findings at P1 or P2, 2 the check couldn't run (usage, no Chrome, Node < 22, navigation or HTTP error, timeout).
import { readFileSync, writeFileSync } from 'node:fs';
import { inflateSync } from 'node:zlib';
import { applyAuth, emulate, fail, launch, load, parseArgs, q, realClick, resolveTarget, sleep, waitFor } from '../../design/scripts/cdp.mjs';

const USAGE = 'Usage: node ui_check.mjs <url|file> [--width 375,768,1280,1920] [--height 900] [--scheme light|dark|light,dark] [--wait-for css]'
  + ' [--eval "js"] [--click css]... [--wait 500] [--root dir] [--tabs 40] [--shot out.png] [--full] [--perf] [--save f.json] [--compare f.json]'
  + ' [--links] [--cookie name=value]... [--header "Name: value"]... [--stress[=text,spacing]] [--json]';
const opt = { width: '375,768,1280,1920', height: '900', scheme: 'light', 'wait-for': '', eval: '', wait: '500', root: '', tabs: '40',
  shot: '', full: false, perf: false, json: false, links: false, save: '', compare: '', cookie: [], header: [], stress: '', click: [] };
// A bare --stress would otherwise take the next argument as its value.
const pos = await parseArgs(process.argv.slice(2).map((a) => (a === '--stress' ? '--stress=on' : a)), opt, ['full', 'perf', 'json', 'links'], USAGE);
const modes = new Set(opt.stress === 'on' ? ['text'] : opt.stress.split(',').filter(Boolean));
if ([...modes].some((m) => m !== 'text' && m !== 'spacing')) await fail('--stress takes no value or a comma list of text, spacing');
if (pos.length !== 1) await fail(USAGE);
const widths = [...new Set(opt.width.split(',').map(Number))];
const height = Number(opt.height), wait = Number(opt.wait), tabs = Number(opt.tabs);
if (widths.some((w) => !(w > 0)) || !(height > 0) || !(wait >= 0) || !(tabs >= 0)) await fail('--width, --height, --wait, and --tabs take numbers');
const schemes = [...new Set(opt.scheme.split(','))];
if (schemes.some((c) => c !== 'light' && c !== 'dark')) await fail('--scheme takes light, dark, or light,dark');
let baseline = null;
if (opt.compare) {
  try { baseline = JSON.parse(readFileSync(opt.compare, 'utf8')); } catch (e) { await fail(`--compare: cannot read ${opt.compare}: ${e.message}`); }
  if (!baseline?.metrics) await fail(`--compare: ${opt.compare} is not a file written by --save`);
}
const samples = opt.save || opt.compare ? 3 : opt.perf ? 1 : 0;

const MESSAGE_CHECKS = ['js-error', 'console'];
const SEVERITY = { overflow: 1, contrast: 1, focus: 1, name: 1, 'broken-image': 1, 'js-error': 1, 'request-asset': 1,
  clipped: 2, overlap: 2, target: 2, distorted: 2, 'placeholder-label': 2, console: 2, request: 2, lang: 2, 'zoom-blocked': 2, 'lcp-lazy': 2,
  'layout-shift': 2, clickable: 1, 'broken-link': 2, 'perf-regression': 2, 'target-touch': 3, favicon: 3, alt: 3, heading: 3, viewport: 3, 'contrast-unmeasured': 3, lcp: 3,
  'text-over-media-contrast': 1, 'content-hidden-at-rest': 2, 'clipped-popover': 2, 'tiny-text': 2, 'input-zoom': 2, 'line-length': 3, 'tight-leading': 3, 'all-caps-body': 3,
  'wide-tracking': 3, 'edge-flush-text': 3, 'nested-card': 3, 'icon-tile': 3, 'heading-rhythm': 3,
  title: 2, 'meta-duplicate': 2, canonical: 2, 'share-image': 2, noindex: 2, 'json-ld': 2, 'meta-js-only': 2, 'meta-missing': 3, 'meta-length': 3,
  'install-asset': 2, 'install-icon': 3, 'install-meta': 3, 'inp-slow': 2, inp: 3, 'layout-shift-input': 2, 'duplicate-id-ref': 2, 'duplicate-id': 3, 'link-purpose': 3 };

const kb = (n) => `${(n / 1024).toFixed(1)} KB`;
const lum = (rgb) => { const [r, g, b] = rgb.map((v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };

// Chrome's screenshots are 8-bit RGB or RGBA, non-interlaced; anything else returns null and the text stays unmeasured.
const decodePng = (b64) => {
  const buf = Buffer.from(b64, 'base64');
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20), ch = { 2: 3, 6: 4 }[buf[25]];
  if (buf[24] !== 8 || !ch || buf[28] !== 0) return null;
  const idat = [];
  for (let o = 8; o < buf.length; o += 12 + buf.readUInt32BE(o)) if (buf.toString('latin1', o + 4, o + 8) === 'IDAT') idat.push(buf.subarray(o + 8, o + 8 + buf.readUInt32BE(o)));
  const raw = inflateSync(Buffer.concat(idat)), stride = w * ch, px = Buffer.alloc(h * stride);
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)];
    for (let x = 0; x < stride; x++) {
      const a = x >= ch ? px[y * stride + x - ch] : 0, b = y ? px[(y - 1) * stride + x] : 0, c = x >= ch && y ? px[(y - 1) * stride + x - ch] : 0;
      const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
      px[y * stride + x] = raw[y * (stride + 1) + 1 + x] + [0, a, b, (a + b) >> 1, pa <= pb && pa <= pc ? a : pb <= pc ? b : c][f];
    }
  }
  return { w, h, ch, px };
};

// Runs inside the page (installed as window.__cssPath): a short selector that matches only this element, for the report.
function cssPath(el) {
  const parts = [];
  for (let e = el; e && e.nodeType === 1 && e !== document.documentElement; e = e.parentElement) {
    if (e.id && document.querySelectorAll('#' + CSS.escape(e.id)).length === 1) { parts.unshift('#' + CSS.escape(e.id)); break; }
    let p = e.tagName.toLowerCase();
    // Variant and arbitrary-value classes (md:flex, w-[20px]) make unreadable selectors; plain ones identify the element.
    const cls = [...e.classList].filter((c) => !/[:[\]/.]/.test(c)).slice(0, 2);
    if (cls.length) p += '.' + cls.map((c) => CSS.escape(c)).join('.');
    const same = e.parentElement ? [...e.parentElement.children].filter((c) => c.tagName === e.tagName) : [];
    if (same.length > 1) p += `:nth-of-type(${same.indexOf(e) + 1})`;
    parts.unshift(p);
    if (document.querySelectorAll(parts.join(' > ')).length === 1 || parts.length >= 5) break;
  }
  return parts.join(' > ');
}

// Runs inside the page. Returns findings as { check, selector, text, detail, review }.
function audit({ mobile, phone, spacing }) {
  const out = [];
  const vw = document.documentElement.clientWidth;
  const sel = window.__cssPath;
  const label = (el) => {
    const t = (el.innerText || el.getAttribute('aria-label') || el.getAttribute('alt') || el.getAttribute('placeholder') || '').trim().replace(/\s+/g, ' ');
    return t ? `"${t.length > 40 ? t.slice(0, 40) + '…' : t}"` : '';
  };
  const add = (check, el, detail, review = false) => out.push({ check, selector: el ? sel(el) : '', text: el ? label(el) : '', detail, review });
  const box = (el) => el.getBoundingClientRect();
  const visible = (el) => el.checkVisibility({ opacityProperty: true, visibilityProperty: true }) && box(el).width > 0 && box(el).height > 0;
  const SKIP = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'BR', 'WBR', 'OPTION']);
  const all = [...document.body.querySelectorAll('*')].filter((el) => !SKIP.has(el.tagName));
  const ownText = (el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());

  // Overflow: report the element that sticks out of a parent that doesn't, so the fix lands on the cause.
  const rootHides = ['hidden', 'clip'].includes(getComputedStyle(document.body).overflowX) || ['hidden', 'clip'].includes(getComputedStyle(document.documentElement).overflowX);
  if (document.documentElement.scrollWidth > vw + 1 || rootHides) {
    const scrollsOrClips = (el) => {
      for (let a = el.parentElement; a && a !== document.body && a !== document.documentElement; a = a.parentElement) {
        if (getComputedStyle(a).overflowX !== 'visible') return true;
      }
      return false;
    };
    const culprits = all.filter((el) => visible(el) && getComputedStyle(el).position !== 'fixed' && box(el).right > vw + 1 && !scrollsOrClips(el));
    const set = new Set(culprits);
    for (const el of culprits) {
      if (set.has(el.parentElement)) continue;
      const r = box(el);
      add('overflow', el, `right edge at ${Math.round(r.right)}px, ${Math.round(r.right - vw)}px past the ${vw}px viewport`
        + (rootHides ? ' (hidden by overflow-x on html or body, not fixed)' : ''));
    }
  }

  // Clipped text: cut by overflow without an ellipsis or a line clamp.
  for (const el of all) {
    if (!ownText(el) || !visible(el)) continue;
    const s = getComputedStyle(el);
    const cutX = ['hidden', 'clip'].includes(s.overflowX) && el.scrollWidth > el.clientWidth + 1 && s.textOverflow !== 'ellipsis';
    const cutY = ['hidden', 'clip'].includes(s.overflowY) && el.scrollHeight > el.clientHeight + 1 && s.webkitLineClamp === 'none';
    if (cutX || cutY) add('clipped', el, cutX ? `text is ${el.scrollWidth - el.clientWidth}px wider than its box, cut without an ellipsis`
      : `text is ${el.scrollHeight - el.clientHeight}px taller than its box, cut without a line clamp`, true);
  }

  // Colors are resolved by a canvas, which understands computed color syntax (rgb, oklch, color()) and composites alpha.
  const ctx = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const alphaOf = (c) => { ctx.clearRect(0, 0, 1, 1); ctx.fillStyle = '#000'; ctx.fillStyle = c; ctx.fillRect(0, 0, 1, 1); return ctx.getImageData(0, 0, 1, 1).data[3] / 255; };
  const flatten = (layers) => {
    ctx.clearRect(0, 0, 1, 1);
    for (const c of layers) { ctx.fillStyle = c; ctx.fillRect(0, 0, 1, 1); }
    const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
    return [r, g, b];
  };
  const lum = (rgb) => { const [r, g, b] = rgb.map((v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const hex = (rgb) => '#' + rgb.map((v) => v.toString(16).padStart(2, '0')).join('');
  // The page's own canvas color (dark under color-scheme: dark), read from a probe since a canvas can't parse system colors.
  const probe = document.createElement('div');
  probe.style.cssText = 'position:absolute;width:0;height:0;background-color:Canvas';
  document.body.append(probe);
  const canvasColor = getComputedStyle(probe).backgroundColor;
  probe.remove();
  const canvasBase = () => canvasColor;

  // Contrast: per element that holds text, against the backgrounds of its ancestors.
  const unmeasured = [];
  const seen = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const el = n.parentElement;
    if (!el || seen.has(el) || !n.textContent.trim() || SKIP.has(el.tagName) || el.closest('svg') || !visible(el)) continue;
    seen.add(el);
    if (el.closest(':disabled, [aria-disabled="true"]')) continue;
    const layers = [];
    let unknown = '', positioned = false, opaque = false;
    for (let a = el; a; a = a.parentElement) {
      const s = getComputedStyle(a);
      if (s.backgroundImage !== 'none') { unknown = 'an image or gradient'; break; }
      if (s.backdropFilter && s.backdropFilter !== 'none') { unknown = 'glass'; break; }
      if (alphaOf(s.backgroundColor) > 0) { layers.unshift(s.backgroundColor); if (alphaOf(s.backgroundColor) >= 1) { opaque = true; break; } }
      if (a !== el && ['absolute', 'fixed'].includes(s.position)) positioned = true;
    }
    if (unknown) { unmeasured.push(el); continue; }
    if (!opaque) layers.unshift(canvasBase());
    const s = getComputedStyle(el);
    const bg = flatten(layers);
    const fg = flatten([...layers, s.color]);
    const [l1, l2] = [lum(fg), lum(bg)].sort((a, b) => b - a);
    const ratio = (l1 + 0.05) / (l2 + 0.05);
    const size = parseFloat(s.fontSize), weight = Number(s.fontWeight) || 400;
    const min = size >= 24 || (size >= 18.66 && weight >= 700) ? 3 : 4.5;
    if (ratio < min) add('contrast', el, `${(Math.floor(ratio * 100) / 100).toFixed(2)}:1, needs ${min}:1 (${hex(fg)} on ${hex(bg)})`
      + (positioned ? '; positioned text, the real background may be a sibling' : ''), positioned);
  }
  // Measured from screenshots by the caller, which reaches the page only through this list.
  window.__uiMedia = unmeasured;

  // Overlap: line boxes of text from different elements that cross each other, cut to what their overflow ancestors let show.
  const clips = new Map();
  const clipOf = (el) => {
    if (clips.has(el)) return clips.get(el);
    let c = { left: -Infinity, top: -Infinity, right: Infinity, bottom: Infinity };
    for (let a = el; a && a !== document.documentElement; a = a.parentElement) {
      const s = getComputedStyle(a);
      if (s.overflowX === 'visible' && s.overflowY === 'visible') continue;
      const r = box(a);
      c = { left: Math.max(c.left, r.left), top: Math.max(c.top, r.top), right: Math.min(c.right, r.right), bottom: Math.min(c.bottom, r.bottom) };
    }
    clips.set(el, c);
    return c;
  };
  const lines = [];
  const walker2 = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = walker2.nextNode(); n && lines.length < 1500; n = walker2.nextNode()) {
    const el = n.parentElement;
    if (!el || !n.textContent.trim() || SKIP.has(el.tagName) || !visible(el)) continue;
    const range = document.createRange();
    range.selectNodeContents(n);
    const c = clipOf(el);
    for (const raw of range.getClientRects()) {
      const r = { left: Math.max(raw.left, c.left), top: Math.max(raw.top, c.top), right: Math.min(raw.right, c.right), bottom: Math.min(raw.bottom, c.bottom) };
      r.width = r.right - r.left; r.height = r.bottom - r.top;
      if (r.width > 1 && r.height > 1) lines.push({ el, r });
    }
  }
  const pairs = new Set();
  for (let i = 0; i < lines.length; i++) for (let j = i + 1; j < lines.length; j++) {
    const a = lines[i], b = lines[j];
    if (a.el === b.el || a.el.contains(b.el) || b.el.contains(a.el)) continue;
    const ix = Math.min(a.r.right, b.r.right) - Math.max(a.r.left, b.r.left);
    const iy = Math.min(a.r.bottom, b.r.bottom) - Math.max(a.r.top, b.r.top);
    if (ix > 2 && iy > 0.3 * Math.min(a.r.height, b.r.height)) {
      const key = sel(a.el) + '|' + sel(b.el);
      if (pairs.has(key)) continue;
      pairs.add(key);
      add('overlap', a.el, `text crosses ${sel(b.el)} ${label(b.el)} by ${Math.round(ix)}×${Math.round(iy)}px`, true);
    }
  }

  // Targets and names of interactive elements.
  const INTERACTIVE = 'a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button], [role=link], [role=checkbox], [role=radio],'
    + ' [role=switch], [role=tab], [role=menuitem], [tabindex]:not([tabindex="-1"])';
  const nameOf = (el) => {
    const aria = el.getAttribute('aria-label');
    if (aria && aria.trim()) return aria;
    const by = el.getAttribute('aria-labelledby');
    if (by) { const t = by.split(/\s+/).map((id) => document.getElementById(id)?.textContent ?? '').join(' ').trim(); if (t) return t; }
    if (el.labels && [...el.labels].some((l) => l.textContent.trim())) return 'label';
    const type = (el.getAttribute('type') || '').toLowerCase();
    if (el.tagName === 'INPUT' && ['submit', 'reset', 'button'].includes(type)) return el.value || type;
    if (el.tagName === 'INPUT' && type === 'image') return el.getAttribute('alt') || '';
    if (!['INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName)) {
      if (el.textContent.trim()) return el.textContent.trim();
      if (el.querySelector('img[alt]:not([alt=""]), svg title, [aria-label]')) return 'image';
    }
    return el.getAttribute('title')?.trim() || '';
  };
  // A ::before or ::after positioned over the control is the usual way to enlarge a target without changing its look, so it counts.
  const hitArea = (el, r) => {
    let { left, top, right, bottom } = r;
    const s = getComputedStyle(el);
    if (s.position === 'static') return r;
    const ox = r.left + parseFloat(s.borderLeftWidth), oy = r.top + parseFloat(s.borderTopWidth);
    for (const p of ['::before', '::after']) {
      const ps = getComputedStyle(el, p);
      if (ps.content === 'none' || ps.display === 'none' || ps.position !== 'absolute' || ps.pointerEvents === 'none') continue;
      const [l, t, w, h] = [ps.left, ps.top, ps.width, ps.height].map(parseFloat);
      if ([l, t, w, h].some(Number.isNaN)) continue;
      left = Math.min(left, ox + l); top = Math.min(top, oy + t);
      right = Math.max(right, ox + l + w); bottom = Math.max(bottom, oy + t + h);
    }
    return { width: right - left, height: bottom - top };
  };
  const coarse = matchMedia('(pointer: coarse)').matches;
  const touch = [];
  for (const el of document.querySelectorAll(INTERACTIVE)) {
    if (!visible(el)) continue;
    const r = box(el);
    const name = nameOf(el);
    if (!name) {
      if (el.getAttribute('placeholder')?.trim()) add('placeholder-label', el, 'the placeholder is the only label; it disappears on input');
      else add('name', el, `<${el.tagName.toLowerCase()}> has no accessible name (label, aria-label, or text)`);
    }
    if (r.width <= 1 || r.height <= 1) continue;
    // A link inside running text is exempt from target size (WCAG 2.5.8 inline exception), and a labelled checkbox's target includes its label.
    if (el.tagName === 'A' && getComputedStyle(el).display === 'inline' && [...el.parentElement.childNodes].some((c) => c !== el && c.textContent.trim())) continue;
    if (el.labels?.length && ['checkbox', 'radio'].includes(el.type)) continue;
    const hit = hitArea(el, r);
    const small = Math.min(hit.width, hit.height);
    const size = `${Math.round(hit.width)}×${Math.round(hit.height)}px`;
    if (small < 24) add('target', el, `${size}, under the 24px minimum`);
    else if (coarse && small < 44) touch.push({ el, small, size });
  }
  // The script can't tell primary controls from secondary ones, so one line lists the smallest and the shot decides which are primary.
  if (touch.length) {
    touch.sort((a, b) => a.small - b.small);
    const rest = touch.slice(1, 3).map((t) => `${sel(t.el)} ${t.size}`).join(', ');
    add('target-touch', touch[0].el, `${touch.length} control(s) with a hit area under 44px under pointer: coarse, smallest ${touch[0].size}`
      + (rest ? `; next: ${rest}` : '') + '; only primary controls need 44px, padded without changing their size', true);
  }

  // Cursor is inherited, so only the element that sets it counts; a pointer or listener on a wrapper of real controls is fine.
  const NATIVE = 'a[href], button, input, select, textarea, summary, label, option, video, audio, iframe, [contenteditable]:not([contenteditable=false])';
  for (const el of all) {
    const onclick = typeof el.onclick === 'function', clicker = !!window.__uiClickers?.has(el), ownPointer = getComputedStyle(el).cursor === 'pointer';
    if (!onclick && !clicker && !ownPointer) continue;
    // React sets a no-op onclick on its root container (iOS click delegation), which is not a handler of the page.
    if (el._reactRootContainer || Object.keys(el).some((k) => k.startsWith('__reactContainer$'))) continue;
    if (el.matches(NATIVE) || el.hasAttribute('role') || el.hasAttribute('tabindex') || !visible(el) || el.parentElement.closest(`${INTERACTIVE}, ${NATIVE}`)) continue;
    const wraps = !!el.querySelector(`${INTERACTIVE}, ${NATIVE}`);
    const pointer = !wraps && ownPointer && getComputedStyle(el.parentElement).cursor !== 'pointer';
    const r = box(el);
    const listener = !wraps && clicker && r.width * r.height < 0.5 * vw * innerHeight;
    if (!onclick && !pointer && !listener) continue;
    add('clickable', el, `clickable (${onclick ? 'onclick' : listener ? 'click listener' : 'cursor: pointer'}) but no keyboard access:`
      + ' use a <button> or <a href>, or add a role, tabindex="0", and Enter/Space handling', !onclick && !listener);
  }

  for (const img of document.images) {
    if (getComputedStyle(img).display === 'none') continue;
    if (img.complete && img.naturalWidth === 0 && img.getAttribute('src')) { add('broken-image', img, `failed to load ${img.currentSrc || img.src}`); continue; }
    if (!img.hasAttribute('alt')) add('alt', img, 'no alt attribute (alt="" if it is decorative)');
    if (!visible(img) || !img.naturalWidth) continue;
    const r = box(img);
    const natural = img.naturalWidth / img.naturalHeight, shown = r.width / r.height;
    if (getComputedStyle(img).objectFit === 'fill' && Math.abs(shown - natural) / natural > 0.03) {
      add('distorted', img, `shown at ${shown.toFixed(2)}:1, the image is ${natural.toFixed(2)}:1 (object-fit: cover?)`);
    }
  }

  const headings = [...document.querySelectorAll('h1, h2, h3, h4, h5, h6')].filter(visible);
  const h1s = headings.filter((h) => h.tagName === 'H1');
  if (h1s.length > 1) add('heading', h1s[1], `${h1s.length} h1 elements on the page`);
  for (let i = 1; i < headings.length; i++) {
    const prev = Number(headings[i - 1].tagName[1]), cur = Number(headings[i].tagName[1]);
    if (cur > prev + 1) add('heading', headings[i], `h${prev} then h${cur}, a level skipped`);
  }

  // A label or ARIA reference resolves to the first element with the id, so a repeated component's second copy takes the first's name or error.
  const REFS = ['for', 'aria-labelledby', 'aria-describedby', 'aria-controls', 'aria-activedescendant', 'aria-owns', 'aria-errormessage', 'list'];
  const byId = new Map(), referenced = new Set();
  for (const el of document.querySelectorAll('[id]')) if (el.id && !el.closest('svg, template')) byId.set(el.id, [...(byId.get(el.id) ?? []), el]);
  for (const a of REFS) for (const el of document.querySelectorAll(`[${a}]`)) for (const id of el.getAttribute(a).split(/\s+/)) referenced.add(id);
  for (const a of document.querySelectorAll('a[href^="#"]')) {
    const raw = a.getAttribute('href').slice(1);
    // A malformed escape (href="#100%") is still a usable literal fragment, so it is compared as written.
    try { referenced.add(decodeURIComponent(raw)); } catch { referenced.add(raw); }
  }
  let loose = 0;
  for (const [id, els] of byId) {
    if (els.length < 2) continue;
    if (referenced.has(id)) add('duplicate-id-ref', els[1], `id "${id}" on ${els.length} elements; its label or ARIA reference reaches only the first`);
    else if (loose++ < 3) add('duplicate-id', els[1], `id "${id}" on ${els.length} elements`);
  }
  // The layout heuristics below are capped per check, so one repeated component doesn't flood the report.
  const counts = {};
  const some = (check, el, detail, review = true) => { counts[check] = (counts[check] ?? 0) + 1; if (counts[check] <= 5) add(check, el, detail, review); };
  const HEADING = 'h1, h2, h3, h4, h5, h6, [role=heading]';
  const CONTROL = `${INTERACTIVE}, label, nav`;
  const ownLen = (el) => [...el.childNodes].reduce((n, c) => n + (c.nodeType === 3 ? c.textContent.trim().length : 0), 0);

  // A screen reader's links list reads each name alone, so "Read more" five times, or one name on two different pages, hides where each goes.
  const GENERIC = /^(?:click here|here|read more|more|learn more|details|link|this|go)$/;
  const byName = new Map();
  for (const a of document.querySelectorAll('a[href]')) {
    if (!visible(a)) continue;
    const n = nameOf(a).toLowerCase().replace(/[^\p{L}\p{N} ]/gu, ' ').replace(/\s+/g, ' ').trim();
    if (!n || n === 'image') continue;
    if (GENERIC.test(n)) { some('link-purpose', a, `link named "${n}" alone; name the destination, or an aria-label that starts with the visible words`); continue; }
    // A row's cell gives its link context (WCAG 2.4.4), so a column of "Edit" links isn't ambiguous.
    if (a.closest('td, th, [role=cell], [role=gridcell]')) continue;
    let u;
    try { u = new URL(a.href); } catch { continue; }
    if (u.origin !== location.origin) continue;
    if (!byName.has(n)) byName.set(n, new Map());
    byName.get(n).set(u.pathname + u.search, a);
  }
  for (const [n, urls] of byName) if (urls.size > 1) some('link-purpose', [...urls.values()][1], `${urls.size} links named "${n}" go to different pages`);

  // Typography floors and line length, from computed style and the rendered line boxes.
  for (const el of all) {
    if (!ownText(el) || !visible(el) || el.closest('svg, pre, code')) continue;
    const s = getComputedStyle(el), size = parseFloat(s.fontSize), len = ownLen(el);
    const heading = !!el.closest(HEADING), control = !!el.closest(CONTROL), body = !heading && !control;
    const lead = (s.lineHeight === 'normal' ? 1.2 * size : parseFloat(s.lineHeight)) / size, track = (parseFloat(s.letterSpacing) || 0) / size;
    if (!heading && len > 50 && lead < 1.3) some('tight-leading', el, `line-height ${lead.toFixed(2)}× the ${size}px font, under 1.3`);
    if (!heading && size < (control ? 11 : 12)) some('tiny-text', el, `${size}px ${control ? 'control' : 'body'} text, under ${control ? 11 : 12}px`, false);
    if (s.textTransform === 'uppercase' && len > 30) some('all-caps-body', el, `${len} characters set in uppercase`);
    if (body && len > 30 && track > 0.05 && !spacing) some('wide-tracking', el, `letter-spacing ${track.toFixed(2)}em on body text, over 0.05em`);
    const range = document.createRange();
    range.selectNodeContents(el);
    const r = range.getBoundingClientRect(), edge = Math.min(r.left, vw - r.right);
    if (body && len > 30 && edge >= 0 && edge < 16) some('edge-flush-text', el, `text ${Math.round(edge)}px from the viewport edge, under 16px`);
    if (s.display.startsWith('inline') || len <= 80) continue;
    ctx.font = s.font;
    const ch = ctx.measureText('0').width || size / 2, rows = [];
    for (const q of range.getClientRects()) {
      const c = (q.top + q.bottom) / 2, row = rows.find((w) => Math.abs(w.c - c) < size / 2);
      if (row) { row.l = Math.min(row.l, q.left); row.r = Math.max(row.r, q.right); } else if (q.width > 1) rows.push({ c, l: q.left, r: q.right });
    }
    const long = rows.map((w) => (w.r - w.l) / ch).filter((n) => n > 80);
    if (long.length >= 2) some('line-length', el, `${long.length} lines over 80 characters, longest ~${Math.round(Math.max(...long))}ch`);
  }

  // iOS Safari zooms the page into a focused field under 16px and leaves it zoomed; other browsers don't, so only phone widths count.
  if (phone) {
    const FIELD = 'input:not([type]), input[type=text], input[type=search], input[type=email], input[type=url], input[type=tel], input[type=password],'
      + ' input[type=number], textarea, select, [contenteditable]:not([contenteditable=false])';
    for (const el of document.querySelectorAll(FIELD)) {
      if (el.disabled || !visible(el)) continue;
      const size = parseFloat(getComputedStyle(el).fontSize);
      if (size < 16) some('input-zoom', el, `${size}px field; iOS Safari zooms the page on focus under 16px → 16px on touch: \`text-base sm:text-sm\` or a (pointer: coarse) query`, false);
    }
  }

  // Cards: a shadow, or a radius with a border or a background of its own.
  const bgOf = (el) => { for (let a = el; a; a = a.parentElement) { const c = getComputedStyle(a).backgroundColor; if (alphaOf(c) > 0) return c; } return canvasColor; };
  const framed = (s) => parseFloat(s.borderTopWidth) > 0 && s.borderTopStyle !== 'none';
  const cardLike = (el) => {
    const s = getComputedStyle(el);
    if (['absolute', 'fixed'].includes(s.position) || s.display.startsWith('inline') || el.matches(`${CONTROL}, dialog, [popover], [role=dialog], [role=menu], [role=tooltip], [role=listbox]`)) return false;
    const tinted = alphaOf(s.backgroundColor) > 0 && s.backgroundColor !== bgOf(el.parentElement);
    return s.boxShadow !== 'none' || (parseFloat(s.borderTopLeftRadius) > 0 && (framed(s) || tinted));
  };
  const cards = new Set(all.filter((el) => visible(el) && box(el).width >= 50 && box(el).height >= 30 && el.textContent.trim().length >= 10 && cardLike(el)));
  for (const el of cards) {
    let outer = el.parentElement;
    while (outer && !cards.has(outer)) outer = outer.parentElement;
    if (outer) some('nested-card', el, `a card inside the card ${sel(outer)}`);
  }

  // Heading neighbours: a framed icon tile right above it, and spacing that binds it to what precedes it.
  const rhythm = [];
  for (const h of headings) {
    const prev = h.previousElementSibling, next = h.nextElementSibling, r = box(h);
    if (!prev || !visible(prev)) continue;
    const t = box(prev), ts = getComputedStyle(prev), ratio = t.width / t.height;
    if (t.width >= 32 && t.width <= 128 && ratio >= 0.7 && ratio <= 1.4 && (alphaOf(ts.backgroundColor) > 0 || framed(ts))
      && parseFloat(ts.borderTopLeftRadius) < t.width / 2 && t.bottom <= r.top + 1 && prev.querySelector('svg, img, i, [class*=icon]')) {
      some('icon-tile', prev, `${Math.round(t.width)}×${Math.round(t.height)}px icon tile above the heading ${sel(h)}`);
    }
    if (!next || !visible(next)) continue;
    const above = r.top - t.bottom, below = box(next).top - r.bottom;
    if (above >= 0 && below - above >= 12) rhythm.push({ h, above, below });
  }
  if (rhythm.length >= 2) some('heading-rhythm', rhythm[0].h, `${rhythm.length} headings have less space above than below`
    + ` (${Math.round(rhythm[0].above)}px above, ${Math.round(rhythm[0].below)}px below); they read as part of the previous block`);

  // An absolutely positioned menu or popover is cut only by overflow on its containing block or an ancestor of it.
  for (const el of all) {
    if (getComputedStyle(el).position !== 'absolute' || !visible(el) || !el.innerText.trim()) continue;
    const r = box(el);
    for (let a = el.offsetParent; a && a !== document.body && a !== document.documentElement; a = a.parentElement) {
      const s = getComputedStyle(a);
      if (s.overflowX === 'visible' && s.overflowY === 'visible') continue;
      const c = box(a), cut = Math.max(c.left - r.left, r.right - c.right, c.top - r.top, r.bottom - c.bottom);
      if (cut > 1 && r.right > c.left && r.left < c.right && r.bottom > c.top && r.top < c.bottom) { some('clipped-popover', el, `${Math.round(cut)}px cut off by overflow on ${sel(a)}`); break; }
    }
  }

  // Text still transparent after the page was scrolled through: a reveal animation that never ran.
  let total = 0, hidden = 0, firstHidden = null;
  const floats = (el) => { for (let a = el; a; a = a.parentElement) if (['absolute', 'fixed'].includes(getComputedStyle(a).position)) return true; return false; };
  const walker3 = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = walker3.nextNode(); n; n = walker3.nextNode()) {
    const el = n.parentElement, len = n.textContent.trim().length;
    if (!el || !len || SKIP.has(el.tagName) || !el.checkVisibility() || !box(el).width) continue;
    const gone = !el.checkVisibility({ opacityProperty: true, visibilityProperty: true });
    if (gone && floats(el)) continue;
    total += len;
    if (gone) { hidden += len; firstHidden ??= el; }
  }
  if (total >= 200 && hidden >= 150 && hidden / total > 0.3) {
    add('content-hidden-at-rest', firstHidden, `${hidden} of ${total} characters of text stay invisible (opacity 0 or visibility: hidden) after scrolling through the page`, true);
  }

  if (mobile && !document.querySelector('meta[name=viewport]')) add('viewport', null, 'no <meta name=viewport>: phones lay this page out at 980px');
  if (!document.documentElement.getAttribute('lang')?.trim()) add('lang', null, 'no lang on <html>: screen readers and translation guess the language');
  const vp = document.querySelector('meta[name=viewport]')?.getAttribute('content') ?? '';
  const maxScale = /maximum-scale\s*=\s*([\d.]+)/i.exec(vp);
  if ((maxScale && Number(maxScale[1]) < 2) || /user-scalable\s*=\s*(no|0)\b/i.test(vp)) add('zoom-blocked', null, `viewport "${vp}" blocks pinch zoom`);
  return out;
}

// Runs inside the page once: head metadata is the same at every width.
async function metadata({ quiet }) {
  const out = [];
  const add = (check, detail, review = false, selector = '') => out.push({ check, selector, text: '', detail, review });
  const metas = (doc, key) => [...doc.querySelectorAll('meta')].filter((m) => [m.getAttribute('name'), m.getAttribute('property')].some((v) => v?.trim().toLowerCase() === key));
  const content = (doc, key) => metas(doc, key)[0]?.getAttribute('content')?.trim() ?? '';
  // An SVG <title> names the icon, not the page.
  const titles = [...document.querySelectorAll('title')].filter((t) => t instanceof HTMLTitleElement);
  const canonicals = [...document.querySelectorAll('link[rel~="canonical" i]')];
  if (!titles.length || !document.title.trim()) add('title', 'no <title> or an empty one: tabs, history, bookmarks, and results show the URL');
  const counts = { title: titles.length, canonical: canonicals.length };
  for (const k of ['description', 'robots', 'og:url', 'og:title', 'og:description', 'twitter:card']) counts[k] = metas(document, k).length;
  for (const [k, n] of Object.entries(counts)) if (n > 1) add('meta-duplicate', `${n} ${k} tags; two metadata sources compete (layout and page, or a head library and hand-written tags)`);
  let noindexed = false;
  for (const k of ['robots', 'googlebot']) {
    const v = content(document, k);
    if (/\b(noindex|none)\b/i.test(v)) { noindexed = true; add('noindex', `meta ${k} "${v}": search engines drop this page; intended only for private, duplicate, staging, or ad-only pages (seo.md)`, true); }
  }
  const canonical = canonicals[0]?.getAttribute('href')?.trim(), ogUrl = content(document, 'og:url');
  if (canonical === '') add('canonical', 'empty canonical href; it points search engines at nothing');
  else if (canonical !== undefined && !/^https?:\/\//i.test(canonical)) add('canonical', `relative canonical "${canonical}"; write it absolute`);
  else if (canonical && ogUrl) {
    try {
      const a = new URL(canonical, document.baseURI).href, b = new URL(ogUrl, document.baseURI).href;
      if (a !== b) add('canonical', `canonical ${a} and og:url ${b} differ; previews and search credit different URLs`);
    } catch { add('canonical', `canonical "${canonical}" or og:url "${ogUrl}" is not a valid URL`); }
  }
  for (const k of ['og:image', 'og:image:url', 'twitter:image', 'twitter:image:src']) {
    for (const m of metas(document, k)) {
      const v = m.getAttribute('content')?.trim() ?? '';
      if (!/^https?:\/\//i.test(v)) add('share-image', `${k} "${v}" is not an absolute URL; preview fetchers don't resolve it`);
    }
  }
  [...document.querySelectorAll('script[type="application/ld+json" i]')].forEach((s, i) => {
    try { JSON.parse(s.textContent); } catch (e) { add('json-ld', `JSON-LD block ${i + 1} doesn't parse (${e.message}); the whole block is ignored`, false, window.__cssPath(s)); }
  });
  const desc = content(document, 'description'), ogImage = content(document, 'og:image') || content(document, 'og:image:url');
  if (!quiet && !noindexed) {
    // A page with no share tags at all may not be meant for sharing, so only the description is asked of it.
    const shared = !!desc || !!document.querySelector('meta[property^="og:" i]');
    const missing = [!desc && 'meta description', shared && !canonical && 'canonical', shared && !ogImage && 'og:image'].filter(Boolean);
    if (ogImage && !content(document, 'twitter:card')) missing.push('twitter:card (X shows a small card)');
    if (missing.length) add('meta-missing', `no ${missing.join(', ')} on an indexable page`, true);
    if (document.title.trim().length > 60) add('meta-length', `${document.title.trim().length}-character title; rough proxy, results truncate by pixel width`, true);
    if (desc.length > 160) add('meta-length', `${desc.length}-character description; rough proxy, results truncate by pixel width`, true);
  }
  // Share fetchers don't run JS, so a head filled in by client code shows no preview.
  if (/^https?:$/.test(location.protocol) && !quiet) {
    const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), 5000);
    try {
      const r = await fetch(location.href, { credentials: 'same-origin', cache: 'no-store', signal: ctl.signal });
      if (r.ok && /html/i.test(r.headers.get('content-type') ?? '')) {
        const raw = new DOMParser().parseFromString(await r.text(), 'text/html');
        const late = ['og:title', 'og:image', 'description'].filter((k) => content(document, k) && !content(raw, k));
        if (late.length) add('meta-js-only', `${late.join(', ')} set only by client JS; link-preview fetchers read the server HTML`, true);
      }
    } catch {} finally { clearTimeout(timer); }
  }
  return out;
}

// Runs inside the page: longer copy, an unbroken token, emoji, and CJK in place of the real text, so the layout checks see the worst case.
function stress() {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT), nodes = [];
  for (let n = walker.nextNode(); n; n = walker.nextNode()) if (n.textContent.trim() && !n.parentElement.closest('script, style, noscript, template, textarea, svg')) nodes.push(n);
  nodes.forEach((n, i) => {
    const words = n.textContent.trim().split(/\s+/);
    let t = `${n.textContent} ${words.slice(0, Math.ceil(words.length * 0.4)).join(' ')}`;
    if (i % 3 === 1) t = t.replace(/\S{3,}/, 'Wolfeschlegelsteinhausenbergerdorff'.repeat(3));
    if (i % 3 === 2) t += ' 🎉👩‍💻 国際化テキストの確認';
    n.textContent = t;
  });
}

// Runs inside the page: the WCAG 1.4.12 user overrides; text they clip or overlap is lost for readers who need wider spacing.
function spacing() {
  const s = document.createElement('style');
  s.textContent = '*:not(svg, svg *) { line-height: 1.5 !important; letter-spacing: 0.12em !important; word-spacing: 0.16em !important } p { margin-bottom: 2em !important }';
  document.head.append(s);
}

// Runs inside the page: scrolls to the bottom and back so scroll-triggered reveals and lazy content fire.
async function settle() {
  const pause = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let y = 0, i = 0; y < document.documentElement.scrollHeight && i < 60; y += innerHeight * 0.8, i++) { scrollTo({ top: y, behavior: 'instant' }); await pause(50); }
  scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' });
  await pause(50);
  scrollTo({ top: 0, behavior: 'instant' });
  await pause(700);
}

// Runs inside the page: the largest-contentful-paint element and the layout shifts so far, from the buffered performance entries.
async function vitals({ perf }) {
  const sel = window.__cssPath;
  const read = (type) => new Promise((resolve) => {
    try { new PerformanceObserver((list, obs) => { obs.disconnect(); resolve(list.getEntries()); }).observe({ type, buffered: true }); } catch { resolve([]); }
    setTimeout(() => resolve([]), 300);
  });
  const [paints, shifts] = await Promise.all([read('largest-contentful-paint'), read('layout-shift')]);
  const out = [];
  const lcp = paints.at(-1);
  const el = lcp?.element?.isConnected ? lcp.element : null;
  if (el?.tagName === 'IMG' && el.loading === 'lazy') {
    out.push({ check: 'lcp-lazy', selector: sel(el), text: '', detail: 'the largest element in view is a lazy image; drop loading="lazy" and add fetchpriority="high"', review: false });
  }
  if (!perf) return out;
  if (el) {
    const ms = Math.round(lcp.renderTime || lcp.loadTime || lcp.startTime);
    out.push({ check: 'lcp', selector: sel(el), text: '', detail: `largest contentful paint at ${ms}ms${lcp.url ? ` (${lcp.url})` : ''}, lab value`, review: false });
  }
  const firstClick = window.__uiInput?.clickAt[0] ?? Infinity;
  const moved = shifts.filter((s) => !s.hadRecentInput && s.startTime < firstClick);
  const total = moved.reduce((n, s) => n + s.value, 0);
  if (total > 0.1) {
    const nodes = [...new Set(moved.flatMap((s) => s.sources ?? []).map((x) => (x.node?.nodeType === 1 ? x.node : x.node?.parentElement)).filter((n) => n?.isConnected))];
    out.push({ check: 'layout-shift', selector: nodes[0] ? sel(nodes[0]) : '', text: '', review: true,
      detail: `layout shift ${total.toFixed(2)} during load, over 0.1; this moved` + (nodes.length > 1 ? ` with ${nodes.slice(1, 4).map(sel).join(', ')}` : '')
        + '; the cause is content above it that arrived late (an image without a size, an injected banner, a late font)' });
  }
  return out;
}

// Observed live, not buffered: the buffered event-timing read drops entries under the default 104ms threshold.
function watchInput() {
  const u = { events: [], shifts: [], clickAt: [], clicked: [] };
  new PerformanceObserver((l) => u.events.push(...l.getEntries().filter((e) => e.interactionId))).observe({ type: 'event', durationThreshold: 16 });
  new PerformanceObserver((l) => u.shifts.push(...l.getEntries().filter((e) => !e.hadRecentInput))).observe({ type: 'layout-shift' });
  window.__uiInput = u;
}

// Runs inside the page after the clicks: per click, its slowest interaction split by phase, and the shifts Chrome counts after it.
function interactions() {
  const sel = window.__cssPath, u = window.__uiInput, out = [];
  // A click that navigated replaced the document, and its timings with it.
  if (!u) return { findings: [], slowest: null, navigated: true };
  const clicks = u.clicked;
  const groups = new Map();
  for (const e of u.events) {
    const g = groups.get(e.interactionId) ?? { start: Infinity, ps: Infinity, pe: 0, end: 0 };
    g.start = Math.min(g.start, e.startTime); g.ps = Math.min(g.ps, e.processingStart);
    g.pe = Math.max(g.pe, e.processingEnd); g.end = Math.max(g.end, e.startTime + e.duration);
    groups.set(e.interactionId, g);
  }
  const worst = clicks.map(() => null);
  for (const g of groups.values()) {
    const i = u.clickAt.findLastIndex((t) => t <= g.start);
    if (i < 0 || i >= clicks.length) continue;
    // Event durations are rounded to 8ms, so the presentation phase can come out a few ms negative.
    const ms = g.end - g.start, w = { ms, input: g.ps - g.start, processing: g.pe - g.ps, presentation: Math.max(0, g.end - g.pe) };
    if (!worst[i] || ms > worst[i].ms) worst[i] = w;
  }
  const target = (css) => {
    const el = document.querySelector(css), t = (el?.innerText || el?.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ');
    return { selector: el ? sel(el) : css, text: t ? `"${t.length > 40 ? t.slice(0, 40) + '…' : t}"` : '' };
  };
  const r = Math.round;
  clicks.forEach((css, i) => {
    const w = worst[i];
    if (w && w.ms > 200) {
      out.push({ check: w.ms > 500 ? 'inp-slow' : 'inp', ...target(css), review: false,
        detail: `${r(w.ms)}ms to the next paint after clicking ${css} (input delay ${r(w.input)}, processing ${r(w.processing)}, presentation ${r(w.presentation)});`
          + ' lab, unthrottled CPU; field good is ≤200ms at p75' });
    }
  });
  // Clicks are 100ms apart and Chrome ignores shifts within 500ms of any input, so a late shift can't be tied to one click.
  const moved = u.shifts.filter((s) => s.startTime >= (u.clickAt[0] ?? Infinity)), total = moved.reduce((n, s) => n + s.value, 0);
  if (total > 0.1) {
    const nodes = [...new Set(moved.flatMap((s) => s.sources ?? []).map((x) => (x.node?.nodeType === 1 ? x.node : x.node?.parentElement)).filter((n) => n?.isConnected))];
    out.push({ check: 'layout-shift-input', selector: nodes[0] ? sel(nodes[0]) : '', text: '', review: true,
      detail: `layout shift ${total.toFixed(2)} more than 500ms after clicking ${clicks.join(', ')}; something was inserted above it` });
  }
  const ms = worst.filter(Boolean).map((w) => w.ms);
  return { findings: out, slowest: ms.length ? r(Math.max(...ms)) : null };
}

// Installed before any page script: remembers elements that get a click-like listener, which no DOM property exposes.
function watchClicks() {
  const set = new WeakSet(), add = EventTarget.prototype.addEventListener;
  EventTarget.prototype.addEventListener = function (type, ...rest) {
    if (this instanceof Element && /^(click|mousedown|mouseup|pointerdown|pointerup)$/.test(type)) set.add(this);
    return add.call(this, type, ...rest);
  };
  Object.defineProperty(window, '__uiClickers', { value: set });
}

// Runs inside the page: navigation and paint timings, read field by field because PerformanceEntry getters don't survive JSON.
async function timings() {
  const nav = performance.getEntriesByType('navigation')[0];
  const fcp = performance.getEntriesByName('first-contentful-paint')[0];
  const read = (type) => new Promise((resolve) => {
    try { new PerformanceObserver((list, obs) => { obs.disconnect(); resolve(list.getEntries()); }).observe({ type, buffered: true }); } catch { resolve([]); }
    setTimeout(() => resolve([]), 300);
  });
  const [paints, tasks] = await Promise.all([read('largest-contentful-paint'), read('longtask')]);
  const lcp = paints.at(-1);
  const ms = (v) => (Number.isFinite(v) ? Math.round(v) : null);
  return { ttfb: ms(nav && nav.responseStart - nav.startTime), fcp: ms(fcp?.startTime), lcp: ms(lcp && (lcp.renderTime || lcp.loadTime || lcp.startTime)),
    longtasks: tasks.length, tbt: ms(tasks.reduce((n, t) => n + t.duration - 50, 0)) };
}

// Runs inside the page: same-origin links worth requesting, deduped without their fragment, each with the selector of its first anchor.
function collectLinks() {
  const skip = /log-?out|sign-?out|delete|destroy|remove|cancel|unsubscribe/i;
  const urls = new Map();
  for (const a of document.querySelectorAll('a[href]')) {
    const raw = a.getAttribute('href').trim();
    if (!raw || raw.startsWith('#') || /^(mailto|tel|sms|javascript|data|blob):/i.test(raw)) continue;
    let u;
    try { u = new URL(a.href); } catch { continue; }
    u.hash = '';
    if (u.origin !== location.origin || skip.test(u.pathname + u.search) || urls.has(u.href)) continue;
    urls.set(u.href, window.__cssPath(a));
  }
  return [...urls].map(([url, selector]) => ({ url, selector }));
}

// Runs inside the page, so requests carry the session's cookies. A redirect counts as fine: following it could reach another origin or a logout.
async function checkLinks(links) {
  const one = async (link) => {
    const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), 5000);
    const get = (method) => fetch(link.url, { method, redirect: 'manual', credentials: 'same-origin', cache: 'no-store', signal: ctl.signal });
    try {
      let r = await get('HEAD');
      if (r.status === 405 || r.status === 501) r = await get('GET');
      link.status = r.type === 'opaqueredirect' ? 300 : r.status;
    } catch (e) { link.error = ctl.signal.aborted ? 'timeout after 5s' : e.message; } finally { clearTimeout(timer); }
  };
  const queue = [...links];
  await Promise.all(Array.from({ length: 8 }, async () => { while (queue.length) await one(queue.shift()); }));
  return links;
}

// Runs inside the page. Fetched without cookies and without following redirects, as iOS fetches install assets; same-origin only.
async function installAssets() {
  const out = [];
  const add = (check, detail) => out.push({ check, selector: '', text: '', detail, review: false });
  const manifestLink = document.querySelector('link[rel~="manifest" i][href]');
  const capable = [...document.querySelectorAll('meta[name]')].filter((m) => m.name.toLowerCase() === 'apple-mobile-web-app-capable');
  if ((!manifestLink && !capable.length) || !/^https?:$/.test(location.protocol)) return out;
  const touch = [...document.querySelectorAll('link[rel~="apple-touch-icon" i]')], startup = [...document.querySelectorAll('link[rel~="apple-touch-startup-image" i]')];
  if (!touch.length) add('install-meta', 'no apple-touch-icon: iOS saves a page screenshot as the home-screen icon');
  if (startup.length && !capable.some((m) => m.content.trim().toLowerCase() === 'yes')) {
    add('install-meta', 'startup images without apple-mobile-web-app-capable=yes: iOS never shows them');
  }
  const urlOf = (href, base) => { try { const u = new URL(href, base); return u.origin === location.origin ? u : null; } catch { return null; } };
  const path = (u) => u.pathname + u.search;
  const get = async (u, body = true) => {
    const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), 5000);
    try {
      const r = await fetch(u, { credentials: 'omit', redirect: 'manual', cache: 'no-store', signal: ctl.signal });
      const type = (r.headers.get('content-type') ?? '').split(';')[0].trim().toLowerCase();
      const why = r.type === 'opaqueredirect' ? 'a redirect' : r.status >= 400 ? `HTTP ${r.status}` : type === 'text/html' ? 'an HTML page' : '';
      if (why) {
        add('install-asset', `${why} without cookies for ${path(u)}: iOS fetches install assets without cookies, so a sign-in redirect leaves a page screenshot as the icon`);
        return null;
      }
      if (!body) { r.body?.cancel(); return { type }; }
      return { type, blob: await r.blob() };
    } catch (e) {
      add('install-asset', `${ctl.signal.aborted ? 'timeout after 5s' : e.message} fetching ${path(u)} without cookies`);
      return null;
    } finally { clearTimeout(timer); }
  };
  const decode = async (blob) => {
    try {
      const bmp = await createImageBitmap(blob), c = new OffscreenCanvas(bmp.width, bmp.height), g = c.getContext('2d');
      g.drawImage(bmp, 0, 0);
      const px = g.getImageData(0, 0, bmp.width, bmp.height).data;
      let clear = false;
      for (let i = 3; i < px.length && !clear; i += 4) clear = px[i] < 255;
      return { w: bmp.width, h: bmp.height, clear };
    } catch { return null; }
  };
  const icons = [];
  let parsed = false;
  const manifestUrl = manifestLink && urlOf(manifestLink.getAttribute('href'), document.baseURI);
  if (manifestUrl) {
    const m = await get(manifestUrl);
    if (m) {
      try {
        const list = JSON.parse(await m.blob.text()).icons;
        parsed = true;
        for (const icon of Array.isArray(list) ? list : []) {
          if (typeof icon?.src !== 'string') continue;
          let u;
          try { u = new URL(icon.src, manifestUrl); } catch { continue; }
          icons.push({ u, same: u.origin === location.origin, sizes: String(icon.sizes ?? '').toLowerCase().split(/\s+/), purpose: String(icon.purpose ?? 'any').toLowerCase().split(/\s+/) });
        }
      } catch (e) { add('install-asset', `manifest ${path(manifestUrl)} doesn't parse (${e.message})`); }
    }
  }
  const touchUrls = [...new Set(touch.map((l) => urlOf(l.getAttribute('href') ?? '', document.baseURI)?.href).filter(Boolean))];
  const startupUrls = [...new Set(startup.map((l) => urlOf(l.getAttribute('href') ?? '', document.baseURI)?.href).filter(Boolean))];
  await Promise.all([
    ...touchUrls.map(async (h) => {
      const u = new URL(h), r = await get(u);
      if (!r) return;
      if (r.type !== 'image/png') add('install-icon', `apple-touch-icon ${path(u)} is ${r.type || 'untyped'}: iOS reads PNG icons only`);
      const d = await decode(r.blob);
      if (!d) return;
      if (d.w !== 180 || d.h !== 180) add('install-icon', `apple-touch-icon ${path(u)} is ${d.w}×${d.h}, iOS expects 180×180`);
      if (d.clear) add('install-icon', `apple-touch-icon ${path(u)} has transparent pixels: iOS composites them onto black`);
    }),
    ...startupUrls.map((h) => get(new URL(h), false)),
    ...icons.filter((i) => i.same && i.purpose.includes('any') && (i.sizes.includes('192x192') || i.sizes.includes('512x512'))).map(async (i) => { const r = await get(i.u); i.png = r?.type === 'image/png'; i.size = r && (await decode(r.blob)); }),
  ]);
  for (const n of [192, 512]) {
    // A cross-origin icon can't be checked here, so one that declares the size counts as present.
    const ok = icons.some((i) => i.purpose.includes('any') && i.sizes.includes(`${n}x${n}`) && (!i.same || (i.png && i.size?.w === n && i.size?.h === n)));
    if (parsed && !ok) add('install-icon', `manifest has no ${n}×${n} PNG icon with purpose any`);
  }
  for (const i of icons) if (i.purpose.includes('any') && i.purpose.includes('maskable')) add('install-icon', `${path(i.u)} serves any and maskable: one of the two crops or shrinks it`);
  return out;
}

// The hosts --links may send authenticated requests to: loopback, private IPv4 ranges, and single-label names such as docker services.
const privateHost = (hostname) => {
  const h = hostname.replace(/^\[|\]$/g, '').toLowerCase();
  if (h === 'localhost' || h.endsWith('.localhost') || h === '::1') return true;
  const v4 = /^(\d+)\.(\d+)\.\d+\.\d+$/.exec(h);
  if (v4) { const [a, b] = [Number(v4[1]), Number(v4[2])]; return a === 127 || a === 10 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168); }
  return !!h && !h.includes('.') && !h.includes(':');
};

// Runs inside the page before tabbing: remembers how each focusable element and its parent look unfocused.
function prepareFocus() {
  const PROPS = ['outlineStyle', 'outlineWidth', 'outlineColor', 'boxShadow', 'borderTopColor', 'borderBottomColor', 'borderBottomWidth',
    'backgroundColor', 'color', 'textDecorationLine', 'transform', 'left', 'top', 'clipPath', 'opacity'];
  const sig = (el) => {
    if (!el) return '';
    const s = getComputedStyle(el), a = getComputedStyle(el, '::after'), b = getComputedStyle(el, '::before');
    return PROPS.map((p) => s[p]).join('|') + [a, b].map((p) => `${p.content}|${p.boxShadow}|${p.outlineStyle}|${p.opacity}|${p.backgroundColor}`).join('|');
  };
  // Transitions would make the focused style read as its starting value.
  const style = document.createElement('style');
  style.textContent = '*, *::before, *::after { transition: none !important; animation: none !important; }';
  document.head.append(style);
  window.__uiCheck = { sig, before: new Map() };
  for (const el of document.querySelectorAll('*')) window.__uiCheck.before.set(el, sig(el) + '#' + sig(el.parentElement));
}

// Text over an image, gradient, or glass: glyph pixels are those that change when the text is hidden, each compared with the same pixel behind it.
const mediaContrast = async (i) => {
  const m = await evaluate(`(() => { const el = window.__uiMedia[${i}]; el.scrollIntoView({ block: 'center', behavior: 'instant' });
    const b = el.getBoundingClientRect(), s = getComputedStyle(el), t = el.innerText.trim().replace(/\\s+/g, ' '), x = Math.max(0, b.left), y = Math.max(0, b.top);
    const size = parseFloat(s.fontSize), weight = Number(s.fontWeight) || 400;
    return { selector: window.__cssPath(el), text: t ? '"' + (t.length > 40 ? t.slice(0, 40) + '…' : t) + '"' : '', min: size >= 24 || (size >= 18.66 && weight >= 700) ? 3 : 4.5,
      clip: { x: x + scrollX, y: y + scrollY, width: Math.min(innerWidth, b.right) - x, height: Math.min(innerHeight, b.bottom) - y, scale: 1 } }; })()`);
  const { clip, ...found } = m;
  if (!(clip.width >= 1 && clip.height >= 1)) return found;
  const shot = async () => decodePng((await send('Page.captureScreenshot', { format: 'png', clip })).data);
  const shown = await shot();
  await evaluate(`(() => { const el = window.__uiMedia[${i}]; window.__uiStyle = el.getAttribute('style');
    el.style.cssText += ';-webkit-text-fill-color: transparent !important; text-shadow: none !important; transition: none !important'; })()`);
  const bare = await shot();
  await evaluate(`(() => { const el = window.__uiMedia[${i}], s = window.__uiStyle; if (s === null) el.removeAttribute('style'); else el.setAttribute('style', s); })()`);
  if (!shown || !bare || shown.px.length !== bare.px.length) return found;
  const glyph = [];
  for (let p = 0; p < shown.px.length; p += shown.ch) {
    const fg = [...shown.px.subarray(p, p + 3)], bg = [...bare.px.subarray(p, p + 3)], diff = Math.max(...fg.map((v, k) => Math.abs(v - bg[k])));
    const [l1, l2] = [lum(fg), lum(bg)].sort((a, b) => b - a);
    if (diff >= 10) glyph.push({ diff, ratio: (l1 + 0.05) / (l2 + 0.05) });
  }
  // Antialiased edges blend into the backdrop and would pass for low contrast; only pixels at least half as changed as the strongest count.
  const peak = Math.max(0, ...glyph.map((g) => g.diff)), ratios = glyph.filter((g) => g.diff >= peak / 2).map((g) => g.ratio).sort((a, b) => a - b);
  if (ratios.length < 8) return found;
  return { ...found, pixels: ratios.length, ratio: Math.floor(ratios[Math.floor(ratios.length * 0.1)] * 100) / 100 };
};

const url = await resolveTarget(pos[0], opt.root);
if (opt.links && !privateHost(new URL(url).hostname)) {
  await fail(`--links runs only against a local or private host (localhost, 127/8, 10/8, 172.16/12, 192.168/16, a docker service name), not ${new URL(url).host}:`
    + ' every request carries the session\'s cookies');
}
// The base 40s includes 20s for the metadata re-read and install-asset fetches; clicks add their pauses and, under --perf, the 1s wait for late shifts.
const clickMs = opt.click.length ? widths.length * schemes.length * (opt.click.length * 100 + 1000) + 10000 : 0;
const cdp = await launch(40000 + widths.length * schemes.length * 45000 + samples * 30000 + (opt.links ? 150000 : 0) + clickMs);
const { send, evaluate, on } = cdp;
await send('Page.enable');
const mainFrame = (await send('Page.getFrameTree')).frameTree.frame.id;
await send('Runtime.enable');
await send('Network.enable');
await send('Page.addScriptToEvaluateOnNewDocument', { source: `(${watchClicks})()` });
await applyAuth(cdp, url, opt.cookie, opt.header);

let events = [];
let headerNoindex = false;
const urls = new Map();
const types = new Map();
let net = { requests: 0, js: 0, css: 0 };
on('Network.loadingFinished', (p) => {
  net.requests++;
  const t = types.get(p.requestId);
  if (t === 'Script') net.js += p.encodedDataLength; else if (t === 'Stylesheet') net.css += p.encodedDataLength;
});
on('Runtime.exceptionThrown', (p) => events.push({ check: 'js-error', detail: (p.exceptionDetails.exception?.description ?? p.exceptionDetails.text).split('\n')[0] }));
on('Runtime.consoleAPICalled', (p) => {
  if (p.type !== 'error' && p.type !== 'assert') return;
  events.push({ check: 'console', detail: p.args.map((a) => a.value ?? a.description ?? '').join(' ').split('\n')[0].slice(0, 200) });
});
on('Network.requestWillBeSent', (p) => urls.set(p.requestId, p.request.url));
on('Network.responseReceived', (p) => {
  types.set(p.requestId, p.type);
  // Only the top document: an iframe's own noindex says nothing about this page.
  if (p.type === 'Document' && p.frameId === mainFrame) {
    const h = Object.entries(p.response.headers ?? {}).find(([k]) => k.toLowerCase() === 'x-robots-tag')?.[1] ?? '';
    if (/\b(noindex|none)\b/i.test(h)) { headerNoindex = true; events.push({ check: 'noindex', detail: `X-Robots-Tag "${h}" on ${p.response.url}` }); }
  }
  if (p.response.status < 400) return;
  const favicon = /\/favicon\.ico(\?|$)/.test(p.response.url);
  const asset = ['Document', 'Stylesheet', 'Script', 'Font', 'Image'].includes(p.type);
  events.push({ check: favicon ? 'favicon' : asset ? 'request-asset' : 'request', detail: `HTTP ${p.response.status} ${p.type} ${p.response.url}` });
});
on('Network.loadingFailed', (p) => {
  net.requests++;
  if (!p.canceled) events.push({ check: 'request', detail: `${p.errorText} ${p.type} ${urls.get(p.requestId) ?? ''}`.trim() });
});

const focusWidth = [...widths].filter((w) => w < 1600).sort((a, b) => b - a)[0] ?? widths[0];
const found = new Map();
const seenIn = new Map();
const countLoad = () => { for (const d of new Set(events.filter((e) => MESSAGE_CHECKS.includes(e.check)).map((e) => e.detail))) seenIn.set(d, (seenIn.get(d) ?? 0) + 1); };
let linkReport = null;
let clickWorst = null;
const record = (f, where) => {
  const key = `${f.check}|${f.selector}|${f.selector ? '' : f.detail}`;
  const prev = found.get(key);
  if (prev) { if (!prev.where.includes(where)) prev.where.push(where); return; }
  found.set(key, { ...f, severity: SEVERITY[f.check], where: [where] });
};

for (const width of widths) for (const scheme of schemes) {
  const where = schemes.length > 1 ? `${width}/${scheme}` : String(width);
  events = [];
  await emulate(cdp, { width, height, scheme });
  await load(cdp, url);
  if (opt['wait-for']) await waitFor(cdp, opt['wait-for']);
  if (opt.eval) await evaluate(opt.eval);
  if (opt.click.length) {
    await evaluate(`(${watchInput})()`);
    for (const css of opt.click) {
      // A target hidden at this width (a desktop-only menu at 375) is skipped here, not fatal for the other widths.
      if (await evaluate(`(() => { const el = ${q(css)}; const b = el?.getBoundingClientRect(); return !!el && !(b.width > 0 && b.height > 0); })()`)) {
        if (!opt.json) console.log(`at ${where}: --click ${css} has no size here (hidden?), skipped`);
        continue;
      }
      await evaluate(`window.__uiInput.clickAt.push(performance.now()); window.__uiInput.clicked.push(${JSON.stringify(css)})`);
      const covered = await realClick(cdp, css);
      if (covered && !opt.json) console.log(`click ${css}: the pointer lands on ${covered}, which covers it`);
      await sleep(100);
    }
  }
  // A shift that lands after Chrome's 500ms input window must happen before it is read.
  await sleep(opt.perf && opt.click.length ? Math.max(wait, 1000) : wait);
  await evaluate(`window.__cssPath = ${cssPath}`);
  // Vitals first: the scroll in settle would add lazy-load shifts that aren't part of the load.
  for (const f of await evaluate(`(${vitals})(${JSON.stringify({ perf: opt.perf })})`)) record(f, where);
  if (opt.perf && opt.click.length) {
    const { findings, slowest, navigated } = await evaluate(`(${interactions})()`);
    if (navigated && !opt.json) console.log(`at ${where}: a click navigated away, so its timing couldn't be read`);
    for (const f of findings) record(f, where);
    if (slowest !== null && slowest > (clickWorst?.slowest ?? -1)) clickWorst = { slowest, width };
  }
  if (modes.has('text')) await evaluate(`(${stress})()`);
  if (modes.has('spacing')) await evaluate(`(${spacing})()`);
  await evaluate(`(${settle})()`);
  for (const f of await evaluate(`(${audit})(${JSON.stringify({ mobile: width < 700, phone: width <= 430, spacing: modes.has('spacing') })})`)) record(f, where);
  const first = width === widths[0] && scheme === schemes[0];
  if (first) for (const f of await evaluate(`(${metadata})(${JSON.stringify({ quiet: opt.cookie.length + opt.header.length > 0 || headerNoindex })})`)) record(f, 'page');
  // Each screenshot pair costs a round trip, so only the first 20 texts over media are measured.
  const media = await evaluate('window.__uiMedia.length');
  let unmeasured = 0;
  for (let i = 0; i < media; i++) {
    const m = i < 20 ? await mediaContrast(i) : await evaluate(`window.__cssPath(window.__uiMedia[${i}])`).then((selector) => ({ selector, text: '' }));
    const { selector, text } = m;
    if (m.ratio < m.min) record({ check: 'text-over-media-contrast', selector, text, review: true, detail: `${m.ratio.toFixed(2)}:1 at the 10th percentile of ${m.pixels} glyph pixels, needs ${m.min}:1` }, where);
    else if (m.ratio === undefined && unmeasured++ < 3) record({ check: 'contrast-unmeasured', selector, text, review: true, detail: 'text over an image, gradient, or glass; check it in the screenshot' }, where);
  }
  await evaluate("scrollTo({ top: 0, behavior: 'instant' })");
  for (const e of events) record({ ...e, selector: '', text: '', review: e.check === 'noindex' || (e.check === 'request' && / (Fetch|XHR) /.test(e.detail)) }, where);
  countLoad();
  // After the events are recorded, so a failing asset fetch lands once, as install-asset, not also as `request`.
  // --header is added to every same-origin request, so the cookie-less fetch iOS makes can't be reproduced.
  if (first && !opt.header.length) for (const f of await evaluate(`(${installAssets})()`)) record(f, 'install');
  // After the events are recorded, so the link requests' own failures land in the link findings, not in `request`.
  if (opt.links && !linkReport) {
    const landed = new URL(await evaluate('location.href'));
    if (landed.origin !== new URL(url).origin && !privateHost(landed.hostname)) await fail(`--links: the page redirected to ${landed.origin}, which is not a local or private host`);
    const all = await evaluate(`(${collectLinks})()`);
    const checked = await evaluate(`(${checkLinks})(${JSON.stringify(all.slice(0, 200))})`);
    const broken = checked.filter((l) => l.error || l.status >= 400);
    for (const l of broken) record({ check: 'broken-link', selector: l.selector, text: '', review: false, detail: `${l.error ? l.error : `HTTP ${l.status}`} ${l.url}` }, 'links');
    linkReport = { found: all.length, checked: checked.length, broken: broken.length };
  }
  if (opt.shot) {
    const [sh] = await evaluate('[document.documentElement.scrollHeight]');
    const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: opt.full,
      clip: { x: 0, y: 0, width, height: opt.full ? sh : height, scale: 1 } });
    const base = opt.shot.replace(/\.[^./\\]+$/, '');
    const file = base + (widths.length > 1 ? `-${width}` : '') + (schemes.length > 1 ? `-${scheme}` : '') + '.png';
    writeFileSync(file, Buffer.from(shot.data, 'base64'));
    if (!opt.json) console.log(`shot: ${file}`);
  }
  if (tabs && width === focusWidth && scheme === schemes[0]) {
    await evaluate(`(${prepareFocus})()`);
    const visited = new Set();
    for (let i = 0; i < tabs; i++) {
      for (const type of ['rawKeyDown', 'keyUp']) await send('Input.dispatchKeyEvent', { type, key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
      const r = await evaluate(`(() => { const el = document.activeElement, u = window.__uiCheck;
        if (!el || el === document.body || !u.before.has(el)) return null;
        const now = u.sig(el) + '#' + u.sig(el.parentElement);
        return { changed: now !== u.before.get(el), id: [...document.querySelectorAll('*')].indexOf(el) }; })()`);
      if (!r || visited.has(r.id)) break;
      visited.add(r.id);
      if (!r.changed) {
        const f = await evaluate(`(() => { const el = document.activeElement, t = (el.innerText || el.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ');
          return { selector: window.__cssPath(el), text: t ? '"' + t.slice(0, 40) + '"' : '' }; })()`);
        record({ check: 'focus', ...f, detail: 'no visible change on keyboard focus (outline, ring, border, or background)', review: false }, where);
      }
    }
  }
}

// Uncached loads at the focus-check width; each metric is the median of its samples.
let perf = null;
if (samples) {
  await send('Network.setCacheDisabled', { cacheDisabled: true });
  await emulate(cdp, { width: focusWidth, height, scheme: schemes[0] });
  const runs = [];
  for (let i = 0; i < samples; i++) {
    net = { requests: 0, js: 0, css: 0 };
    events = [];
    await load(cdp, url);
    if (opt['wait-for']) await waitFor(cdp, opt['wait-for']);
    await sleep(wait);
    runs.push({ ...(await evaluate(`(${timings})()`)), ...net });
    countLoad();
  }
  const median = (k) => { const v = runs.map((r) => r[k]).filter((x) => x !== null).sort((a, b) => a - b); return v.length ? v[(v.length - 1) >> 1] : null; };
  perf = { width: focusWidth, samples, metrics: Object.fromEntries(['ttfb', 'fcp', 'lcp', 'longtasks', 'tbt', 'js', 'css', 'requests'].map((k) => [k, median(k)])),
    ...(clickWorst && { clicks: clickWorst }) };
}
await cdp.close();

const messages = [...new Set([...found.values()].filter((f) => MESSAGE_CHECKS.includes(f.check)).map((f) => f.detail))];
let known = 0, once = 0;
if (baseline) {
  const old = new Set(baseline.messages ?? []);
  for (const [k, f] of found) {
    if (!MESSAGE_CHECKS.includes(f.check)) continue;
    if (old.has(f.detail)) { found.delete(k); known++; } else if ((seenIn.get(f.detail) ?? 0) < 2) { found.delete(k); once++; }
  }
  const b = baseline.metrics, m = perf.metrics;
  for (const k of ['ttfb', 'fcp', 'lcp']) {
    if (b[k] != null && m[k] != null && m[k] > b[k] * 1.5 && m[k] - b[k] > 500) {
      record({ check: 'perf-regression', selector: '', text: '', review: false, detail: `${k.toUpperCase()} ${b[k]}ms → ${m[k]}ms (median of ${samples})` }, String(focusWidth));
    }
  }
  // The 1 KB floor keeps a tiny asset that changes size from reading as a regression.
  for (const k of ['js', 'css']) {
    if (b[k] != null && m[k] > b[k] * 1.25 && m[k] - b[k] > 1024) {
      record({ check: 'perf-regression', selector: '', text: '', review: false, detail: `${k.toUpperCase()} ${kb(b[k])} → ${kb(m[k])} transferred (median of ${samples})` }, String(focusWidth));
    }
  }
}
if (opt.save) writeFileSync(opt.save, JSON.stringify({ url, width: focusWidth, scheme: schemes[0], samples, date: new Date().toISOString(), metrics: perf.metrics, messages }, null, 2) + '\n');

const findings = [...found.values()].sort((a, b) => a.severity - b.severity || a.check.localeCompare(b.check));
const allWhere = widths.length * schemes.length;
for (const f of findings) f.where = f.where.length === allWhere && allWhere > 1 ? ['all'] : f.where;
const failing = findings.some((f) => f.severity <= 2);
if (opt.json) {
  console.log(JSON.stringify({ url, widths, schemes, findings, ...(perf && { perf }), ...(linkReport && { links: linkReport }),
    ...(baseline && { baselineMessages: known, singleLoadMessages: once }) }, null, 2));
} else {
  console.log(`ui-check ${url}  widths ${widths.join(',')}  scheme ${schemes.join(',')}\n`);
  if (perf) {
    const m = perf.metrics, t = (v) => (v === null ? 'n/a' : `${v}ms`);
    console.log(`perf ${perf.width}: TTFB ${t(m.ttfb)} · FCP ${t(m.fcp)} · LCP ${t(m.lcp)} · ${m.longtasks ?? 'n/a'} long tasks, ${t(m.tbt)} blocking · JS ${kb(m.js)} · CSS ${kb(m.css)} · ${m.requests} requests`
      + `${clickWorst ? ` · slowest click ${clickWorst.slowest}ms` : ''}`
      + `${samples > 1 ? ` (median of ${samples} uncached loads` : ' (one uncached load'}, no CPU or network throttling)${opt.save ? `; saved to ${opt.save}` : ''}`);
    if (baseline) console.log(`compared with ${opt.compare}${baseline.url !== url ? ` (baseline was taken on ${baseline.url})` : ''}; ${known} console message(s) also in the baseline and ${once} new one(s) seen in only one load, not reported`);
  }
  if (linkReport) console.log(`links: ${linkReport.checked} checked${linkReport.found > linkReport.checked ? ` of ${linkReport.found}` : ''}, ${linkReport.broken} broken`);
  if (perf || linkReport) console.log('');
  const shown = new Map();
  for (const f of findings) {
    const n = (shown.get(f.check) ?? 0) + 1;
    shown.set(f.check, n);
    if (n === 9) console.log(`      ${f.check}: ${findings.filter((g) => g.check === f.check).length - 8} more (use --json)`);
    if (n > 8) continue;
    const who = [f.selector, f.text].filter(Boolean).join(' ');
    console.log(`P${f.severity}  ${f.check.padEnd(19)} ${f.where.join(',').padEnd(10)} ${who ? who + '  ' : ''}${f.detail}${f.review ? '  [review]' : ''}`);
  }
  const count = (s) => findings.filter((f) => f.severity === s).length;
  console.log(findings.length ? `\n${findings.length} finding(s): P1 ${count(1)}, P2 ${count(2)}, P3 ${count(3)}. [review] = heuristic, confirm in a screenshot before fixing.`
    : 'No measurable defects.');
  console.log('Not measured: visual hierarchy, spacing rhythm, hover states, copy, and whether the design fits the brief; look at the screenshots for those.');
}
process.exit(failing ? 1 : 0);
