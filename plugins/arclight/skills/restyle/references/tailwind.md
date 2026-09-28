# Tailwind reference for restyle

## Contents
1. Class mappings (before → after)
2. Tokens (config / CSS vars)
3. Primary + secondary metric layout
4. Sparkline (inline SVG)
5. Tables and numbers
6. Charts

## 1. Class mappings

| Tell | Replace with |
|---|---|
| `bg-gradient-to-r from-violet-600 to-blue-500` (header/surface) | same surface as page (`bg-zinc-950`) + `border-b border-white/10` |
| gradient button | `bg-accent text-accent-foreground hover:bg-accent/90` (flat) |
| `bg-clip-text text-transparent bg-gradient-*` | `text-zinc-50` (or `text-zinc-900` light) |
| `rounded-2xl` / `rounded-3xl` on card | `rounded-xl` |
| `rounded-xl`/`rounded-full` on text input | `rounded-md` (same step as the button beside it) |
| `rounded-xl`/`rounded-full` on button | `rounded-md` |
| `shadow-md/lg/xl/2xl` on card/input/button | remove; add `border border-white/10` (dark) / `border-zinc-200` (light) |
| `shadow-violet-500/30`, `ring` glows | remove |
| `backdrop-blur-*` + `bg-white/5` on in-page card | `bg-zinc-900 border border-white/10` (opaque) |
| icon tile `p-2 rounded-lg bg-blue-500/10 text-blue-400` next to title | remove the tile + icon |
| label `text-base font-medium text-white` | `text-sm text-zinc-400` |
| value `text-2xl font-bold` | primary: `text-5xl font-semibold tracking-tight tabular-nums`; secondary: `text-2xl font-semibold tabular-nums` |
| delta pill `bg-emerald-500/10 text-emerald-400 rounded-full px-2` on every card | `text-sm text-zinc-400 tabular-nums` with baseline text |
| status badge saturated fill (in a table) | dot + text: `inline-flex items-center gap-1.5` with a `h-1.5 w-1.5 rounded-full` colored dot; see §5 |
| status badge saturated fill (standalone tag) | `rounded border border-white/10 px-1.5 py-0.5 text-xs text-zinc-300`; tint text only for real warnings/errors |

Keep: `shadow-*` on modal, popover, dropdown, toast, tooltip.

## 2. Tokens

Centralize so the scale is enforced. The teal below is a placeholder for "the accent", not a recommendation: use the project's brand color, or pick one that fits the product. Tailwind v3 (`tailwind.config.js`):

```js
theme: {
  extend: {
    colors: {
      accent: { DEFAULT: '#14b8a6', foreground: '#042f2e' },
    },
    borderRadius: {
      // chip 4, button and input 6, card 12
      DEFAULT: '4px', md: '6px', xl: '12px',
    },
  },
}
```

Tailwind v4 (CSS):

```css
@theme {
  --color-accent: #14b8a6;
  --color-accent-foreground: #042f2e;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-xl: 12px;
}
```

With the Tailwind CDN / no config, use the literal classes (chip `rounded`=4px, `rounded-md`=6px, `rounded-xl`=12px are already the defaults) and one accent from the palette used consistently (`bg-<accent>-500`).

## 3. Primary + secondary metric layout

Before: `grid grid-cols-2 gap-4` of four identical cards.

After:

```html
<p class="text-sm text-zinc-400"><span class="font-semibold text-zinc-100">Revenue</span> · Aug 1 to Aug 31, 2026</p>

<div class="mt-3 grid gap-3 lg:grid-cols-[2fr_1fr]">
  <!-- primary -->
  <section class="rounded-xl border border-white/10 bg-zinc-900 p-5">
    <div class="flex items-start justify-between gap-6">
      <div>
        <p class="text-sm text-zinc-400">Revenue</p>
        <p class="mt-1 text-5xl font-semibold tracking-tight tabular-nums text-zinc-50">$48,250</p>
        <p class="mt-2 text-sm text-zinc-400 tabular-nums">+12.5% vs Jul</p>
      </div>
      <!-- sparkline (section 4) -->
    </div>
    <div class="mt-5 flex gap-10 border-t border-white/10 pt-4">
      <div><p class="text-sm text-zinc-400">Subscriptions</p><p class="text-xl font-semibold tabular-nums">$41,900</p></div>
      <div><p class="text-sm text-zinc-400">One-time</p><p class="text-xl font-semibold tabular-nums">$6,350</p></div>
    </div>
  </section>

  <!-- secondary, stacked: auto-rows-fr splits the primary's height so both columns end flush -->
  <div class="grid auto-rows-fr gap-3">
    <section class="flex items-center justify-between rounded-xl border border-white/10 bg-zinc-900 px-4 py-3">
      <div><p class="text-sm text-zinc-400">Conversion</p><p class="text-2xl font-semibold tabular-nums">3.8%</p></div>
      <p class="text-sm text-zinc-400 tabular-nums">+0.4 pt</p>
    </section>
    <!-- … -->
  </div>
</div>
```

### When no metric has extra content: equal strip

If every metric is only label + value + delta, don't invent a primary. One bordered strip, cells divided by hairlines, most important metric first:

```html
<dl class="grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-zinc-200 bg-zinc-200 xl:grid-cols-4">
  <div class="bg-white px-5 py-4">
    <dt class="text-sm text-zinc-500">Revenue</dt>
    <dd class="mt-1 text-2xl font-semibold tracking-tight tabular-nums text-zinc-900">$48,250</dd>
    <dd class="mt-1 text-xs tabular-nums text-zinc-500">+12.5% vs Jul</dd>
  </div>
  <!-- … same structure for the rest … -->
</dl>
```

No sparkline here: a compact cell has no slot for one.

### Ordered peers (pricing tiers, steps)

Keep them in sequence; mark the current one in place.

```html
<div class="grid gap-3 md:grid-cols-3">
  <section class="rounded-xl border border-zinc-200 bg-white p-5">…Starter · Downgrade…</section>
  <section class="rounded-xl border border-accent bg-white p-5 ring-1 ring-accent">
    <p class="text-xs font-semibold text-accent">Current plan</p> …Pro…
  </section>
  <section class="rounded-xl border border-zinc-200 bg-white p-5">…Enterprise · Upgrade…</section>
</div>
```

Same card structure for all tiers (name, price, 3–4 limits, one action) so they compare line by line. Only the action differs: `Downgrade` (quiet) / disabled `Current plan` / `Upgrade` (accent, the one filled button).

## 4. Sparkline

No library needed. Placement: on the value's row (`flex items-center justify-between`, sparkline vertically centered with the number) or as a full-width strip at the bottom of the card (`w-full h-10 mt-4`, `preserveAspectRatio="none"`). Not alone in a corner above empty space. Normalize the series into a `0 0 120 32` viewBox:

```html
<svg viewBox="0 0 120 32" class="h-8 w-32 text-accent" fill="none" aria-hidden="true">
  <polyline points="0,24 12,22 24,25 36,18 48,20 60,14 72,16 84,10 96,12 108,6 120,4"
            stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="120" cy="4" r="2" fill="currentColor"/>
</svg>
```

React helper when data is an array:

```tsx
function Sparkline({ data, className = "h-8 w-32 text-accent" }: { data: number[]; className?: string }) {
  if (data.length < 2) return null;
  const min = Math.min(...data), max = Math.max(...data), span = max - min || 1;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * 120},${30 - ((v - min) / span) * 28}`);
  const [lx, ly] = pts[pts.length - 1].split(",");
  return (
    <svg viewBox="0 0 120 32" className={className} fill="none" aria-hidden="true">
      <polyline points={pts.join(" ")} stroke="currentColor" strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={lx} cy={ly} r={2} fill="currentColor" />
    </svg>
  );
}
```

## 5. Tables and numbers

- Numeric columns: `text-right tabular-nums`; header of that column also `text-right`. Order columns `Status | Customer | Date | Amount` — status at the leading edge, the numeric column last at the right edge. Status cell: `<span class="inline-flex items-center gap-1.5 text-zinc-300"><span class="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>Paid</span>` (dot color carries the state; text stays neutral except for errors).
- Column widths: let `table-auto` size columns from content, or give proportional widths; don't pin status/date/amount to narrow fixed widths so the name column absorbs all spare space.
- Row separation: `divide-y divide-white/10` on `tbody`, not zebra stripes + shadows.
- Currency with consistent decimals in a column (`$86.00`, not `$86`).

## 6. Charts

- Secondary chart: neutral stroke (`stroke-zinc-300` / `#d4d4d8`), 1.5px, no gradient fill, faint horizontal gridlines (`stroke-white/5`), muted axis labels.
- Only the hero series gets the accent.
- Range toggles (7d/30d/90d): segmented control, `rounded-md`, active item `bg-white/10 text-zinc-50`, others `text-zinc-400`.
