#!/usr/bin/env node
// Screenshot a page in headless Chrome over the DevTools protocol, at any width (the --screenshot flag clamps windows to ~500px).
// Usage: node screenshot.mjs <url|file> <out.png> [--width 1280,390] [--height 900] [--full] [--eval "js"] [--wait 500] [--root dir]
//   --width   one or more comma-separated widths; widths under 700 emulate a mobile device. With several widths, files are named out-<width>.png.
//   --full    capture the whole page instead of one viewport.
//   --eval    JS run after load, before the shot (reveal a step, add `.visible` to scroll-in content, stub fetch). Awaited if it returns a promise.
//   --wait    extra ms after load and fonts (default 500).
//   --root    a local file is served over http from this directory (default: the file's directory), so root-relative assets (href="/style.css") load.
// Prints one line per width: file, page size, and "overflow" when the page is wider than the viewport.
// Exit 0 ok, 1 shots written but some width overflows horizontally, 2 no shot (usage, no Chrome, Node < 22, navigation or HTTP error, eval error, timeout).
import { spawn, execFileSync } from 'node:child_process';
import { createServer } from 'node:http';
import { existsSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, extname, join, relative, resolve, sep } from 'node:path';

const USAGE = 'Usage: node screenshot.mjs <url|file> <out.png> [--width 1280,390] [--height 900] [--full] [--eval "js"] [--wait 500] [--root dir]';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let chrome, profile, server;
const cleanup = async () => {
  server?.close();
  if (chrome && chrome.exitCode === null && chrome.signalCode === null) {
    const exited = new Promise((r) => chrome.once('exit', r));
    chrome.kill();
    await Promise.race([exited, sleep(3000)]);
    if (chrome.exitCode === null && chrome.signalCode === null) chrome.kill('SIGKILL');
  }
  if (profile) try { rmSync(profile, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 }); } catch {}
};
const fail = async (msg) => { console.error(msg); await cleanup(); process.exit(2); };
process.on('uncaughtException', (e) => fail(e?.message ?? String(e)));
process.on('unhandledRejection', (e) => fail(e?.message ?? String(e)));

const args = process.argv.slice(2);
const opt = { width: '1280', height: '900', wait: '500', eval: '', root: '', full: false };
const pos = [];
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === '--full') { opt.full = true; continue; }
  if (!a.startsWith('--')) { pos.push(a); continue; }
  let [k, v] = a.slice(2).split(/=(.*)/s);
  if (!Object.hasOwn(opt, k) || k === 'full') await fail(`unknown option ${a}\n${USAGE}`);
  if (v === undefined) { v = args[++i]; if (v === undefined) await fail(`missing value for ${a}`); }
  opt[k] = v;
}
if (pos.length !== 2) await fail(USAGE);
if (typeof WebSocket === 'undefined') await fail('needs Node 22+ (global WebSocket)');
const widths = [...new Set(opt.width.split(',').map(Number))];
const height = Number(opt.height);
const wait = Number(opt.wait);
if (widths.some((w) => !(w > 0)) || !(height > 0) || !(wait >= 0)) await fail('--width and --height take positive numbers, --wait a number of ms');

let [target, out] = pos;
if (/^(localhost|127\.0\.0\.1|\[::1\])(:\d+)?(\/|$)/i.test(target)) target = `http://${target}`;
else if (!/^[a-z][a-z0-9+.-]*:/i.test(target)) {
  // Serve local files over http so root-relative assets resolve, which file:// can't do.
  const file = resolve(target);
  if (!existsSync(file)) await fail(`no such file: ${target}`);
  const root = resolve(opt.root || (statSync(file).isDirectory() ? file : dirname(file)));
  const rel = relative(root, file);
  if (rel.startsWith('..')) await fail(`${target} is outside --root ${root}`);
  const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
    '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.avif': 'image/avif',
    '.gif': 'image/gif', '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf' };
  server = createServer((req, res) => {
    try {
      let p = join(root, decodeURIComponent(new URL(req.url, 'http://x').pathname));
      if (p !== root && !p.startsWith(root + sep)) { res.writeHead(403).end(); return; }
      if (statSync(p).isDirectory()) p = join(p, 'index.html');
      const body = readFileSync(p);
      res.writeHead(200, { 'content-type': types[extname(p).toLowerCase()] ?? 'application/octet-stream' }).end(body);
    } catch { res.writeHead(404).end(); }
  });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  target = `http://127.0.0.1:${server.address().port}/${rel.split(sep).map(encodeURIComponent).join('/')}`;
}

const findChrome = () => {
  const candidates = [process.env.CHROME,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'].filter(Boolean);
  for (const c of candidates) if (existsSync(c)) return c;
  for (const name of ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'microsoft-edge']) {
    try { return execFileSync('which', [name], { encoding: 'utf8' }).trim(); } catch {}
  }
  return null;
};
const chromePath = findChrome();
if (!chromePath) await fail('no Chrome, Chromium, or Edge found; set CHROME=/path/to/chrome');

setTimeout(() => fail('timed out'), 20000 + widths.length * 20000).unref();
profile = mkdtempSync(join(tmpdir(), 'shot-'));
// Port 0 lets Chrome pick a free port and write it to DevToolsActivePort, so parallel runs never share a browser.
chrome = spawn(chromePath, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
  '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
chrome.on('error', (e) => fail(`cannot start ${chromePath}: ${e.message}`));

let page;
for (let i = 0; i < 50 && !page && chrome.exitCode === null; i++) {
  try {
    const port = readFileSync(join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim();
    page = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find((t) => t.type === 'page');
  } catch {}
  if (!page) await sleep(200);
}
if (!page) await fail('Chrome did not start');

const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r); ws.addEventListener('error', () => j(new Error('cannot connect to Chrome'))); });
let seq = 0;
const pending = new Map();
const waiters = [];
ws.addEventListener('message', (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) {
    const { resolve, reject } = pending.get(m.id);
    pending.delete(m.id);
    if (m.error) reject(new Error(`${m.error.message} (${m.error.data ?? 'CDP'})`)); else resolve(m.result);
  } else if (m.method) for (const w of waiters.filter((w) => w.method === m.method)) { waiters.splice(waiters.indexOf(w), 1); w.resolve(); }
});
ws.addEventListener('close', () => { for (const { reject } of pending.values()) reject(new Error('Chrome closed the connection')); pending.clear(); });
const send = (method, params = {}) => new Promise((resolve, reject) => { const id = ++seq; pending.set(id, { resolve, reject }); ws.send(JSON.stringify({ id, method, params })); });
const once = (method, ms) => new Promise((resolve) => {
  const w = { method, resolve };
  waiters.push(w);
  setTimeout(() => { const i = waiters.indexOf(w); if (i >= 0) { waiters.splice(i, 1); resolve(); } }, ms);
});
const evaluate = async (expression) => {
  const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(`eval failed: ${r.exceptionDetails.exception?.description ?? r.exceptionDetails.text}`);
  return r.result?.value;
};

await send('Page.enable');
let overflow = false;
for (const width of widths) {
  const mobile = width < 700;
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile });
  // A page with a resource that never finishes gets its shot anyway after 15s; fonts get 3s on top.
  const loaded = once('Page.loadEventFired', 15000);
  const nav = await send('Page.navigate', { url: target });
  if (nav.errorText) await fail(`navigation failed: ${nav.errorText} (${target})`);
  await loaded;
  const status = await evaluate("performance.getEntriesByType('navigation')[0]?.responseStatus ?? 0");
  if (status >= 400) await fail(`HTTP ${status} for ${target}`);
  await Promise.race([evaluate('document.fonts.ready.then(() => true)'), sleep(3000)]);
  if (opt.eval) {
    const v = await evaluate(opt.eval);
    if (v !== undefined) console.log(`eval: ${JSON.stringify(v)}`);
  }
  await sleep(wait);
  const [sw, sh, hasViewport] = await evaluate("[document.documentElement.scrollWidth, document.documentElement.scrollHeight, !!document.querySelector('meta[name=viewport]')]");
  const clip = { x: 0, y: 0, width, height: opt.full ? sh : height, scale: 1 };
  const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: opt.full, clip });
  const base = out.replace(/\.[^./\\]+$/, '');
  const file = widths.length > 1 ? `${base}-${width}.png` : `${base}.png`;
  writeFileSync(file, Buffer.from(shot.data, 'base64'));
  const wide = sw > width;
  overflow ||= wide;
  const note = mobile && !hasViewport ? '  no <meta name=viewport>: phones lay this page out at 980px' : '';
  console.log(`${file}  ${width}x${clip.height}  page ${sw}x${sh}${wide ? `  overflow: ${sw - width}px wider than viewport` : ''}${note}`);
}
ws.close();
await cleanup();
process.exit(overflow ? 1 : 0);
