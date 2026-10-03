#!/usr/bin/env node
// Measure rendering defects on a live page in headless Chrome: what overflows, clips, overlaps, fails contrast, loses focus, or errors.
// Usage: node ui_check.mjs <url|file> [--width 375,768,1280,1920] [--height 900] [--scheme light|dark|light,dark] [--wait-for css]
//          [--eval "js"] [--wait 500] [--root dir] [--tabs 40] [--shot out.png] [--full] [--perf] [--json]
//   --tabs   how many Tab presses the focus check walks (0 skips it); it runs once, at the widest width under 1600.
//   --shot   also write a screenshot per width and scheme (out-<width>[-<scheme>].png), taken before the focus check; --full for the whole page.
//   --perf   also report the largest-contentful-paint element and the elements that shift during load (lab values).
//   --json   print the findings as JSON instead of text.
//   Other options work as in design/scripts/screenshot.mjs.
// Findings are P1 (breaks use or access), P2 (degrades it), P3 (minor); [review] marks heuristics to confirm in a screenshot.
// Exit 0 nothing at P1 or P2, 1 findings at P1 or P2, 2 the check couldn't run (usage, no Chrome, Node < 22, navigation or HTTP error, timeout).
import { writeFileSync } from 'node:fs';
import { emulate, fail, launch, load, parseArgs, resolveTarget, sleep, waitFor } from '../../design/scripts/cdp.mjs';

const USAGE = 'Usage: node ui_check.mjs <url|file> [--width 375,768,1280,1920] [--height 900] [--scheme light|dark|light,dark] [--wait-for css]'
  + ' [--eval "js"] [--wait 500] [--root dir] [--tabs 40] [--shot out.png] [--full] [--perf] [--json]';
const opt = { width: '375,768,1280,1920', height: '900', scheme: 'light', 'wait-for': '', eval: '', wait: '500', root: '', tabs: '40',
  shot: '', full: false, perf: false, json: false };
const pos = await parseArgs(process.argv.slice(2), opt, ['full', 'perf', 'json'], USAGE);
if (pos.length !== 1) await fail(USAGE);
const widths = [...new Set(opt.width.split(',').map(Number))];
const height = Number(opt.height), wait = Number(opt.wait), tabs = Number(opt.tabs);
if (widths.some((w) => !(w > 0)) || !(height > 0) || !(wait >= 0) || !(tabs >= 0)) await fail('--width, --height, --wait, and --tabs take numbers');
const schemes = [...new Set(opt.scheme.split(','))];
if (schemes.some((c) => c !== 'light' && c !== 'dark')) await fail('--scheme takes light, dark, or light,dark');

const SEVERITY = { overflow: 1, contrast: 1, focus: 1, name: 1, 'broken-image': 1, 'js-error': 1, 'request-asset': 1,
  clipped: 2, overlap: 2, target: 2, distorted: 2, 'placeholder-label': 2, console: 2, request: 2, lang: 2, 'zoom-blocked': 2, 'lcp-lazy': 2,
  'layout-shift': 2, 'target-touch': 3, favicon: 3, alt: 3, heading: 3, viewport: 3, 'contrast-unmeasured': 3, lcp: 3 };

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
function audit({ mobile }) {
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
  if (unmeasured.length) {
    for (const el of unmeasured.slice(0, 3)) add('contrast-unmeasured', el, 'text over an image, gradient, or glass; check it in the screenshot', true);
  }

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
    const small = Math.min(r.width, r.height);
    if (small < 24) add('target', el, `${Math.round(r.width)}×${Math.round(r.height)}px, under the 24px minimum`);
    else if (mobile && small < 44) touch.push({ el, small, size: `${Math.round(r.width)}×${Math.round(r.height)}px` });
  }
  // The script can't tell primary controls from secondary ones, so one line lists the smallest and the shot decides which are primary.
  if (touch.length) {
    touch.sort((a, b) => a.small - b.small);
    const rest = touch.slice(1, 3).map((t) => `${sel(t.el)} ${t.size}`).join(', ');
    add('target-touch', touch[0].el, `${touch.length} control(s) under 44px on a phone width, smallest ${touch[0].size}`
      + (rest ? `; next: ${rest}` : '') + '; only primary controls need 44px', true);
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
  if (mobile && !document.querySelector('meta[name=viewport]')) add('viewport', null, 'no <meta name=viewport>: phones lay this page out at 980px');
  if (!document.documentElement.getAttribute('lang')?.trim()) add('lang', null, 'no lang on <html>: screen readers and translation guess the language');
  const vp = document.querySelector('meta[name=viewport]')?.getAttribute('content') ?? '';
  const maxScale = /maximum-scale\s*=\s*([\d.]+)/i.exec(vp);
  if ((maxScale && Number(maxScale[1]) < 2) || /user-scalable\s*=\s*(no|0)\b/i.test(vp)) add('zoom-blocked', null, `viewport "${vp}" blocks pinch zoom`);
  return out;
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
  const moved = shifts.filter((s) => !s.hadRecentInput);
  const total = moved.reduce((n, s) => n + s.value, 0);
  if (total > 0.1) {
    const nodes = [...new Set(moved.flatMap((s) => s.sources ?? []).map((x) => (x.node?.nodeType === 1 ? x.node : x.node?.parentElement)).filter((n) => n?.isConnected))];
    out.push({ check: 'layout-shift', selector: nodes[0] ? sel(nodes[0]) : '', text: '', review: true,
      detail: `layout shift ${total.toFixed(2)} during load, over 0.1; this moved` + (nodes.length > 1 ? ` with ${nodes.slice(1, 4).map(sel).join(', ')}` : '')
        + '; the cause is content above it that arrived late (an image without a size, an injected banner, a late font)' });
  }
  return out;
}

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

const cdp = await launch(20000 + widths.length * schemes.length * 45000);
const { send, evaluate, on } = cdp;
await send('Page.enable');
await send('Runtime.enable');
await send('Network.enable');

let events = [];
const urls = new Map();
on('Runtime.exceptionThrown', (p) => events.push({ check: 'js-error', detail: (p.exceptionDetails.exception?.description ?? p.exceptionDetails.text).split('\n')[0] }));
on('Runtime.consoleAPICalled', (p) => {
  if (p.type !== 'error' && p.type !== 'assert') return;
  events.push({ check: 'console', detail: p.args.map((a) => a.value ?? a.description ?? '').join(' ').split('\n')[0].slice(0, 200) });
});
on('Network.requestWillBeSent', (p) => urls.set(p.requestId, p.request.url));
on('Network.responseReceived', (p) => {
  if (p.response.status < 400) return;
  const favicon = /\/favicon\.ico(\?|$)/.test(p.response.url);
  const asset = ['Document', 'Stylesheet', 'Script', 'Font', 'Image'].includes(p.type);
  events.push({ check: favicon ? 'favicon' : asset ? 'request-asset' : 'request', detail: `HTTP ${p.response.status} ${p.type} ${p.response.url}` });
});
on('Network.loadingFailed', (p) => {
  if (!p.canceled) events.push({ check: 'request', detail: `${p.errorText} ${p.type} ${urls.get(p.requestId) ?? ''}`.trim() });
});

const url = await resolveTarget(pos[0], opt.root);
const focusWidth = [...widths].filter((w) => w < 1600).sort((a, b) => b - a)[0] ?? widths[0];
const found = new Map();
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
  await sleep(wait);
  await evaluate(`window.__cssPath = ${cssPath}`);
  for (const f of await evaluate(`(${audit})(${JSON.stringify({ mobile: width < 700 })})`)) record(f, where);
  for (const f of await evaluate(`(${vitals})(${JSON.stringify({ perf: opt.perf })})`)) record(f, where);
  for (const e of events) record({ ...e, selector: '', text: '', review: e.check === 'request' && / (Fetch|XHR) /.test(e.detail) }, where);
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
await cdp.close();

const findings = [...found.values()].sort((a, b) => a.severity - b.severity || a.check.localeCompare(b.check));
const allWhere = widths.length * schemes.length;
for (const f of findings) f.where = f.where.length === allWhere && allWhere > 1 ? ['all'] : f.where;
const failing = findings.some((f) => f.severity <= 2);
if (opt.json) {
  console.log(JSON.stringify({ url, widths, schemes, findings }, null, 2));
} else {
  console.log(`ui-check ${url}  widths ${widths.join(',')}  scheme ${schemes.join(',')}\n`);
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
