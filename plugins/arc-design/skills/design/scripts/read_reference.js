// Reads a reference site's design system in one pass: node screenshot.mjs <url> out.png --eval "$(cat read_reference.js)".
// An expression, not a module: screenshot.mjs prints the --eval value as JSON, and a bare arrow function would print {}.
(() => {
  const bump = (m, k, n = 1) => m.set(k, (m.get(k) ?? 0) + n);
  const top = (m, n) => [...m].sort((a, b) => b[1] - a[1]).slice(0, n);
  const median = (a) => { if (!a.length) return null; const s = [...a].sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
  const round = (v) => Math.round(v * 100) / 100;
  const names = new Set(), used = new Set(), queries = new Set(), unreadable = [];
  const bp = /\((?:min|max)-width:\s*[\d.]+(?:px|r?em)\)|\(width\s*[<>]=?\s*[\d.]+(?:px|r?em)\)/g;
  // Tailwind v4 declares its tokens inside @layer theme and imports nest sheets, so every grouping rule is walked.
  const walk = (rules) => { for (const r of rules ?? []) {
    if (r.style) for (const p of r.style) if (p.startsWith('--')) names.add(p);
    for (const m of (r.style?.cssText ?? '').matchAll(/var\((--[\w-]+)/g)) used.add(m[1]);
    for (const m of (r.media?.mediaText ?? '').matchAll(bp)) queries.add(m[0]);
    if (r.styleSheet) { try { walk(r.styleSheet.cssRules); } catch { unreadable.push(r.styleSheet.href); } }
    if (r.cssRules) walk(r.cssRules);
  } };
  // A cross-origin sheet throws on cssRules; listing it keeps a silent gap from passing as the whole system.
  for (const s of document.styleSheets) { try { walk(s.cssRules); } catch { unreadable.push(s.href); } }
  const html = document.documentElement, cs = getComputedStyle(html);
  const tokens = Object.fromEntries([...names].filter((n) => used.has(n)).sort().map((n) => [n, cs.getPropertyValue(n).trim()]).filter(([, v]) => v));

  const rows = new Map(), sizes = new Map(), space = new Map(), radius = new Map(), shadow = new Map(), motion = new Map();
  const ownsText = (el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
  for (const el of document.body.querySelectorAll('*')) {
    if (!el.getClientRects().length) continue;
    const s = getComputedStyle(el);
    // Only elements that own text, so a wrapper's inherited size doesn't count as a step.
    if (ownsText(el) && !el.closest('pre, code, kbd, samp, svg')) {
      const chars = [...el.childNodes].reduce((n, c) => n + (c.nodeType === 3 ? c.textContent.trim().length : 0), 0);
      bump(rows, `${s.fontSize} w${s.fontWeight} lh ${s.lineHeight} ls ${s.letterSpacing} ${s.fontFamily.split(',')[0].replace(/["']/g, '')}`);
      bump(sizes, parseFloat(s.fontSize), chars);
    }
    for (const p of ['paddingTop', 'paddingLeft', 'marginTop', 'marginBottom', 'rowGap', 'columnGap']) { const v = parseFloat(s[p]); if (v > 0) bump(space, round(v)); }
    // Pills compute to a huge px value (9999px, calc(infinity)); naming them keeps them out of the size steps.
    if (s.borderRadius !== '0px') bump(radius, parseFloat(s.borderRadius) >= 999 ? 'pill' : s.borderRadius);
    // Tailwind pads every shadow with transparent zero layers; dropping them lets equal shadows group.
    const sh = s.boxShadow.replace(/rgba\(0, 0, 0, 0\) 0px 0px 0px 0px(, )?/g, '').replace(/, $/, '');
    if (sh && sh !== 'none') bump(shadow, sh);
    if (s.transitionDuration.split(',').some((d) => parseFloat(d) > 0)) bump(motion, `${s.transitionProperty} | ${s.transitionDuration} | ${s.transitionTimingFunction}`);
  }

  // Body text is the size carrying the most characters, not the most elements: nav links outnumber paragraphs.
  const steps = [...sizes].sort((a, b) => a[0] - b[0]);
  const base = top(sizes, 1)[0]?.[0] ?? null;
  const scale = { base, steps: steps.map(([px, chars], i) => ({ px, chars, ratio: i ? round(px / steps[i - 1][0]) : null })), rows: top(rows, 16) };

  const total = [...space.values()].reduce((a, b) => a + b, 0);
  const share = (u) => [...space].reduce((n, [v, c]) => n + (Math.abs(v / u - Math.round(v / u)) < 0.01 ? c : 0), 0) / (total || 1);
  // The largest unit covering most values is the base; 4 always divides more than 8, so a smaller unit wins only when the larger one falls short.
  const unit = [16, 12, 8, 6, 5, 4, 2].find((u) => share(u) >= 0.8) ?? null;
  // Siblings that each hold several text elements are groups; siblings that are text themselves are items inside one group.
  const inside = [], between = [];
  for (const parent of document.body.querySelectorAll('*')) {
    const kids = [...parent.children].filter((k) => k.getClientRects().length && getComputedStyle(k).position !== 'absolute' && getComputedStyle(k).position !== 'fixed');
    if (kids.length < 2) continue;
    const texts = kids.map((k) => (ownsText(k) ? 1 : 0) + [...k.querySelectorAll('*')].filter(ownsText).length);
    for (let i = 1; i < kids.length; i++) {
      const a = kids[i - 1].getBoundingClientRect(), b = kids[i].getBoundingClientRect();
      const gap = b.top - a.bottom;
      if (gap <= 0 || gap > 400 || Math.abs(a.left - b.left) > 2) continue;
      if (texts[i - 1] <= 1 && texts[i] <= 1) inside.push(round(gap)); else if (texts[i - 1] >= 2 && texts[i] >= 2) between.push(round(gap));
    }
  }
  const gi = median(inside), gb = median(between);
  const spacing = { unit, unitShare: unit ? round(share(unit)) : null, values: [...space].sort((a, b) => a[0] - b[0]),
    groupGap: { inside: gi, between: gb, ratio: gi && gb ? round(gb / gi) : null, samples: [inside.length, between.length] } };

  const V3 = [640, 768, 1024, 1280, 1536], V4 = [40, 48, 64, 80, 96];
  const found = [...queries].map((q) => { const [, n, u] = q.match(/([\d.]+)(px|r?em)/); return { q, n: Number(n), u }; });
  const breakpoints = { queries: [...queries].sort(),
    tailwindV3: V3.filter((v) => found.some((f) => f.u === 'px' && f.n === v)),
    tailwindV4: V4.filter((v) => found.some((f) => f.u !== 'px' && f.n === v)),
    other: [...new Set(found.filter((f) => !(f.u === 'px' ? V3 : V4).includes(f.n)).map((f) => `${f.n}${f.u}`))] };

  return { url: location.href, viewport: innerWidth, dark: matchMedia('(prefers-color-scheme: dark)').matches,
    theme: { classes: [...html.classList].filter((c) => !c.includes(':') && /dark|light|theme/i.test(c)), dataTheme: html.dataset.theme ?? '', colorScheme: cs.colorScheme },
    unreadable, declared: names.size, tokens, scale, spacing,
    radius: { distinct: radius.size, top: top(radius, 8) }, shadow: { distinct: shadow.size, top: top(shadow, 6) },
    transitions: top(motion, 8), breakpoints,
    fonts: [...new Set([...document.fonts].filter((f) => f.status === 'loaded').map((f) => f.family.replace(/["']/g, '')))] };
})()
