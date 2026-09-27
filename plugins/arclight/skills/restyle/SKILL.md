---
name: restyle
description: De-AI a generic, template-looking UI. Audits the code for "AI tells" (gradients, decorative icon tiles, identical card grids, big radius + drop shadow on everything, greetings/emoji, fake identical deltas, unaligned numbers) and rewrites it into a restrained, information-first design with one meaningful accent, clear hierarchy, borders instead of shadows, and honest copy. Use this whenever the user wants to restyle, clean up, polish, "make less generic", "make it look less AI", "look more professional/pro/like Linear/Stripe", de-template, or critique the visual design of an existing dashboard, admin panel, settings page, landing section, or any app UI — especially Tailwind/React/HTML code — even if they don't say the word "restyle". Also use when reviewing freshly AI-generated UI before shipping. The layout and structure stay; for a new visual language or style on an existing product use redesign, and for a screen that doesn't exist yet use design.
argument-hint: "[file or folder]"
---

# Restyle: remove the AI tells

Generated UIs look generic for a consistent reason: every visual choice is decoration instead of information. Gradients, rainbow icon tiles, equal-weight cards, soft shadows on everything, and friendly filler copy all say nothing. The fix is one rule applied five ways:

> **Every visual decision must carry information. If it says nothing, remove it. If it stays, it must mean something.**

The result should still be polished — this is restraint, not brutalism. Keep the layout's purpose, data bindings, behavior, and accessibility intact.

## Workflow

1. **Find the UI.** Locate the files that render the target screen (components, pages, templates, global CSS, `tailwind.config.*`). Run the scanner to get a first list of candidates:
   ```bash
   python3 <skill-dir>/scripts/scan_tells.py <path-to-src-or-file>
   ```
   If Python isn't available, skip the scan and read the code. It is a heuristic grep, not a verdict — a `shadow-lg` on a modal is correct, a `shadow-lg` on a card is a tell. Read the code yourself too; hierarchy and copy problems don't show up in a grep.

2. **Decide before editing:**
   - **The profile.** App/tool surface (dashboard, admin, settings, billing) or marketing surface (landing, pricing page, portfolio, storefront)? The five principles apply to both, but on a marketing surface the radius and elevation values come from the design marketing profile (`<skill-dir>/../design/references/profile-marketing.md`: 16–24px large cards, tinted layered shadows where lift means something) instead of principle 4's tool values, and its layout, imagery, and copy tells join the audit.
   - **The primary thing on the page.** What is this screen for? On a revenue dashboard it's revenue; on a billing page it's the current plan; on a settings page it's the form. This drives hierarchy (principle 3) and where the accent goes (principle 1).
   - **The accent.** Reuse the existing brand color if there is one (look in tailwind config / CSS vars / the primary button). Otherwise pick one flat color that fits the product, not a house default. Everything else is neutral.

3. **Write the audit** (in the user's language), grouped by principle. For each finding: `file:line` → what it is → the fix. Keep it scannable — a table works well. This is what teaches the user *why*, so include the one-line reason per principle.

4. **Apply the fixes.** Prefer fixing at the source of truth: if radius/shadow/colors are set in a shared component or config, change it there rather than patching every usage. Don't change data fetching, props, event handlers, or routes. Also keep, unless the user asks: URLs and anchor ids, nav labels, form field `name`s and order, ids or labels that analytics may track, the logo, and legal or consent copy. Restyling changes how it looks, not what it says or where it lives.

5. **Verify.** Re-run the scanner and confirm the remaining hits are intentional (overlay shadows, semantic status colors). Then look at the rendered result — code that passes every rule can still look wrong. If a browser or headless Chrome is available, screenshot it (`"<chrome>" --headless=new --screenshot=out.png --window-size=1280,1000 --virtual-time-budget=5000 file:///abs/path.html`) and check specifically: blocks with large empty areas, elements floating detached from what they describe, and ordered sets that lost their order. Finally re-read every visible string you wrote or kept (headings, labels, buttons, captions) and fix anything awkward or vague.

6. **Report** briefly: what changed per principle, and anything you flagged instead of changed (see "Don't invent data").

## The five principles

### 1. One flat accent, and color means something
**Tell:** gradient headers/buttons/text (`bg-gradient-to-*`, `from-* to-*`, `linear-gradient`), several competing brand-ish colors, gradient area fill under charts, glow.
**Fix:** surfaces are neutral; the header is the same surface as the page, separated by a 1px border. The accent appears only where it signals *act here* or *this is the main thing*: the primary CTA, the active nav item/tab, the hero metric's sparkline. Secondary charts use a neutral line with no gradient fill.
Semantic colors (red/amber/green) are allowed only for real status (error, warning, success) — and should be muted (tinted text or subtle badge), not saturated pills everywhere.
**Why:** if everything is colorful, color can't point at anything.

### 2. Drop decoration; the number is the hero
**Tell:** an icon in a colored rounded square next to every card title, each card a different color, icons that repeat what the label already says.
**Fix:** remove them. The label becomes small muted text; the value becomes the largest, heaviest thing in the card (`text-3xl`–`text-5xl font-semibold tracking-tight tabular-nums`). Icons stay where they aid recognition or action: navigation, icon buttons, search, file types — and when they stay, they should be real icons (the project's icon library, or inline SVG with a consistent stroke), not emoji or Unicode glyphs like ☺ ⚙ 🔔, which render differently per platform and look placeholder.
**Why:** four colors on four metrics implies four categories that don't exist; the eye goes to the tile, not the value.

### 3. Hierarchy, not identical cards
**Tell:** a uniform grid of N separately floating, decorated cards with the same size, weight, and structure when their importance isn't equal (the 2×2 or 4-across KPI row is the classic).
**First ask: does the primary have more to say?** Hierarchy needs substance. A primary block is justified only when the most important item carries *real extra content* the others don't — a breakdown, a chart, a target, an absolute baseline value — already present in the data.
- **Yes** → one primary block, the rest secondary. The primary gets the large value plus that extra content; secondaries are compact (label, value, delta), stacked beside it or in a row beneath.
- **No** — every item is just label + value + delta → keep them equal. A single bordered strip divided into cells (`divide-x`, or `gap-px` over a border-colored background) is the honest layout; put the most important metric first, since reading order already carries priority. What made the original look generated was the decoration (tiles, shadows, colors, fake deltas), not the equal sizes. Enlarging one cell with nothing to fill it creates empty space that looks worse than the grid did, at every width.

**Size follows content, and the row ends flush.** A primary is as big as its content, never padded out with empty space. Blocks side by side share top and bottom edges: stacked secondaries divide the primary's height between them (`grid auto-rows-fr`, or `flex-1` on each), so neither column ends with blank space under it. Check the rendered result before settling.

**Ordered peers stay in order.** "One primary + N secondary" is for items of *unequal importance*. Items that are *compared against each other* and have a natural order — pricing tiers, steps, versions, time periods — keep their sequence side by side (Starter | Pro | Enterprise), because position itself tells the reader where each sits. Mark the current/recommended one in place (accent border or small label) instead of pulling it out of the row; replacing the comparison with a list is not OK.

**State pages lead with the state.** When a page exists to show the user's current situation — billing, subscription, account, usage — that state is the primary: put a summary block at the top with the plan/tier name and price (or the key quantity) large, plus the next relevant fact (renewal date, next invoice) and the main action. This is what the user came to see. Don't fold it into a subtitle line. The ordered comparison (tiers) sits below it.

**Why:** equal weight forces the reader to decide what matters; the layout should already have decided — but only where importance really differs.

### 4. Borders and a radius scale; shadows only for things that float
**Tell:** `rounded-2xl`/`rounded-3xl` (16px+) and `shadow-*` on every card, input, and button; glassmorphism (`backdrop-blur`, translucent cards) on in-page surfaces; colored glows.
**Fix** (values for app/tool surfaces; marketing surfaces take theirs from the marketing profile, but the "not everything elevated" rule holds):
- In-page surfaces (cards, panels, tables, inputs): 1px subtle border, no shadow. Dark: `border-white/10` on `bg-zinc-900`-ish; light: `border-zinc-200` on `bg-white`.
- Radius scale, smaller and consistent: **button 6px** (`rounded-md`), **input 8px** (`rounded-lg`), **card 12px** (`rounded-xl`). Badges `rounded-md` or `rounded-full` — pick one. Nested elements never have a larger radius than their container.
- Shadow is reserved for layers that sit *above* the page: modal, popover, dropdown menu, toast, tooltip. Keep those shadows.
**Why:** shadow means "elevated." When everything is elevated, nothing is, and the page looks soft and templated.

### 5. Copy and numbers carry information
**Copy tell:** greetings ("Welcome back, Jordan 👋", "Good morning!", "Here's what's happening today"), emoji in headings, filler subtitles, generic placeholder text.
**Fix:** replace with a context line that tells the user what they are looking at: `Revenue · Aug 1 to Aug 31, 2026`, `Billing · Pro plan, renews Oct 12`. If nothing useful fits, remove the line.

**Number tell:** every card shows the same `+12.5%` pill; deltas without a baseline; percentage changes on things that are already percentages; numbers that don't line up.
**Fix:**
- Deltas are specific and state the baseline: `+12.5% vs Jul`.
- Correct units: a change in a rate is in **percentage points** — conversion 3.4% → 3.8% is `+0.4 pt`, not `+11.8%`. Counts and money use `%` or absolute change.
- Delta color: neutral text by default. Only color by *good/bad* (not up/down) when it's unambiguous — churn going down is good, so a red "down" arrow is wrong. When in doubt, neutral.
- `tabular-nums` on all numeric values; right-align numeric table columns; consistent decimals per column.
- Tables: the right-aligned numeric column goes **last**, flush with the right edge (right-aligned followed by left-aligned pinches the row in the middle). Status sits at an **edge**, never mid-row: leading column by default (`Status | Customer | Date | Amount`), shown as a colored dot + text label rather than a pill. Pills stay for standalone tags outside tables.
- A sparkline on the primary metric only when the trend data already exists *and* the block has a natural slot (beside body content, or a full-width strip at the bottom). Never a new prop just to feed it, never in a compact cell; when in doubt, leave it out. Details in `references/tailwind.md` §4–5.

**Marketing copy tell:** an uppercase eyebrow over every section, numbered eyebrows (`001 · Capabilities`), em dashes as separators, several labels for one CTA intent ("Get started", "Try free", "Sign up"), "Scroll to explore". **Fix:** see the tells table in the marketing profile.

**Why:** filler copy and identical fake deltas are the fastest way a reader spots a template.

## Don't invent data
When values are hardcoded placeholders, it's fine to make them plausible and varied (and to add a small breakdown or baseline label). The exception is proof on marketing pages (customer counts, percentages, ratings, testimonials): never add new ones; replace invented ones with a visible placeholder like `[customer count]` only if the user wants that, otherwise keep them and flag them. When values come from props/API/state, don't fabricate new fields: restyle what exists, and if the design wants something missing (a comparison baseline, a breakdown series for a sparkline), add an optional prop or leave a clear `TODO` and mention it in the report.

## Don't overcorrect
- Keep status colors that encode real status; just mute them.
- Keep icons that help navigation or actions.
- Keep overlay shadows.
- Don't add a centered max-width container to an app shell that filled the width before.
- Don't flatten hierarchy that was already right, and don't restyle things outside the requested scope without saying so.

## References
- `references/tailwind.md` — class-level before/after mappings, a token setup snippet, the primary+secondary metric layout, and an inline SVG sparkline. Read it when applying fixes in Tailwind code.
- `<skill-dir>/../design/references/profile-marketing.md` — layout, imagery, and copy tells plus values for marketing surfaces. Read it when the profile is marketing.
- `scripts/scan_tells.py` — heuristic scanner; `--help` for options.
