---
name: restyle
description: De-AI a generic, template-looking UI. Audits the code for "AI tells" (gradients, decorative icon tiles, identical card grids, big radius and shadow everywhere, pure-black dark themes, emoji, fake deltas, unaligned numbers) and rewrites it into a restrained, information-first design with one accent and honest copy. Use whenever the user wants to restyle, clean up or polish the look, "make it look less AI", "look more professional/like Linear/Stripe", de-template, or critique the visual design (code, render, or a screenshot) of an existing dashboard, admin panel, settings page, landing section, or any app UI, even without the word "restyle". Layout and structure stay. Not for a new visual language (redesign), a screen that doesn't exist yet (design), or measured rendering defects such as overflow, contrast, focus (ui-check).
argument-hint: "[file or folder]"
---

# Restyle: remove the AI tells

Generated UIs look generic because every visual choice is decoration instead of information: gradients, rainbow icon tiles, equal-weight cards, shadows on everything, filler copy. The fix is one rule applied five ways:

> **Every visual decision must carry information. If it says nothing, remove it. If it stays, it must mean something.**

The result should still be polished: this is restraint, not brutalism. Keep the layout's purpose, data bindings, behavior, and accessibility intact. If the user wants a new style or direction rather than the generated look removed, that is the redesign skill; if unclear, ask once: "Keep the current layout and clean it up, or a new look with the content kept?"

**The values below are references, not a spec.** The project's own system wins: what `DESIGN.md`, the tokens, or the shared components set consistently (radius scale, font weights, spacing, control heights and paddings, density, border and shadow treatment) stays as it is. Restyle removes the tells, which are decoration without meaning and inconsistency (a one-off value beside the scale, 16px+ radius on every element, a shadow on every card), and leaves the rest of the design alone. Before changing a value, ask whether it is a tell or just a choice different from these defaults; a different choice stays.

## Workflow

This skill's rules replace any other design skill run earlier in the session. Read only the target's current files and the sources the design skill allows (`${CLAUDE_PLUGIN_ROOT}/skills/design/SKILL.md`, Sources); git history, other branches, other repos, and earlier attempts are off limits unless the user names them.

**Critique only** (the user asks for a critique, review, or opinion, not a change, including from a screenshot or mockup alone): follow [critique.md](references/critique.md), report, and stop.

1. **Find the UI.** A before/after, a named reference ("like Linear"), or a score: read [requests.md](references/requests.md) first.
   Locate the files that render the target screen (components, pages, templates, global CSS, `tailwind.config.*`). Run the scanner to get a first list of candidates:
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/scan_tells.py <path-to-src-or-file>
   ```
   If Python isn't available, skip the scan and read the code. It is a heuristic grep, not a verdict: a `shadow-lg` on a modal is correct, a `shadow-lg` on a card is a tell. Read the code yourself too; hierarchy and copy problems don't show up in a grep.

2. **Decide before editing:**
   - **The profile.** App/tool surface (dashboard, admin, settings, billing) or marketing surface (landing, pricing page, portfolio, storefront)? The five principles apply to both, but on a marketing surface the radius and elevation values come from the design marketing profile (`${CLAUDE_PLUGIN_ROOT}/skills/design/references/profile-marketing.md`: its per-element radius table, tinted layered shadows where lift means something) instead of principle 4's tool values, and its layout, imagery, and copy tells join the fixes.
   - **The primary thing on the page.** What is this screen for? On a revenue dashboard it's revenue; on a billing page it's the current plan; on a settings page it's the form. This drives hierarchy (principle 3) and where the accent goes (principle 1).
   - **The accent.** Reuse the existing brand color if there is one (look in tailwind config / CSS vars / the primary button). Otherwise pick one flat color that fits the product, not a house default. Everything else is neutral.

3. **Apply the fixes.** Go straight from the scanner output and your read of the code to edits; don't write an audit or findings table first, since the user judges the result on the page.
   - Fix at the source of truth: if radius, shadow, or colors are set in a shared component or config, change it there rather than patching every usage. Sort each inconsistency first: a value missing from the tokens (add the token), a one-off (use the existing token), a component used for the wrong concept (swap the component), or a local defect (fix in place).
   - Don't change data fetching, props, event handlers, or routes. The scanner tags each `7-code` hit: fix `presentation` hits (list the transitioned properties instead of `all`, animate `transform` instead of width, height, or offsets, replace overshoot easing with the token curves, give a removed outline a `:focus-visible` ring, put a hidden reveal start state behind the marketing profile's `.js` guard); `behavior` hits change handlers, so list them as flagged and fix them only if the user asks (then follow the ui-interaction skill).
   - Keep, unless the user asks: URLs and anchor ids, nav labels, form field `name`s and order, ids, classes, and `data-*` attributes that tests or analytics use, page titles and head metadata (description, canonical, share tags), the logo, and legal, consent, and pricing copy. Restyling changes how it looks, not what it says or where it lives.

4. **Verify.** Re-run the scanner and confirm the remaining hits are intentional (overlay shadows, glass on floating layers, semantic status colors, flagged behavior hits, a radius or weight the project's scale uses). Check contrast for every color pair you changed, in one command: `node ${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/contrast.mjs "fg|bg|kind" ...` (kind `text` 4.5:1, `ui` 3:1 for input borders and focus rings; color formats and exit codes in the design skill, step 6). Then render and measure the result in one run, since code that passes every rule can still look wrong:
   ```bash
   d=$(mktemp -d) && node ${CLAUDE_PLUGIN_ROOT}/skills/ui-check/scripts/ui_check.mjs <url-or-file> --width 1280,390 --shot "$d/after.png"
   ```
   It writes `after-1280.png` and `after-390.png` and lists rendering findings (`--scheme light,dark`, `--wait-for`, and other options: ui-check skill, step 2). For a component that isn't a static file, use the URL of a dev server that is already running. In the shots, check for blocks with large empty areas, elements floating detached from what they describe, and ordered sets that lost their order. Then the first-impression check: in the widest shot, name the first three things the eye lands on; the first is the primary from step 2, or hierarchy needs another pass. Each area's purpose must be nameable at a glance; an area you can't name in a few words needs a heading, a label, or regrouping. Fix every P1 and P2 finding in what you changed, confirming each `[review]` finding in its shot first and dropping it when the layout intends it (ui-check step 3); list findings outside your change in the report. Exit 2 means it couldn't run (no Node 22+, no Chromium-based browser, or no running dev server): say so. For one element's hover or focus state, one component alone, or emulated preferences, use the screenshot script (options: design skill, step 7). Finally re-read every visible string you wrote or kept and fix anything awkward or vague.

5. **Report** in a few lines, only what the page doesn't show: behavior hits flagged instead of fixed, proof and copy you kept but flagged, `TODO`s for missing data (see "Don't invent data"), and checks that couldn't run. No per-principle change list or explanations; the diff and the page show those.

## The five principles

### 1. One flat accent, and color means something
**Tell:** gradient headers/buttons/text (`bg-gradient-to-*`, `from-* to-*`, `linear-gradient`), several competing brand-ish colors, gradient area fill under charts, glow.
**Fix:** surfaces are neutral; the header is the same surface as the page, separated by a 1px border. The accent appears only where it signals *act here* or *this is the main thing*: the primary CTA, the active nav item/tab, the hero metric's sparkline. Secondary charts use a neutral line with no gradient fill.
Semantic colors (red/amber/green) are allowed only for real status (error, warning, success), and muted (tinted text or subtle badge), not saturated pills everywhere.
**Why:** if everything is colorful, color can't point at anything.

### 2. Drop decoration; the number is the hero
**Tell:** an icon in a colored rounded square next to every card title, each card a different color, icons that repeat what the label already says, a thick colored left or right border as an accent bar on cards and callouts.
**Fix:** remove them (a side border stays only where it marks the current item or a quote). The label becomes small muted text; the value becomes the largest, heaviest thing in the card: the largest step of the project's type scale used there, `font-semibold tabular-nums`, tracking only from ~25px up. Icons stay where they aid recognition or action: navigation, icon buttons, search, file types. When they stay, use the project's icon library or inline SVG with one stroke, never emoji or Unicode glyphs (they render differently per platform). Size, stroke, library, and active state: `${CLAUDE_PLUGIN_ROOT}/skills/design/references/icons.md`.
**Why:** four colors on four metrics implies four categories that don't exist; the eye goes to the tile, not the value.

### 3. Hierarchy, not identical cards
**Tell:** a uniform grid of N separately floating, decorated cards with the same size, weight, and structure when their importance isn't equal (the 2×2 or 4-across KPI row is the classic).
Decide the primary, peers, and type rank with `references/hierarchy.md`.

**One primary action per view.** **Tell:** two or more solid accent buttons competing in one view, the same action visible twice at once (a "New project" button in the header and again in the toolbar), a row of equal buttons for actions of unequal frequency. **Fix:** one solid primary for the main task; the others become secondary (outline or ghost), and rarely used ones move into a "…" menu (build it with `${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/overlays.md`), keeping their handlers. Of two visible copies of one action, keep the one closest to where the user works. Don't hide an action the task needs on every visit behind a menu.

**Why:** equal weight forces the reader to decide what matters; the layout should already have decided, but only where importance really differs.

### 4. Borders and a radius scale; shadows only for things that float
**Tell:** `rounded-2xl`/`rounded-3xl` (16px+) and `shadow-*` on every card, input, and button; a hairline border and a large shadow on the same in-page element; glassmorphism (`backdrop-blur`, translucent cards) on in-page surfaces; colored glows. Glass on a sticky header, floating nav, or a layer over imagery can stay when it meets the glass rules in `${CLAUDE_PLUGIN_ROOT}/skills/design/references/materials.md`. In a project whose `DESIGN.md` records the `glass` style, glass panes in the page are its material, not a tell.
**Fix** (values for app/tool surfaces; marketing surfaces take theirs from the marketing profile, but the "not everything elevated" rule holds):
- In-page surfaces (cards, panels, tables) take no shadow. Removing a shadow doesn't mean adding a border: a surface gets a 1px hairline only where it meets a surface of the same value and space can't separate it (`cards.md`); a card on a tinted canvas, a group inside a panel, and a list inside a card take none. Dark: `border-white/10` on `bg-zinc-900`-ish; light: `border-zinc-200` on `bg-white`. Inputs, selects, and checkboxes need a 3:1 boundary instead: light `border-zinc-500`, dark `border-white/35` or stronger.
- After the pass, count the lines on the screen (`layout.md`, Grouping): a border inside a bordered surface, a divider beside a border, or a line between groups the gap already separates goes. Fewer lines than before is the expected result, not more.
- Dark themes follow `${CLAUDE_PLUGIN_ROOT}/skills/design/references/dark-mode.md`: near-black layers instead of `bg-black`, three alpha inks instead of pure white, a calmed accent with its foreground re-checked, dimmed photos.
- Radius: keep the project's scale when it has one (tokens, `DESIGN.md`, or one set of values the shared components use consistently), pills included. Fix only what breaks it: off-scale one-offs, a larger radius on a smaller element than its neighbour, non-concentric nested corners, side-by-side controls on different steps. With no scale, use **chip and badge 4px**, **button and input 6px** (`rounded-md`, the same step so they line up side by side), **card, panel, modal 12px** (`rounded-xl`). Nested corners are outer − padding; sides flush with an edge (bottom sheet, sidebar) lose their corners. For rings, media in cards, or nested panels, read `${CLAUDE_PLUGIN_ROOT}/skills/design/references/radius.md`.
- Shadow is reserved for layers that sit *above* the page: modal, popover, dropdown menu, toast, tooltip. Keep those shadows.
- Groups without an entity of their own (settings groups, form sections) lose their box and become sections, nested boxes flatten into spaced groups (a divider where space can't carry it), and card media shares one ratio. When you regroup or respace boxes, read `${CLAUDE_PLUGIN_ROOT}/skills/design/references/cards.md` and `${CLAUDE_PLUGIN_ROOT}/skills/design/references/layout.md`.
**Why:** shadow means "elevated"; when everything is elevated, nothing is.

### 5. Copy and numbers carry information
**Copy tell:** greetings ("Welcome back, Jordan 👋", "Good morning!", "Here's what's happening today"), emoji in headings, filler subtitles, generic placeholder text, status and error strings with "successfully", "Oops", or exclamation marks.
**Fix:** replace with a context line that tells the user what they are looking at: `Revenue · Aug 1 to Aug 31, 2026`, `Billing · Pro plan, renews Oct 12`. If nothing useful fits, remove the line. Status and error wording follows `${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/feedback.md` (Microcopy).

**Number tell:** every card shows the same `+12.5%` pill; deltas without a baseline; percentage changes on things that are already percentages; numbers that don't line up.
**Fix:**
- Deltas are specific and state the baseline: `+12.5% vs Jul`.
- Correct units: a change in a rate is in **percentage points**: conversion 3.4% → 3.8% is `+0.4 pt`, not `+11.8%`. Counts and money use `%` or absolute change.
- Delta color: neutral text by default. Only color by *good/bad* (not up/down) when it's unambiguous: churn going down is good, so a red "down" arrow is wrong. When in doubt, neutral.
- `tabular-nums` on all numeric values; right-align numeric table columns; consistent decimals per column. Compact values, currency symbols, and relative time follow the Numbers section of `${CLAUDE_PLUGIN_ROOT}/skills/design/references/typography.md`.
- Tables keep their column order, since users, saved views, and exports rely on it; restyle changes how cells look. Suggest a reorder in the report when a right-aligned numeric column sits mid-row before left-aligned text (it pinches the row) or status sits mid-row, and apply it only when the user asks. Status shows as a colored dot + text label rather than a saturated pill. Standalone tags outside tables are small 4px chips (`references/tailwind.md` §1).
- A sparkline on the primary metric only when the trend data already exists *and* the block has a natural slot (beside body content, or a full-width strip at the bottom). Never a new prop just to feed it, never in a compact cell; when in doubt, leave it out. Details in `references/tailwind.md` §3–4.

**Marketing copy tell:** eyebrows over every section, stock headlines ("Built for…", "The future of…"), several labels for one CTA intent, a bare "Learn more". **Fix:** the tells table in the marketing profile.

**Why:** filler copy and identical fake deltas are the fastest way a reader spots a template.

## Don't invent data
- **Hardcoded placeholder values:** fine to make them plausible and varied (and to add a small breakdown or baseline label).
- **Proof on marketing pages** (customer counts, percentages, ratings, testimonials): never add new ones. Keep existing ones and flag them in the report; replace them with a visible placeholder like `[customer count]` only if the user asks. For existing copy this replaces the marketing profile's placeholder rule.
- **Values from props/API/state:** don't fabricate new fields; restyle what exists. If the design wants something missing (a comparison baseline, a breakdown series for a sparkline), leave a clear `TODO` and mention it in the report. Add an optional prop only if the user asks.

## Don't overcorrect
- Keep status colors that encode real status; just mute them.
- Keep icons that help navigation or actions.
- Never propose a new typeface unless the user asks for a type change.
- Keep overlay shadows, and glass on floating layers that meets `materials.md`.
- If `DESIGN.md` records a style (premium, cinematic, playful, technical, glass, print, gallery), the values its Decisions set (a multi-hue palette, display weights, hard offset shadows, glass, a dark canvas, mono numbers) are intentional; remove only what its Avoid list or the tells outside it cover.
- Don't add a centered max-width container to an app shell that filled the width before.
- Don't flatten hierarchy that was already right, and don't restyle things outside the requested scope without saying so.
- Don't resize controls: heights, paddings, and gaps stay unless they are a tell (marketing-scale padding in a tool). Touch targets follow `${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/baseline.md` (Pointer and touch), which never grows a control; an icon-only button stays square (`${CLAUDE_PLUGIN_ROOT}/skills/design/references/icons.md`).
- Don't swap one value for another just because it differs from the defaults here: a project that uses 500 for labels, an 8px button radius, or pill buttons throughout made a choice, not a tell.

## References
- `references/tailwind.md`: class-level before/after mappings, a token setup snippet, the primary+secondary metric layout, and an inline SVG sparkline. Read it when applying fixes in Tailwind code.
- `references/hierarchy.md`: the order for deciding a state page, ordered peers, or one primary block, plus size and type rank. Read it for principle 3.
- `references/critique.md` for critique only; `references/requests.md` for a before/after, a named reference, or a score.
- The design skill's references named in the principles above, each read when its principle says so, plus `color.md` (its palette audit) before merging or replacing colors.
