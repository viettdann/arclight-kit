#!/usr/bin/env node
// WCAG 2.x contrast checker. Usage: node contrast.mjs "#fff|#6366f1" "hsl(222 47% 11%)|#fff" "oklch(0.93 0.005 250)|#131316|large" "#0f766e|#fff|ui" ...
// Pairs are split on "|" because oklch() values contain spaces; a translucent fg is composited over bg first, since that is what the eye sees.
// A bg written as "<tint> over <backdrop>" (glass) is composited the same way, top layer first.

const oklchToRgb = (L, C, H, a) => {
  const h = (H * Math.PI) / 180;
  const [A, B] = [C * Math.cos(h), C * Math.sin(h)];
  const l = (L + 0.3963377774 * A + 0.2158037573 * B) ** 3;
  const m = (L - 0.1055613458 * A - 0.0638541728 * B) ** 3;
  const s = (L - 0.0894841775 * A - 1.291485548 * B) ** 3;
  const lin = [
    4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
  ];
  // Out-of-gamut channels are clipped, which is what browsers do when painting to an sRGB display.
  const enc = (c) => {
    const v = Math.min(1, Math.max(0, c));
    return 255 * (v <= 0.0031308 ? 12.92 * v : 1.055 * v ** (1 / 2.4) - 0.055);
  };
  return { r: enc(lin[0]), g: enc(lin[1]), b: enc(lin[2]), a };
};

const hslToRgb = (H, S, L, a) => {
  const h = ((H % 360) + 360) % 360;
  const k = (n) => (n + h / 30) % 12;
  const c = S * Math.min(L, 1 - L);
  const f = (n) => 255 * (L - c * Math.max(-1, Math.min(k(n) - 3, 9 - k(n), 1)));
  return { r: f(0), g: f(8), b: f(4), a };
};

const NUM = String.raw`(\d*\.?\d+)`;
const alpha = (v, pct) => (v === undefined ? 1 : Math.min(1, Math.max(0, pct ? v / 100 : +v)));

const parse = (input) => {
  const s = input.trim().toLowerCase();
  if (s === "white") return { r: 255, g: 255, b: 255, a: 1 };
  if (s === "black") return { r: 0, g: 0, b: 0, a: 1 };
  const ok = s.match(new RegExp(String.raw`^oklch\(\s*${NUM}(%?)\s+${NUM}\s+${NUM}(?:deg)?\s*(?:\/\s*${NUM}(%?))?\s*\)$`));
  if (ok) {
    const L = ok[2] ? ok[1] / 100 : +ok[1];
    return oklchToRgb(Math.min(1, L), +ok[3], +ok[4], alpha(ok[5], ok[6]));
  }
  const hsl = s.match(new RegExp(String.raw`^hsla?\(\s*${NUM}(?:deg)?\s*[,\s]\s*${NUM}%\s*[,\s]\s*${NUM}%\s*(?:[,/]\s*${NUM}(%?))?\s*\)$`));
  if (hsl) return hslToRgb(+hsl[1], Math.min(1, hsl[2] / 100), Math.min(1, hsl[3] / 100), alpha(hsl[4], hsl[5]));
  // rgb(255 255 255 / 0.08) and rgba(255, 255, 255, 0.08), as the dark-mode reference writes borders.
  const rgb = s.match(new RegExp(String.raw`^rgba?\(\s*${NUM}\s*[,\s]\s*${NUM}\s*[,\s]\s*${NUM}\s*(?:[,/]\s*${NUM}(%?))?\s*\)$`));
  if (rgb) {
    const c = (v) => Math.min(255, +v);
    return { r: c(rgb[1]), g: c(rgb[2]), b: c(rgb[3]), a: alpha(rgb[4], rgb[5]) };
  }
  let h = s.replace(/^#/, "");
  if (h.length === 3 || h.length === 4) h = [...h].map((c) => c + c).join("");
  if (!/^[0-9a-f]{6}([0-9a-f]{2})?$/.test(h)) throw new Error(`Bad color: ${input}`);
  const n = (i) => parseInt(h.slice(i, i + 2), 16);
  return { r: n(0), g: n(2), b: n(4), a: h.length === 8 ? n(6) / 255 : 1 };
};

const composite = (fg, bg) => ({
  r: fg.r * fg.a + bg.r * (1 - fg.a),
  g: fg.g * fg.a + bg.g * (1 - fg.a),
  b: fg.b * fg.a + bg.b * (1 - fg.a),
});

const luminance = ({ r, g, b }) => {
  const lin = (v) => {
    const c = v / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
};

const THRESHOLDS = { text: 4.5, large: 3, ui: 3 };

const pairs = process.argv.slice(2);
if (pairs.length === 0) {
  console.error('Usage: node contrast.mjs "<fg>|<bg>[|text|large|ui]" [...]  (colors: #hex, oklch(...), rgb(...), hsl(...), white, black; bg may be "<translucent> over <opaque>")');
  process.exit(2);
}

let failed = false;
for (const pair of pairs) {
  const [fgHex, bgHex, rawKind = "text"] = pair.split("|");
  const kind = rawKind.trim().toLowerCase();
  let fg, bg;
  try {
    if (!bgHex) throw new Error(`Expected "<fg>|<bg>", got: ${pair}`);
    if (!Object.hasOwn(THRESHOLDS, kind)) throw new Error(`Unknown kind "${kind}", use text, large or ui`);
    // A background may be a stack, top layer first: "<glass tint> over <backdrop>".
    const layers = bgHex.split(/\s+over\s+/i).map(parse);
    const base = layers.pop();
    if (base.a !== 1) throw new Error(`Background must be opaque (or end in an opaque layer): ${bgHex}`);
    [fg, bg] = [parse(fgHex), layers.reduceRight((under, top) => ({ ...composite(top, under), a: 1 }), base)];
  } catch (e) {
    console.error(e.message);
    process.exit(2);
  }
  const [l1, l2] = [luminance(composite(fg, bg)), luminance(bg)].sort((a, b) => b - a);
  const ratio = (l1 + 0.05) / (l2 + 0.05);
  const min = THRESHOLDS[kind];
  const ok = ratio >= min;
  // A failing ratio never prints as the threshold itself: 4.495 shows 4.49, not 4.50.
  const shown = (!ok && +ratio.toFixed(2) >= min ? Math.floor(ratio * 100) / 100 : ratio).toFixed(2);
  if (!ok) failed = true;
  console.log(`${ok ? "pass" : "FAIL"}  ${shown.padStart(5)}:1  (${kind} needs ${min}:1)  ${fgHex} on ${bgHex}`);
}
process.exit(failed ? 1 : 0);
