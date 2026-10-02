# Materials

A material is how a surface is made: what fills it, what edges it, how it lifts, and what texture it carries. Each one says something about its layer (part of the page, raised, floating, special), so choose it from that meaning and use one per context. Profiles and styles pick materials from this file and set their parameters; the rules here (where a material belongs, fallbacks, contrast, `prefers-*`) hold for every profile and style.

Contents: choosing · solid and hairline · lightness layers · shadow · glass · scrim · gradient and glow · texture · tint fill · style materials (double bezel, solid lip, hard offset shadow, inversion) · checks.

## Choosing

| Layer | Tool profile | Marketing profile | Dark theme |
| --- | --- | --- | --- |
| In the page (card, panel, table, section) | Solid and hairline | Solid; a card on a tinted canvas may take one layered shadow (`cards.md`) | Lightness step and alpha hairline |
| Floating (menu, popover, modal, toast, tooltip) | Raised solid and overlay shadow | Same | One step lighter and hairline; shadow optional |
| Over moving content (sticky header, floating nav, controls over media) | Solid, or glass | Glass or solid | Glass or solid |
| Behind a modal or sheet | Scrim | Scrim | Scrim |
| One special element (hero media, the featured card) | None | Gradient, texture, or a style material | Same, glow only where the style allows |

Never a full-strength border and a shadow on the same element: the two edges read as a double outline.

## Solid and hairline

The default material: an opaque surface token with a 1px hairline where it meets a surface of the same value.

- Light: the hairline is the text color at about 6–10% (`border` token). Dark: white at about 6–10% alpha (`rgb(255 255 255 / 0.08)`), not a fixed grey hex: the same token reads one step lighter on every layer, where a hex disappears on one surface and glares on another.
- A hairline is decorative, around 1.2:1. A boundary that identifies a control (text input, select, checkbox) needs 3:1 against its surface, so inputs use `border-strong`, checked with `scripts/contrast.mjs` as `ui`.
- Hover on a solid surface changes its value (one step), not its position or shadow, in the tool profile.

## Lightness layers

Depth from surface value instead of shadow: base, surface, raised, and floating (a layer opened from a raised one), each one step above what it sits on.

- The step follows what a layer sits on, not what kind of element it is: a card sits one step above the page, a popover one step above what it opens from, a menu inside a modal one step above the modal.
- Dark themes raise with lightness only. A black shadow on a near-black page is invisible, so it can't be the elevation cue. In-page surfaces carry no shadow; floating layers are told apart by their lighter surface plus a hairline, and a shadow may stay under them for overlap, not as the signal. Steps and inks are built in `dark-mode.md`.

## Shadow

Shadow means "this is above the page". Elevation tokens are levels 0–3 (`tokens.md`).

- **Overlay shadow:** menus, popovers, dialogs, toasts, tooltips, in every profile. Keep these.
- **Layered shadow** (marketing): a tight contact shadow plus a soft ambient one, tinted toward the background hue rather than pure black, only where lift carries meaning. Example: `0 1px 2px oklch(0.3 0.02 <hue> / 0.08), 0 8px 24px oklch(0.3 0.02 <hue> / 0.08)`.
- **Diffused shadow** (premium): large blur, low opacity, small offset, tinted the same way, plus a 1px highlight on the top edge of lifted objects. Most surfaces stay flat, so depth still marks what matters.
- Not on in-page surfaces in the tool profile, never colored glows as shadows, never on every card, input, and button.

## Glass

A translucent layer that blurs what passes behind it. It says "this floats above content that keeps moving" and keeps the reader's place in that content (the page under a sticky header, the map under a sheet). The generated-look version is glass on cards over a static gradient: nothing moves behind it, so the blur only lowers contrast. Minimal and brutalist use no glass.

- **Where:** sticky or fixed headers and navigation, floating toolbars and tab bars, sheets, popovers, and menus over imagery or a map, captions and controls over video or a photo. Not on in-page surfaces (cards, panels, pricing tiers, form groups, stat tiles), never glass inside glass.
- **Budget:** one or two glass layers per view, each small relative to the viewport. Every glass layer repaints when the content behind it moves, which is costly on phones; a blurred layer covering most of the screen stutters.
- **Tint:** the surface token at an alpha, not white or black at a low one: `color-mix(in oklch, var(--surface) 75%, transparent)`, or `bg-surface/75`. Glass that holds text is 70–85% opaque; the blur hints at what passes behind, it isn't a window.
- **Blur:** 12–24px (`backdrop-blur-md` to `backdrop-blur-xl`), optionally `saturate(140%)` so colors behind don't turn muddy. More blur costs more and reads as fog.
- **Edge and depth:** a hairline as in solid surfaces, plus an optional 1px inner highlight on the top edge. Floating glass (sheet, popover, floating nav) keeps its overlay shadow; a header flush with the top edge has a bottom hairline only and no corner radius (`radius.md`). In a dark theme the tint is a layer step lighter than what it covers.
- **Fallback:** opaque by default, translucent only where the blur works, so an unsupported browser never shows unblurred text over busy content: `bg-surface/95 supports-[backdrop-filter]:bg-surface/75 backdrop-blur-md`, or the translucent values inside `@supports (backdrop-filter: blur(1px))`. Under `prefers-reduced-transparency: reduce` and `prefers-contrast: more` the layer is solid, with a stronger border under `more`.
- **Contrast:** check text on the glass over the lightest and the darkest content that can pass behind it. The contrast script takes a stacked background, top layer first: `node scripts/contrast.mjs "#1c1c1a|#ffffffbf over #ffffff" "#1c1c1a|#ffffffbf over #202020"`. Blur averages what is behind, so a solid backdrop color is the worst case.

## Scrim

The layer behind a modal, sheet, or drawer that dims the page (`overlay` token).

- Near-black at about 40–60% in light themes, 60–70% in dark, tinted toward the brand hue like the neutrals. It dims; it doesn't hide what the dialog came from.
- No blur by default. A blurred scrim counts as glass: same fallbacks, and it is the view's one large glass layer only while the dialog is open.
- Under `prefers-contrast: more` the scrim gets darker, never lighter.

## Gradient and glow

- **Gradient** (marketing only): adjacent hues (about 60° of travel), lightness moving in one direction, interpolated `in oklch` (`linear-gradient(in oklch, ...)`), with slight noise against banding. Never under body text, never on buttons, headers, or text in the tool profile.
- **Glow:** only as the single light source of a style that lists it (cinematic dark tech): a soft glow behind the product visual, or a gradient hairline on the one featured card. Nothing else on the page glows.

## Texture

Grain, halftone, dither, scanlines: an analog surface over flat color. Used by cinematic (film grain) and brutalist (analog texture).

- A fixed `pointer-events: none` overlay, subtle: grain at 3–5% opacity, patterns light enough that edges stay crisp.
- It lies over imagery, bands, and display type. Body text sits outside the textured area; when the texture covers the whole page, body text must still pass 4.5:1 measured with the texture on.
- Removed under `prefers-contrast: more`. A texture that moves (flicker, rolling scanlines) is also removed, or frozen, under `prefers-reduced-motion: reduce`.
- No texture in the tool profile.

## Tint fill

A very light background of a hue with a dark text step of the same hue, at 4.5:1. For categories (tags, labels, callouts) and avatars in quiet palettes (`avatars.md`); minimal uses it for every category color. Never a saturated fill for a category in the tool profile.

## Style materials

Belong to one style; use them only when that style is chosen, on the objects the style names.

- **Double bezel** (premium): an outer shell (subtle tinted background, hairline ring, 6–8px padding, shell radius from the premium radius table) holding an inner core (its own background, an inset top highlight, radius = outer − padding). One or two objects per page, never every card.
- **Solid lip** (playful, bubbly): a 3–4px band of a darker shade of the fill under buttons and cards, drawn as a hard shadow (`0 4px 0 <darker step>`); press removes it and moves the element down by the same distance.
- **Hard offset shadow** (playful, neo-brutal): an unblurred shadow in the ink color (`4px 4px 0 var(--ink)`) with a 2–3px ink border; press translates the element into its shadow.
- **Inversion** (brutalist): a solid block in the text color with the canvas color as text, for the one thing that matters on the screen. Depth in brutalist comes from rules and inversion only.

## Checks

- [ ] One material per layer per context; no border plus shadow on one element.
- [ ] Shadows only on floating layers (and marketing lift with meaning); none in-page in the tool profile; dark themes raise with lightness.
- [ ] Glass only on layers over moving content, at most two per view, 70–85% opaque with text, passing contrast over the lightest and darkest backdrop, opaque without `backdrop-filter` and solid under `prefers-reduced-transparency` and `prefers-contrast: more`.
- [ ] Gradients and glow only where the profile or style allows, never under body text.
- [ ] Texture removed under `prefers-contrast: more` (and frozen under reduced motion if it moves); body text outside it or passing with it on.
- [ ] Input boundaries pass 3:1; hairlines are alpha in dark themes.
- [ ] Style materials appear only with their style, on one or two objects where the style says so.
