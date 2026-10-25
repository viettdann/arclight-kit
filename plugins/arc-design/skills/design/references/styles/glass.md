# Style: Glass

Smoky glass panes for a tool: a neutral grey face, a lit edge drawn in `box-shadow`, depth read as thickness, and one small clear pane for every state. Reads as tactile, calm, and dense enough to work in; fails when the face gets a gradient or glow, when panes stack blur on blur, or when each state invents its own look.

**Fits:** "glass", "Solid Glass", "smoky glass", "frosted panes", "material", "tactile", AI apps and agent workspaces, dashboards and consoles that live in panes. **Profile:** tool. On a marketing surface it applies its palette, panes, and radius on top of the marketing profile and keeps that profile's space and motion. **Posture:** restrained.

## Decisions

- **Canvas:** dark by default; this overrides the light-by-default rule, because the style's panes read as glass against a dark field and the brief chose the style for that. Light when the brand is light or the brief asks. Dark is built per `dark-mode.md`.
- **Backdrop:** the dark theme has none, a flat `--background`. The light theme fixes two or three large, soft radial fields of the brand hue at 4–11% alpha behind the layout (`--light-1..3`), so the panes have something to blur.
- **Rule 1, the finish is at the edge:** every pane draws, with `box-shadow` only and `border-width: 0`, a 1px inset top rim (`--glass-rim`), a 1px inset inner ring (`--glass-inner`), a 1px outer hairline ring (`--glass-edge`), a contact shadow `0 1px 2px var(--glass-contact)`, and a shade `0 12px 32px -14px var(--glass-shade)`. Popovers and dialogs use `inset 0 1px 0 var(--glass-rim), inset 0 -1px 0 var(--popover-under), 0 0 0 1px var(--popover-edge), 0 24px 60px -18px var(--glass-shade), 0 6px 16px -6px var(--glass-lift)`.
- **Rule 2, heavy, not airy:** the face is neutral grey. Dark-theme blur is `blur(26px)` with no saturate, light-theme pane blur is `blur(26px) saturate(180%)`, and controls on glass use `blur(14px)`.
- **Rule 3, depth is thickness:** panel (layout columns) < card < popover and dialog, each more opaque than the one below (values in the palette table). Nothing else separates the three.
- **Rule 4, one state:** hover, selected, and held-open all wear the same small clear pane, `background: var(--glass-state)` with `box-shadow: inset 0 1px 0 var(--glass-state-rim), 0 0 0 1px var(--glass-state-edge)`.
- **Primary button:** a solid ink fill (`--primary`) with a 1px inset top rim. The brand hue goes to status and one accent per view, not to the button.
- **Brand color:** with a brand color or existing tokens, the project's tokens keep their values and the glass roles map onto them: `--brand`, `--light-1`, and `--light-3` take the brand hue, and the neutrals keep the table's lightness and alpha steps.
- **Status colors:** status hues and `--brand` color only dots, glyphs, rings, and fills, and each dot or glyph sits beside its text label; status text and labels on panes use `--foreground` or `--muted-foreground`.
- **Input boundaries:** inputs use `--border-strong`, each value passing 3:1 as `ui` on `--card` over `--background` (check with `scripts/contrast.mjs`). `--input` and `--border` stay decorative hairlines.
- **Radius:** every pane (panel, card, popover, menu, dialog) 14px (`--radius: 0.875rem`), controls 11px (`--radius-control: 0.7rem`), nested corners concentric (inner = outer − padding). This overrides the tool-profile roles in `radius.md`.
- **Overrides for glass-style panes:** `profile-tool.md` "Depth comes from surface value, not shadow … glass only on a sticky or floating layer over moving content" does not apply, since a pane is glass in the page and takes the shadow stack above. `cards.md` flat panels and "never border plus shadow" do not apply either: a pane's edge is a `box-shadow` ring, never a border. `tokens.md` "Tint neutrals slightly toward the brand hue" does not apply: the canvas and pane faces (`--background`, `--panel`, `--card`, `--popover`) stay grey, chroma at most 0.007; edge, shadow, and border tokens keep the palette's cool tint. `materials.md` (Glass) keeps only its Fallback and Contrast rules for these panes.
- **Blur placement:** `backdrop-filter` goes on popovers, menus, and dialogs in both themes, and on panels and single cards in the light theme, where the light fields show through. Cards repeated in a list (agent steps, ask cards, rows) and every in-page pane in the dark theme take the tint and edge with no `backdrop-filter`: the flat canvas behind them gives the blur nothing to change, and each blurred layer repaints on scroll.
- **Nested panes:** a pane inside another pane keeps its tint and edge and has no `backdrop-filter` of its own, so there is never blur on both.
- **Fallback:** under `@supports not (backdrop-filter: blur(1px))`, `@media (prefers-reduced-transparency: reduce)`, and `@media (prefers-contrast: more)`, panes use the opaque values from the table and no `backdrop-filter`. Rim and shadow stay. Under `prefers-contrast: more` the outer hairline is `--border` at double alpha.
- **Contrast:** check text on each pane over the lightest and darkest backdrop that can sit behind it, including a light field over the canvas, per `materials.md` (Glass, Contrast).
- **Type, spacing, and motion:** follow the profile.
- **Default palette:** the brand's colors always win. When the brief and the code give no brand color, use this set (from Solid Glass, MIT © DeepLethe, values as of 2026-10-24: https://github.com/deeplethe/solid-glass) instead of choosing a new one, and list it as an assumption in the summary:

  | Token | Light | Dark |
  |---|---|---|
  | `--background` | `oklch(0.925 0.007 265)` | `oklch(0.16 0 0)` |
  | `--foreground` | `oklch(0.16 0 0)` | `oklch(0.985 0 0)` |
  | `--muted-foreground` | `oklch(0.47 0 0)` | `oklch(0.78 0 0)` |
  | `--panel` | `oklch(0.975 0.004 265 / 44%)` | `oklch(1 0 0 / 4.5%)` |
  | `--card` | `oklch(0.98 0.004 265 / 60%)` | `oklch(0.31 0 0 / 46%)` |
  | `--popover` | `oklch(0.985 0.003 265 / 96%)` | `oklch(0.22 0 0 / 96%)` |
  | `--primary` / `--primary-foreground` | `oklch(0.2 0 0)` / `oklch(0.985 0 0)` | `oklch(0.94 0 0)` / `oklch(0.18 0 0)` |
  | `--border` | `oklch(0.3 0.02 265 / 13%)` | `oklch(1 0 0 / 11%)` |
  | `--input` | `oklch(0.3 0.02 265 / 15%)` | `oklch(1 0 0 / 13%)` |
  | `--border-strong` | `oklch(0.6 0.02 265)` | `oklch(0.6 0 0)` |
  | `--glass-rim` | `oklch(1 0 0 / 90%)` | `oklch(1 0 0 / 16%)` |
  | `--glass-inner` | `oklch(1 0 0 / 35%)` | `oklch(1 0 0 / 4%)` |
  | `--glass-edge` | `oklch(0.38 0.03 265 / 10%)` | `oklch(1 0 0 / 6%)` |
  | `--glass-contact` | `oklch(0.25 0.03 265 / 6%)` | `oklch(0 0 0 / 10%)` |
  | `--glass-shade` | `oklch(0.3 0.06 265 / 28%)` | `oklch(0 0 0 / 60%)` |
  | `--glass-lift` | `oklch(0.25 0.03 265 / 14%)` | `oklch(0 0 0 / 22%)` |
  | `--popover-edge` / `--popover-under` | `oklch(0.38 0.03 265 / 22%)` / `oklch(0.38 0.03 265 / 16%)` | `oklch(1 0 0 / 6%)` / `transparent` |
  | `--glass-state` / `--glass-state-rim` / `--glass-state-edge` | `oklch(0.3 0.02 265 / 9%)` / `oklch(1 0 0 / 85%)` / `oklch(0.3 0.02 265 / 13%)` | `oklch(1 0 0 / 7%)` / `oklch(1 0 0 / 11%)` / `oklch(1 0 0 / 6%)` |
  | `--light-1` / `--light-2` / `--light-3` | `oklch(0.68 0.13 165 / 7%)` / `oklch(0.75 0.08 240 / 11%)` / `oklch(0.68 0.13 165 / 4%)` | `transparent` |
  | `--brand` | `oklch(0.68 0.13 165)` | `oklch(0.68 0.13 165)` |
  | `--status-running` / `--status-done` / `--success` / `--status-interrupted` | `oklch(0.52 0 0)` / `oklch(0.56 0.16 248)` / `oklch(0.58 0.15 152)` / `oklch(0.66 0.16 58)` | same |
  | opaque `--panel` / `--card` / `--popover` | `oklch(0.947 0.006 265)` / `oklch(0.958 0.005 265)` / `oklch(0.98 0.003 265)` | `oklch(0.19 0 0)` / `oklch(0.225 0 0)` / `oklch(0.245 0 0)` |

## Signature moves (examples)

These show the style's spirit; they are not a menu. Derive the surface's distinctive move from the product first, and use one of these only when it fits better. Never more than two per page.

- **The thickness ladder** (`materials.md`, Style materials, Pane) as the only hierarchy cue between layout columns, cards, and overlays: no borders, no extra shadows, only more opaque as a layer rises.
- **A sidebar as a pane standing on its edge,** lit along the side facing the page: `inset -1px 0 0 var(--glass-edge), inset 0 1px 0 var(--glass-inner)`.
- **The one-state pane on agent work:** steps, ask cards, and turn status wear the same small clear pane for hover, selected, and held open; their behavior comes from `${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/agent.md`.

## Range

- **Figures:** a number on one card pane at 14px radius in `--foreground`, with a status dot in its hue beside the text label.
- **Steps:** a column of card panes, one per step, separated only by the thickness ladder; the current step wears the one-state clear pane.
- **Rows and forms:** rows as repeated cards with tint and edge and no `backdrop-filter`; inputs on `--border-strong`; the primary a solid ink fill with its top rim.
- **Bands:** in the light theme, two or three soft fields of the brand hue behind the panes; in the dark theme, the flat canvas. Never a gradient on a face.

## Avoid

A border on a pane (a second ring on top of the shadow edge); gradient or glow on the face; refraction or liquid-glass distortion; a tint that boosts backdrop color in the dark theme; a different look per state (hover, selected, and open each styled their own way); glass over glass with blur on both; neutrals tinted toward the brand hue; status color on text.
