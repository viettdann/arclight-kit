# Restyle detailed instructions

Resolve all relative paths in this reference from the parent skill directory containing `SKILL.md`, not from `references/`.

## The five principles

### 1. One flat accent, and color means something
**Tell:** gradient headers/buttons/text (`bg-gradient-to-*`, `from-* to-*`, `linear-gradient`), several competing brand-ish colors, gradient area fill under charts, glow.
**Fix:** surfaces are neutral; the header is the same surface as the page, separated by a 1px border. The accent appears only where it signals *act here* or *this is the main thing*: the primary CTA, the active nav item/tab, the hero metric's sparkline. Secondary charts use a neutral line with no gradient fill.
Semantic colors (red/amber/green) are allowed only for real status (error, warning, success), and muted (tinted text or subtle badge), not saturated pills everywhere.
**Why:** if everything is colorful, color can't point at anything.

### 2. Drop decoration; the number is the hero
**Tell:** an icon in a colored rounded square next to every card title, each card a different color, icons that repeat what the label already says, a thick colored left or right border as an accent bar on cards and callouts.
**Fix:** remove them (a side border stays only where it marks the current item or a quote). The label becomes small muted text; the value becomes the largest, heaviest thing in the card: the largest step of the project's type scale used there, `font-semibold tabular-nums`, tracking only from ~25px up. Icons stay where they aid recognition or action: navigation, icon buttons, search, file types. When they stay, they should be real icons (the project's icon library, or inline SVG with a consistent stroke), not emoji or Unicode glyphs like ☺ ⚙ 🔔, which render differently per platform and look placeholder.
**Why:** four colors on four metrics implies four categories that don't exist; the eye goes to the tile, not the value.

### 3. Hierarchy, not identical cards
**Tell:** a uniform grid of N separately floating, decorated cards with the same size, weight, and structure when their importance isn't equal (the 2×2 or 4-across KPI row is the classic).
**Decide in this order** (a billing page usually matches the first two):

1. **Is this a state page?** When a page exists to show the user's current situation (billing, subscription, account, usage), that state is the primary: put a summary block at the top with the plan/tier name and price (or the key quantity) large, plus the next relevant fact (renewal date, next invoice) and the main action. This is what the user came to see. Don't fold it into a subtitle line. Then apply 2 or 3 to what sits below it.
2. **Are the items ordered peers?** Items that are *compared against each other* and have a natural order (pricing tiers, steps, versions, time periods) keep their sequence side by side (Starter | Pro | Enterprise), because position itself tells the reader where each sits. Mark the current/recommended one in place (accent border or small label) instead of pulling it out of the row; replacing the comparison with a list is not OK.
3. **Otherwise, does the primary have more to say?** Hierarchy needs substance. A primary block is justified only when the most important item carries *real extra content* the others don't (a breakdown, a chart, a target, an absolute baseline value) already present in the data.
   - **Yes** → one primary block, the rest secondary. The primary gets the large value plus that extra content; secondaries are compact (label, value, delta), stacked beside it or in a row beneath.
   - **No**: every item is just label + value + delta → keep them equal. A single bordered strip divided into cells (`divide-x`, or `gap-px` over a border-colored background) is the honest layout; put the most important metric first, since reading order already carries priority. What made the original look generated was the decoration (tiles, shadows, colors, fake deltas), not the equal sizes; enlarging one cell with nothing to fill it only adds empty space.

**Size follows content, and the row ends flush.** A primary is as big as its content, never padded out with empty space. Blocks side by side share top and bottom edges: stacked secondaries divide the primary's height between them (`grid auto-rows-fr`, or `flex-1` on each), so neither column ends with blank space under it.

**Type carries the rest of the hierarchy.** Sizes come from one scale, weights 400 and 600 only, and rank inside a row comes from text color (`text`, `text-muted`, `text-subtle`), not another size. Text slots survive long values: truncate in CSS with `min-w-0` on the flex items, cut the middle of emails and file names, `overflow-wrap: anywhere` for unbroken strings. When you change the type scale or fix truncation, read `../design/references/typography.md` (Size scale, Long text). Bold on every label and a new size for every element are the type versions of identical cards. Display tracking stays at -0.04em or looser, body text is never justified, and body copy, lists, and long text stay left-aligned even when a heading is centered.

**One primary action per view.** **Tell:** two or more solid accent buttons competing in one view, the same action visible twice at once (a "New project" button in the header and again in the toolbar), a row of equal buttons for actions of unequal frequency. **Fix:** one solid primary for the main task; the others become secondary (outline or ghost), and rarely used ones move into a "…" menu (build it with `../ui-interaction/references/overlays.md`), keeping their handlers. Of two visible copies of one action, keep the one closest to where the user works. Don't hide an action the task needs on every visit behind a menu.

**Why:** equal weight forces the reader to decide what matters; the layout should already have decided, but only where importance really differs.

### 4. Borders and a radius scale; shadows only for things that float
**Tell:** `rounded-2xl`/`rounded-3xl` (16px+) and `shadow-*` on every card, input, and button; a hairline border and a large shadow on the same in-page element; glassmorphism (`backdrop-blur`, translucent cards) on in-page surfaces; colored glows. Glass on a sticky header, floating nav, or a layer over imagery can stay when it meets the glass rules in `../design/references/materials.md`.
**Fix** (values for app/tool surfaces; marketing surfaces take theirs from the marketing profile, but the "not everything elevated" rule holds):
- In-page surfaces (cards, panels, tables): 1px hairline border, no shadow. Dark: `border-white/10` on `bg-zinc-900`-ish; light: `border-zinc-200` on `bg-white`. Inputs, selects, and checkboxes need a 3:1 boundary instead: light `border-zinc-500`, dark `border-white/35` or stronger.
- Dark themes follow `../design/references/dark-mode.md`: `bg-black` becomes a near-black with lighter layers, pure-white text becomes three alpha inks, a saturated accent is calmed (and its foreground re-checked), photos are dimmed.
- Radius scale, smaller and consistent: **chip and badge 4px**, **button and input 6px** (`rounded-md`, the same step so they line up side by side), **card, panel, modal 12px** (`rounded-xl`). Badges may stay `rounded-full` if the project already uses pill badges, but only on one line. Nested corners are outer − padding; sides flush with an edge (bottom sheet, sidebar) lose their corners. For rings, media in cards, or nested panels, read `../design/references/radius.md`.
- Shadow is reserved for layers that sit *above* the page: modal, popover, dropdown menu, toast, tooltip. Keep those shadows.
- Groups without an entity of their own (settings groups, form sections) lose their box and become sections, nested boxes flatten into dividers, and card media shares one ratio. When you regroup boxes, read `../design/references/cards.md`.
**Why:** shadow means "elevated." When everything is elevated, nothing is, and the page looks soft and templated.

### 5. Copy and numbers carry information
**Copy tell:** greetings ("Welcome back, Jordan 👋", "Good morning!", "Here's what's happening today"), emoji in headings, filler subtitles, generic placeholder text.
**Fix:** replace with a context line that tells the user what they are looking at: `Revenue · Aug 1 to Aug 31, 2026`, `Billing · Pro plan, renews Oct 12`. If nothing useful fits, remove the line.

**Number tell:** every card shows the same `+12.5%` pill; deltas without a baseline; percentage changes on things that are already percentages; numbers that don't line up.
**Fix:**
- Deltas are specific and state the baseline: `+12.5% vs Jul`.
- Correct units: a change in a rate is in **percentage points**: conversion 3.4% → 3.8% is `+0.4 pt`, not `+11.8%`. Counts and money use `%` or absolute change.
- Delta color: neutral text by default. Only color by *good/bad* (not up/down) when it's unambiguous: churn going down is good, so a red "down" arrow is wrong. When in doubt, neutral.
- `tabular-nums` on all numeric values; right-align numeric table columns; consistent decimals per column. Compact values, currency symbols, and relative time follow the Numbers section of `../design/references/typography.md`.
- Tables: the right-aligned numeric column goes **last**, flush with the right edge (right-aligned followed by left-aligned pinches the row in the middle). Status sits at an **edge**, never mid-row: leading column by default (`Status | Customer | Date | Amount`), shown as a colored dot + text label rather than a pill. Standalone tags outside tables are small 4px chips (`references/tailwind.md` §1).
- A sparkline on the primary metric only when the trend data already exists *and* the block has a natural slot (beside body content, or a full-width strip at the bottom). Never a new prop just to feed it, never in a compact cell; when in doubt, leave it out. Details in `references/tailwind.md` §3–4.

**Marketing copy tell:** an uppercase eyebrow over every section, numbered eyebrows (`001 · Capabilities`), em dashes as separators, several labels for one CTA intent ("Get started", "Try free", "Sign up"), "Scroll to explore", stock headlines ("Built for…", "Meet your new…", "The future of…"), a bare "Learn more" as the CTA. **Fix:** see the tells table in the marketing profile.

**Why:** filler copy and identical fake deltas are the fastest way a reader spots a template.

## Don't invent data
- **Hardcoded placeholder values:** fine to make them plausible and varied (and to add a small breakdown or baseline label).
- **Proof on marketing pages** (customer counts, percentages, ratings, testimonials): never add new ones. Keep existing ones and flag them in the report; replace them with a visible placeholder like `[customer count]` only if the user asks. For existing copy this replaces the marketing profile's placeholder rule.
- **Values from props/API/state:** don't fabricate new fields; restyle what exists. If the design wants something missing (a comparison baseline, a breakdown series for a sparkline), leave a clear `TODO` and mention it in the report. Add an optional prop only if the user asks, since step 3 keeps props unchanged.

## Don't overcorrect
- Keep status colors that encode real status; just mute them.
- Keep icons that help navigation or actions.
- Keep overlay shadows, and glass on floating layers that meets `materials.md`.
- If `DESIGN.md` records a style (premium, cinematic, playful), the values its Decisions set (a multi-hue palette, display weights, hard offset shadows, glass) are intentional; remove only what its Avoid list or the tells outside it cover.
- Don't add a centered max-width container to an app shell that filled the width before.
- Don't flatten hierarchy that was already right, and don't restyle things outside the requested scope without saying so.
