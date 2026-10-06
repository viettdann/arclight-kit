# Color

How to build the ramps, which step does which job, what to call the tokens, and how to audit a palette that already exists. The basics of OKLCH scales and tinted neutrals are in `tokens.md` (Building color scales); the dark set is in `dark-mode.md`. This file adds the numbers those two leave open.

Contents: ramps · roles per step · brand color · several hues · naming · gamut · increased contrast · mid-lightness surfaces · palette audit · checks.

## Ramps

A product needs one neutral ramp (it carries most of the interface), one accent ramp, and a status ramp only for each state the product actually shows. Build them with a color library (`culori`, `colorjs.io`) interpolating in OKLab or OKLCH, then correct the output against the rules below; sRGB interpolation gives muddy mid-steps and HSL lightness bunches steps at one end.

- **Finer at the light end.** Light steps (Tailwind `50`–`200`, Radix `1`–`5`) about 0.04–0.05 apart in OKLCH L; mid-ramp steps about 0.07–0.10. An evenly spaced ramp leaves `100` already too dark for a subtle surface, and the pale backgrounds have nowhere to go.
- **No twins.** Two adjacent steps under about 0.03 L apart look the same on screen: the ramp has one step more than it has decisions. Drop one rather than keep a step nobody can tell apart.
- **Chroma peaks in the middle.** Highest around the solid-fill step, falling toward both ends, so the lightest step is nearly neutral. Full chroma at the ends gives a `50` that glows behind text and a `950` that reads as a stain instead of ink.
- **Ends stop short.** The lightest step stays below L 1 and the darkest above L 0 (roughly 0.98 and 0.15–0.25), so the ramp keeps its hue exactly where the page background and body text live, and `#fff`/`#000` remain free for the rare pure use.
- **One hue end to end.** A ramp whose hue drifts reads as two colors blended and clashes with a neutral tinted toward a different hue.

## Roles per step

Generate the steps the roles call for. Radix numbers steps by role, so `9` is the solid fill in every ramp and theme; Tailwind numbers them by lightness, so this mapping holds in light themes and inverts in dark (page background near `950`, text near `50`). On Tailwind, keep the role mapping in the semantic tier so components never swap step numbers per theme.

| Role | Tailwind (light) | Radix | Semantic token |
| --- | --- | --- | --- |
| App background | white or `50` | `1` | `--color-bg` |
| Subtle background (sidebar, striped row, well) | `50` (`100` if the app is `50`) | `2` | `--color-bg-subtle` |
| Component background | `100` | `3` | `--color-bg-control` |
| Component hover | `200` | `4` | `--color-bg-control-hover` |
| Component active, selected | `200`–`300` | `5` | `--color-bg-control-active` |
| Subtle border, separator | `200` | `6` | `--color-separator`, `--color-border-subtle` |
| Default border | `300` | `7` | `--color-border` |
| Focus ring | accent `600` | accent `9` | `--color-focus-ring` (3:1 against every surface it sits on, measured as `ui`) |
| Strong border, hovered border | `400`–`500` | `8` | `--color-border-strong` |
| Solid fill | `600` | `9` | `--color-accent` |
| Solid fill hover | `700` | `10` | `--color-accent-hover` |
| Low-contrast text | `600` neutral, `700` accent | `11` | `--color-text-muted`, `--color-accent-text` |
| High-contrast text | `900`–`950` | `12` | `--color-text` |

- Where the table gives two roles the same Tailwind step, they render identically. If hover and active (or separator and component hover) must differ, add an intermediate light step or move to a 12-step ramp; don't nudge one with opacity.
- `border-strong` used as an input boundary must reach 3:1 against its surface (`materials.md`): on white, Tailwind gray-400 `#9ca3af` measures 2.54:1 and gray-500 `#6b7280` 4.83:1, so inputs take `500`. Measure the Radix step `8` of your ramp the same way before using it on inputs.
- Fill sits on `600`, not `500`, because white text on most Tailwind `500` hues fails 4.5:1.

## Brand color

- Pin the brand on the solid-fill step, so the primary button shows the real brand and not an approximation, and build the ramp outward from it; that one step may sit slightly off the even spacing.
- Never darken the brand quietly to make a pair pass: the client sees a different color on every button and nobody decided it.
- If white text on the brand fails, keep the brand exact and change where it is used. White on Tailwind blue-500 `#3b82f6` measures 3.68:1: it passes for large text and UI (3:1) but not for body text. Either move fills (buttons, badges with text) to the next darker step (`#2563eb`, 5.17:1) and keep the brand step for large marks, icons, and the logo, or keep the brand as the fill with dark text on it (`#0f172a` on `#3b82f6`, 4.85:1).
- Check every pair with `node ${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/contrast.mjs "#ffffff|<fill>|text"` before writing a number down.

## Several hues

- **Same step, same lightness.** `red-600` and `blue-600` share an OKLCH L, or a danger button looks heavier than a primary one at the same step.
- **Same share of the hue's maximum chroma, not the same chroma.** Hues reach different chroma inside sRGB: at L 0.65 the ceiling is about 0.236 for red (hue 30), 0.204 for green (145), 0.184 for blue (250), 0.132 for yellow (90), and 0.110 for cyan (200). Copying 0.18 across clips the cyan and yellow and leaves the red dull; 80% of each ceiling keeps them equally vivid.
- **Status hues at least 15° of OKLCH hue from the accent.** Closer, and success, warning, or danger reads as the brand (a teal success beside a teal accent looks like a link). When convention leaves no room, such as a red brand with a red danger, keep the hue and give destructive actions a different treatment: outlined button, icon, explicit label.
- Status ramps need only the roles they render: usually `-bg`, `-border`, a fill, and `-fg` (`tokens.md`). Text steps on dark are lighter than fills (`dark-mode.md`).
- Where a status meaning flips by market (gains are red in Chinese finance UIs), make gain and loss their own tokens per locale, not `success` and `danger`.

## Naming

Primitives name a value (`--blue-600`, `--neutral-200`); semantics name a job and are the only tier components read (`tokens.md`, Three layers).

- Neutral roles lead with the property: `--color-{bg|text|border}-{variant}-{state}`, as in `--color-bg-subtle`, `--color-text-muted`, `--color-border-strong`, `--color-bg-control-hover`. Accent and status lead with the role: `--color-accent-hover`, `--color-accent-text`, `--color-danger-bg`.
- One word per concept, everywhere: `text` (not `fg`, `foreground`, `ink`), `bg` (not `background`, `fill`), `border` (not `stroke`, `outline`). Status keeps the `-fg`/`-bg`/`-border` suffixes from `tokens.md`. A reader who has seen `--color-text-muted` should guess `--color-text-disabled` without opening the file.
- Call the brand `accent`. `--color-primary` next to `--color-text-primary` makes every `primary` ambiguous until someone reads the definition; if `primary` appears at all, it means "most prominent in its group".
- `separator` and `border` are separate tokens even while they share a value: a separator divides content, a border encloses a control, and they split the first time inputs are restyled. Merged, that change recolors every divider too.
- Tailwind v4 builds class names from these (`--color-text-muted` becomes `text-text-muted`), so there the utility supplies the property and the token drops it (`--color-muted` → `text-muted`, `--color-subtle` → `bg-subtle`); the rest of the grammar holds (`tokens.md`, Names and frameworks).

| Anti-pattern | Why it breaks | Instead |
| --- | --- | --- |
| Named by hue: `--blue-text`, `--color-blue-button` | Wrong the day the brand changes | `--color-accent-text`, `--color-accent` |
| Named by value: `--color-light-gray`, `--color-text-2` | `light` is the dark one in dark mode; a number says nothing about the job | `--neutral-200` as a primitive, `--color-text-muted` |
| Named by component or place: `--color-sidebar-gray`, `--card-border` | The second use somewhere else makes the name a lie | `--color-bg-subtle`, `--color-border` |
| Hue plus state: `--color-gray-hover` | Belongs to no tier | `--color-bg-control-hover` |
| Primitive in a component: `bg-blue-600` | No seam for themes; a later dark mode means auditing every use | Point a semantic token at it |

## Gamut

- Write the sRGB value first and the wide-gamut value as an override, so an sRGB screen shows a color you chose instead of one the browser clipped. Clipping happens per channel: it shifts hue and lightness and merges the top steps of a vivid ramp into one rendered color.

```css
.badge-success { background: oklch(0.62 0.16 150); } /* inside sRGB (#20a04e) */
@media (color-gamut: p3) {
  .badge-success { background: oklch(0.62 0.22 150); }
}
```

- `@supports (color: color(display-p3 1 1 1))` gates on syntax support only; use `color-gamut: p3` when the question is whether the screen can show it.
- P3 adds most room in greens and reds (green at L 0.62: about 0.17 in sRGB, 0.24 in P3) and little in blues. Build ramps inside sRGB and treat P3 as enhancement, never as the value contrast was checked on.

## Increased contrast

- `prefers-contrast: more` gets its own block per theme. One global override that darkens `text-muted` and `border` also darkens them on the dark theme, where darker means less contrast.
- Widen the OKLCH L gap of each text and border pair by at least about 0.15 over the default, then remeasure with `contrast.mjs`; a gap widened without remeasuring is a guess.

```css
@media (prefers-contrast: more) {
  :root { --color-text-muted: var(--neutral-800); --color-border: var(--neutral-500); --color-separator: var(--neutral-400); }
  [data-theme="dark"] { --color-text-muted: oklch(0.98 0.003 250 / 0.87); --color-border: oklch(1 0 0 / 0.3); --color-separator: oklch(1 0 0 / 0.2); }
}
```

- The block comes after both theme blocks so it wins at equal specificity. A dark theme that follows `prefers-color-scheme` needs the same overrides under `(prefers-color-scheme: dark) and (prefers-contrast: more)`.
- Materials have their own `more` rules (solid glass, darker scrim, no texture): `materials.md`.

## Mid-lightness surfaces

A background between about OKLCH L 0.55 and 0.75 carries neither ink comfortably. On `oklch(0.58 0.12 250)` white measures 4.27:1 and a near-black `oklch(0.21 0.01 250)` 4.15:1: both fail. Up to L 0.75 only the darkest ink passes, and a muted ink at L 0.45 fails (3.36:1 on `oklch(0.75 0.12 250)`).

- Keep text surfaces near the ends: L above about 0.85 with dark text, below about 0.45 with light text.
- A mid-lightness color can be a fill with one short label (checked) or a non-text mark; it is not a card, banner, or section background.
- When a pair fails, move the lightness of one side and hold its hue; changing hue or chroma barely moves contrast and turns a fix into a palette change. Pushing L toward the ends may need lower chroma to stay in gamut.

## Palette audit

For restyle and redesign of an existing product, before proposing any new color.

1. **Collect every literal:** hex, `rgb(`, `hsl(`, `oklch(`, named colors, framework palette classes (`bg-blue-500`, `text-gray-600`), SVG `fill` and `stroke`, chart configs, inline styles, email templates.
2. **Sort by OKLCH L within each hue family;** drifted copies sit next to each other.
3. **Merge near-duplicates:** two colors under about 0.02 apart in OKLab ΔE are one color that drifted. Keep the most-used value; don't average, since an average matches no screen that exists.
4. **Assign each survivor a role** from the step table. A color with no role is either a missing token or a mistake; say which.
5. **Report the mapping** (old value, use count, kept value, role, token) before changing anything. Consolidating changes rendered output on screens nobody asked to touch, so it stays a proposal until the user accepts it.

APCA (Lc) is a useful lens on dark themes and thin text, but contrast here is checked and reported as WCAG 2 ratios with `contrast.mjs`.

## Checks

- [ ] Light-end steps about 0.04–0.05 L apart, mid-ramp 0.07–0.10, no adjacent pair under 0.03; chroma peaks mid-ramp; ends short of pure white and black.
- [ ] Same step has the same L across hues; chroma is the same share of each hue's sRGB maximum.
- [ ] Every role in the step table maps to one step and one semantic token; input boundaries pass 3:1.
- [ ] The brand value is exact on its step; any text on it passes 4.5:1, or fills moved one step darker, or text on it is dark.
- [ ] Status hues at least 15° from the accent, or destructive actions distinguished by treatment.
- [ ] Tokens follow `--color-{bg|text|border}-{variant}-{state}` (in Tailwind v4, without the property word); brand is `accent`; `separator` and `border` are separate; no hue, value, or component names in the semantic tier.
- [ ] sRGB value first, P3 override inside `@media (color-gamut: p3)`.
- [ ] `prefers-contrast: more` has a block for each theme, each pair at least 0.15 L wider and remeasured.
- [ ] No text surface between about L 0.55 and 0.75.
- [ ] On restyle or redesign, the palette audit mapping was reported before any color changed.
