# Fidelity

A design file is a picture of the result plus the numbers behind it. Generated or exported code reproduces the picture at one width with absolute coordinates, so it looks right in the tool and breaks in the product; this reference turns it into project code and proves the build still matches.

Contents: Source · Build from the source · Layout mapping · Variables to tokens · Assets · Fonts first · Exact values · Compare the build · Classify each difference · Checks

## Source

- The source is whatever the user hands over: a design-tool file or frame (through an MCP server, plugin, or inspect panel), an exported code bundle (HTML, JSX, CSS, a variables or tokens JSON), or only an image. Name which one you had in the summary.
- Values come from the source's data (inspect values, exported code, variables); its render or screenshot is the visual target only, never an implementation asset and never something to measure.
- With only an image, snap every value to the existing scale and say in the summary that values were estimated, not read.
- A truncated or summarized response for a large frame isn't a source: request its child frames one by one instead of filling the gaps by eye.
- Only the frames the user named are in scope; note mismatches you see elsewhere, don't fix them.

## Build from the source

- Generated code is a prototype: absolute positions, fixed pixel widths, a `div` per layer, inline styles. Rebuild it in the project's layout (flex, grid, semantic elements); keep absolute or fixed positioning only where the design truly overlaps (a badge on an avatar, a sticky bar, art bleeding over a section edge).
- Before writing markup, search the repo and the installed UI library for a component, icon, and token matching each design element; reuse or compose them and extend through props or variants. Raw markup and literal values only when nothing fits, and say which.
- A component mapping between the design and the code (Code Connect or a project map) is used exactly where it points; styling effort isn't a reason to bypass it.
- The design shows controls as still pictures: decide which elements are interactive and build them as real buttons, links, and inputs with every state from `${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/SKILL.md`. States the design doesn't draw (hover, focus, loading, empty, error) come from the tokens, not invention.
- Frames at several widths are breakpoints; the widths between them follow the responsive rule in SKILL.md. A single desktop frame doesn't license a shrunk desktop layout on phones.
- Copy in the design is content: build it as written, and list placeholder text (lorem ipsum, sample names, fake numbers) in the summary instead of shipping it as real.

## Layout mapping

Auto layout and constraints already state the intent; translate them, don't re-derive them from coordinates.

- Horizontal or vertical stack → `flex-direction: row | column`; wrap → `flex-wrap: wrap`; a grid layout → CSS grid with the same tracks.
- Item spacing → `gap` on the parent, never margins on the children; "space between" spacing → `justify-content: space-between`; padding → `padding`.
- Primary-axis alignment → `justify-content`, cross-axis → `align-items`.
- Fill → `flex: 1 1 0; min-width: 0` on the main axis (so long text truncates instead of overflowing), `align-self: stretch` on the cross axis; hug → no size set; fixed → a fixed size only for things that are fixed by nature (icons, avatars, a sidebar), otherwise `max-width` so it can shrink.
- Min and max width or height → `min-*` and `max-*`. Left-and-right constraints mean stretch; center means centered; scale is rarely meant literally.
- An absolutely positioned child inside a stack → `position: absolute` in a `position: relative` parent.
- A frame with no auto layout: infer it. Items aligned on one row become flex; columns that line up across rows become grid.
- Text boxes get no height: fixed-height text clips when copy or the font changes.
- An inside stroke → `border` with `box-sizing: border-box`; an outside or center stroke → `outline` or a `box-shadow` spread, so the stroke doesn't shift the layout.
- Layer opacity fades the children too; fill opacity is a color with alpha. Keep them apart.
- Drop shadow → `box-shadow`; background blur → `backdrop-filter` under the glass rules in `materials.md`; layer blur → `filter: blur()`.
- Letter spacing given in percent is that many hundredths of an em (`2%` → `0.02em`); line height in percent is a unitless ratio (`150%` → `1.5`).

## Variables to tokens

- Match a design variable or style to a project token by role first, value second: `text/secondary` maps to `--color-text-muted` even when the hex is a shade off; the value difference goes in the summary.
- One value used in two roles in the design becomes two semantic tokens on one primitive (`tokens.md`, Three layers), not one token reused for both.
- Variable modes (light and dark, brand A and B) map to the theme layer, not to separate component values.
- A text style maps to one type-scale step as a set: size, line height, weight, and tracking together.
- A raw value with no variable: equal to a token → use the token; one step off and used once → snap to the token and note it; repeated across the design and missing from the scale → token work: add it per `tokens.md` and list it.
- Never name a token after a layer, frame, or hex value (`--frame-12-bg`, `--gray-6b6b66`); names state the role.
- Design components map to code components by name and variant: each variant property becomes a prop, not a copy of the component per variant.

## Assets

- Use every image and SVG the source provides, as a file, at the position the design puts it. Never redraw, retrace, simplify, or rebuild one from CSS and `div`s; swap it only for an identical asset already in the repo.
- Keep an SVG's `viewBox` and its root `width` and `height`; size it through the wrapper or one dimension so the ratio holds, never `width: 100%; height: 100%` on both.
- Download assets into the repo: design-tool asset URLs are temporary and break after the export expires. No asset URL from the tool's host stays in code.
- Imagery that comes from data (avatars, product photos, user uploads) stays dynamic; the picture in the design is sample content.
- Illustrations, logos, and multi-color art stay byte-identical. A one-color glyph in an icon role may have its hardcoded fill rewritten to `currentColor` (`icons.md`, Color); that is the only edit.
- An asset the export doesn't include becomes a labeled slot listed in the summary, not a stand-in drawn to look like it.

## Fonts first

- Fix fonts before spacing: a substituted font changes glyph widths, so every line break and measured gap after it is wrong too.
- List the families the source uses, by role (body, display, UI label, numbers, code). Each gets its own `@font-face` per weight and style the design renders and its own token; a display serif and a UI sans never share one `--font-sans`.
- Font files come from the export, the brand kit, or the provider. If a licensed file is missing, say so, ship a metric-matched fallback (`typography.md`, Loading fonts), and list it; `system-ui` standing in for the design's face isn't a finished build.
- Weights the design uses outside 400 and 600 are kept and recorded in `DESIGN.md` as a departure, not rounded to the two-weight rule.

## Exact values

- Read each value off the source's data: font size and line height as a pair (a 15px size with a 24px line height, not just 15px), color in its own gamut (a display-p3 value stays p3 with an sRGB fallback, `color.md`, Gamut), radius, border width, shadow, and every small decoration (hairlines, chip backgrounds, dashed outlines, underlines, markers).
- Small decorations are what conversion drops first and nobody notices; check each one in the source against the build.

## Compare the build

- Parity is a render comparison, never a code reading. Shoot the build at the frame's width, in the frame's theme, after fonts load (`--wait-for <css>` or `--eval "document.fonts.ready.then(() => {})"` with the screenshot script), and put it next to the design's render at the same CSS width; a 2x export is compared at its CSS size, not its pixel size.
- Compare in this order: section stacking order, content width and text measure, typeface, type scale, color, spacing, then each decoration.
- The same paragraph wraps to the same number of lines in both. A different count points at the font, size, tracking, or container width, and is cheaper to spot than a spacing error.
- A flow layout never lands on the design's exact coordinates; judge structure, type, and decoration, not pixel positions.
- Also shoot one width the design doesn't cover (390 when only a desktop frame exists): that width is your responsive decision and nobody else checked it.

## Classify each difference

- **Conversion drift:** the build lost or substituted something the source has (a font, a decoration, a value). Fix it.
- **Design newer than the build's source:** the frame changed after the export the build came from (a later edit date or version, new elements that need data the app doesn't have). Report it and let the user choose to re-sync; never invent data or fake the element to match.
- **Deliberate departure:** a change made for a rule the design breaks (a hit area under 24px, a missing focus state, a narrow width). Keep it and list it with the rule. A text pair that fails AA moves to the nearest ramp step that passes, keeping its hue, and is listed with both ratios.
- The summary lists every remaining difference under one of the three, and what was fixed.

## Checks

- [ ] Summary names the source type, and says values were estimated when only an image existed.
- [ ] No absolute positioning or fixed pixel widths left from the export except true overlaps.
- [ ] Existing components and tokens reused; no token named after a layer or hex.
- [ ] Every provided asset is a local file in its design position, unredrawn, with no design-tool asset URL left in code.
- [ ] Every family the source uses has `@font-face` and its own token; no design text renders in a fallback.
- [ ] Build and design shot at the same width; the same paragraph has the same line count.
- [ ] Every remaining difference is classed as conversion drift (fixed), newer design (reported), or deliberate departure (listed), and every failing AA pair moved to the nearest passing ramp step.
