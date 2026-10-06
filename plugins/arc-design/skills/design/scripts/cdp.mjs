// Shared headless Chrome session over the DevTools protocol, for screenshot.mjs and ui-check's ui_check.mjs.
// Importing it registers handlers that turn any uncaught error into `fail` (message on stderr, cleanup, exit 2).
import { spawn, execFileSync } from 'node:child_process';
import { createServer } from 'node:http';
import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync, statSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { dirname, extname, join, relative, resolve, sep } from 'node:path';

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let chrome, profile, server;

export const cleanup = async () => {
  server?.close();
  if (chrome && chrome.exitCode === null && chrome.signalCode === null) {
    const exited = new Promise((r) => chrome.once('exit', r));
    chrome.kill();
    await Promise.race([exited, sleep(3000)]);
    if (chrome.exitCode === null && chrome.signalCode === null) chrome.kill('SIGKILL');
  }
  if (profile) try { rmSync(profile, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 }); } catch {}
};
export const fail = async (msg) => { console.error(msg); await cleanup(); process.exit(2); };
process.on('uncaughtException', (e) => fail(e?.message ?? String(e)));
process.on('unhandledRejection', (e) => fail(e?.message ?? String(e)));

// Parses `--key value`, `--key=value`, and boolean flags into `defaults`; returns the positional arguments. An array default collects repeats.
export const parseArgs = async (argv, defaults, flags, usage) => {
  const pos = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) { pos.push(a); continue; }
    let [k, v] = a.slice(2).split(/=(.*)/s);
    if (flags.includes(k)) { defaults[k] = true; continue; }
    if (!Object.hasOwn(defaults, k)) await fail(`unknown option ${a}\n${usage}`);
    if (v === undefined) { v = argv[++i]; if (v === undefined) await fail(`missing value for ${a}`); }
    if (Array.isArray(defaults[k])) defaults[k].push(v); else defaults[k] = v;
  }
  return pos;
};

const HOST_PORT = /^(\[[0-9a-f:.]+\]|[a-z0-9]([\w-]*[a-z0-9])?(\.[a-z0-9]([\w-]*[a-z0-9])?)*):\d{1,5}([/?#]|$)/i;

// A URL stays as is, `host:port[/path]` becomes http; a local file is served from `root` (default: its directory), so root-relative assets load.
export const resolveTarget = async (target, root) => {
  if (/^(localhost|127\.0\.0\.1|\[::1\])([/?#]|$)/i.test(target)) return `http://${target}`;
  if (HOST_PORT.test(target) && !existsSync(resolve(target))) return `http://${target}`;
  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(target) || /^(data|about|blob|javascript):/i.test(target)) return target;
  const file = resolve(target);
  if (!existsSync(file)) await fail(`no such file: ${target}`);
  const base = resolve(root || (statSync(file).isDirectory() ? file : dirname(file)));
  const rel = relative(base, file);
  if (rel.startsWith('..')) await fail(`${target} is outside --root ${base}`);
  const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
    '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.avif': 'image/avif',
    '.gif': 'image/gif', '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf' };
  server = createServer((req, res) => {
    try {
      let p = join(base, decodeURIComponent(new URL(req.url, 'http://x').pathname));
      if (p !== base && !p.startsWith(base + sep)) { res.writeHead(403).end(); return; }
      if (statSync(p).isDirectory()) p = join(p, 'index.html');
      const body = readFileSync(p);
      res.writeHead(200, { 'content-type': types[extname(p).toLowerCase()] ?? 'application/octet-stream' }).end(body);
    } catch { res.writeHead(404).end(); }
  });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  return `http://127.0.0.1:${server.address().port}/${rel.split(sep).map(encodeURIComponent).join('/')}`;
};

const findChrome = () => {
  const candidates = [process.env.CHROME,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'].filter(Boolean);
  for (const c of candidates) if (existsSync(c)) return c;
  for (const name of ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'microsoft-edge']) {
    try { return execFileSync('which', [name], { encoding: 'utf8' }).trim(); } catch {}
  }
  return findPlaywrightChromium();
};

// CI runners and containers often have only the Chromium that `npx playwright install` downloaded, which is never on PATH.
const findPlaywrightChromium = () => {
  const caches = [process.env.PLAYWRIGHT_BROWSERS_PATH, join(homedir(), '.cache', 'ms-playwright'),
    join(homedir(), 'Library', 'Caches', 'ms-playwright'), process.env.LOCALAPPDATA && join(process.env.LOCALAPPDATA, 'ms-playwright')].filter(Boolean);
  const bins = [['chrome-linux64', 'chrome'], ['chrome-linux', 'chrome'], ['chrome-mac-arm64', 'Chromium.app', 'Contents', 'MacOS', 'Chromium'],
    ['chrome-mac', 'Chromium.app', 'Contents', 'MacOS', 'Chromium'], ['chrome-win64', 'chrome.exe'], ['chrome-win', 'chrome.exe']];
  for (const cache of caches) {
    let dirs;
    try { dirs = readdirSync(cache).filter((d) => /^chromium-\d+$/.test(d)); } catch { continue; }
    dirs.sort((a, b) => Number(b.slice(9)) - Number(a.slice(9)));
    for (const d of dirs) for (const bin of bins) {
      const p = join(cache, d, ...bin);
      if (existsSync(p)) return p;
    }
  }
  return null;
};

// Starts Chrome and returns { send, once, on, evaluate, close } for its first page. Exits 2 after `timeoutMs`.
export const launch = async (timeoutMs) => {
  if (typeof WebSocket === 'undefined') await fail('needs Node 22+ (global WebSocket)');
  const chromePath = findChrome();
  if (!chromePath) await fail('no Chrome, Chromium, or Edge found on PATH or in the Playwright cache; set CHROME=/path/to/chrome');
  setTimeout(() => fail('timed out'), timeoutMs).unref();
  profile = mkdtempSync(join(tmpdir(), 'shot-'));
  // Port 0 lets Chrome pick a free port and write it to DevToolsActivePort, so parallel runs never share a browser.
  const args = ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run', '--remote-debugging-port=0', `--user-data-dir=${profile}`];
  // Chrome refuses to start as root (the usual container user) unless its sandbox is off.
  if (process.getuid?.() === 0) args.push('--no-sandbox');
  chrome = spawn(chromePath, [...args, 'about:blank'], { stdio: 'ignore' });
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
  const listeners = [];
  ws.addEventListener('message', (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) {
      const { resolve, reject } = pending.get(m.id);
      pending.delete(m.id);
      if (m.error) reject(new Error(`${m.error.message} (${m.error.data ?? 'CDP'})`)); else resolve(m.result);
    } else if (m.method) {
      for (const w of waiters.filter((w) => w.method === m.method)) { waiters.splice(waiters.indexOf(w), 1); w.resolve(); }
      for (const l of listeners) if (l.method === m.method) l.fn(m.params);
    }
  });
  ws.addEventListener('close', () => { for (const { reject } of pending.values()) reject(new Error('Chrome closed the connection')); pending.clear(); });
  const send = (method, params = {}) => new Promise((resolve, reject) => { const id = ++seq; pending.set(id, { resolve, reject }); ws.send(JSON.stringify({ id, method, params })); });
  const once = (method, ms) => new Promise((resolve) => {
    const w = { method, resolve };
    waiters.push(w);
    setTimeout(() => { const i = waiters.indexOf(w); if (i >= 0) { waiters.splice(i, 1); resolve(); } }, ms);
  });
  const on = (method, fn) => listeners.push({ method, fn });
  const evaluate = async (expression) => {
    const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(`eval failed: ${r.exceptionDetails.exception?.description ?? r.exceptionDetails.text}`);
    return r.result?.value;
  };
  const close = async () => { ws.close(); await cleanup(); };
  return { send, once, on, evaluate, close };
};

// `--cookie name=value` (repeatable or comma list), `--header "Name: value"` (repeatable), both for the target's origin only. Call before `load`.
export const applyAuth = async ({ send, on }, url, cookies = [], headers = []) => {
  const list = cookies.flatMap((c) => c.split(/,(?=\s*[^\s=,;]+=)/)).map((c) => c.trim()).filter(Boolean);
  for (const [n, c] of list.entries()) {
    const i = c.indexOf('=');
    if (i < 1) await fail(`--cookie #${n + 1} takes name=value (value not shown)`);
    const { success } = await send('Network.setCookie', { name: c.slice(0, i).trim(), value: c.slice(i + 1).trim(), url, path: '/' })
      .catch(() => fail('Chrome could not set --cookie'));
    if (success === false) await fail('Chrome rejected --cookie');
  }
  const extra = [];
  for (const [n, h] of headers.entries()) {
    const m = /^\s*([!#$%&'*+.^_`|~0-9A-Za-z-]+)\s*:\s*([^\r\n]*)$/.exec(h);
    if (!m) await fail(`--header #${n + 1} takes "Name: value" on one line (value not shown)`);
    if (/^(host|content-length|connection|transfer-encoding|upgrade|keep-alive|te|trailer)$/i.test(m[1])) await fail(`--header cannot set ${m[1]}`);
    extra.push({ name: m[1], value: m[2].trim() });
  }
  if (!extra.length) return;
  const { origin } = new URL(url);
  // Network.setExtraHTTPHeaders would also send them to third-party hosts, so only requests to the target's origin are rewritten.
  const names = new Set(extra.map((h) => h.name.toLowerCase()));
  // Every paused request must be continued, or the page hangs until the global timeout.
  on('Fetch.requestPaused', ({ requestId, request }) => {
    const kept = Object.entries(request.headers).filter(([n]) => !names.has(n.toLowerCase())).map(([name, value]) => ({ name, value }));
    send('Fetch.continueRequest', { requestId, headers: [...kept, ...extra] })
      .catch(() => { console.error('--header rejected by Chrome; request sent without it'); return send('Fetch.continueRequest', { requestId }); })
      .catch(() => {});
  });
  await send('Fetch.enable', { patterns: [{ urlPattern: `${origin}/*` }] });
};

// Loads `url` and waits for the load event (15s cap), fonts (3s cap), and an HTTP status below 400.
export const load = async ({ send, once, evaluate }, url) => {
  const loaded = once('Page.loadEventFired', 15000);
  const nav = await send('Page.navigate', { url });
  if (nav.errorText) await fail(`navigation failed: ${nav.errorText} (${url})`);
  await loaded;
  const status = await evaluate("performance.getEntriesByType('navigation')[0]?.responseStatus ?? 0");
  if (status >= 400) await fail(`HTTP ${status} for ${url}`);
  await Promise.race([evaluate('document.fonts.ready.then(() => true)'), sleep(3000)]);
};

// Polls for an element that exists and has a size; exits 2 after 10s.
export const waitFor = async ({ evaluate }, css) => {
  const found = await evaluate(`new Promise((r) => { const t0 = Date.now(); const tick = () => { const el = document.querySelector(${JSON.stringify(css)});
    if (el && el.getBoundingClientRect().width > 0) r(true); else if (Date.now() - t0 > 10000) r(false); else setTimeout(tick, 100); }; tick(); })`);
  if (!found) await fail(`--wait-for: ${css} did not appear within 10s`);
};

export const MEDIA = { 'reduced-motion': ['prefers-reduced-motion', 'reduce'], 'contrast-more': ['prefers-contrast', 'more'],
  'reduced-transparency': ['prefers-reduced-transparency', 'reduce'], 'forced-colors': ['forced-colors', 'active'] };

// Width under 700 emulates a phone. The scheme is always set: headless Chrome otherwise follows the OS theme.
export const emulate = async ({ send }, { width, height, scheme, media = [] }) => {
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: width < 700 });
  const features = media.map((m) => ({ name: MEDIA[m][0], value: MEDIA[m][1] }));
  features.push({ name: 'prefers-color-scheme', value: scheme });
  await send('Emulation.setEmulatedMedia', { features });
};
