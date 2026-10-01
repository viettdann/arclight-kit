# claude-ux-skills

Claude Code marketplace with one plugin, `arclight`.

## Which skill

| Situation | Skill |
| --- | --- |
| Nothing exists yet: new page, screen, or project; tokens, themes, dark mode, `DESIGN.md` | `arclight:design` |
| It exists and you want a new look (new style or direction), keeping content, URLs, and behavior | `arclight:redesign` |
| It exists and looks generated; keep the layout, remove the AI tells | `arclight:restyle` |
| Behavior and states: forms, tables, overlays, feedback, destructive actions, settings | `arclight:ui-interaction` (used alongside the others) |
| Start of any coding session: load the working rules (chat language, scope of a go-ahead, shared-worktree git, docs, comments, commits, migrations, UI) | `/arclight:arc` (user-invoked only) |

`design` combines a **profile** (tool or marketing: density, type size, depth) with an optional **style** (visual language):

| Style | For |
| --- | --- |
| `editorial-minimal` | Calm, document-like, Notion/Linear feel; tool or marketing |
| `soft-premium` | Premium consumer, soft radii, diffused depth, slow motion; marketing |
| `brutalist` | Swiss print or terminal, visible grid, zero ornament; tool or marketing |

No style named → the profile alone is the direction.

## Install

```bash
claude plugin marketplace add viettdann/claude-ux-skills
claude plugin install arclight@claude-ux-skills
```

Optional runtimes: `node` for `design`'s contrast checker, Node 22+ and Chrome, Chromium, or Edge for the screenshot script (`restyle` and `redesign` check the rendered page with it, `design` uses it when asked), `python3` for `restyle`'s tell scanner and `redesign`'s preserve check. Without them the skills still work and say what wasn't machine-checked.

## Changes

- **0.4.0**: New `arc` skill, invoked once per session with `/arclight:arc`, carrying the working rules shared across the arclight projects' CLAUDE.md files so each project keeps only its own facts. Adds three rules those files lacked: an answer is not a go-ahead, a go-ahead covers everything recommended earlier that wasn't dropped, and an explicit command is the confirmation (no re-asking, no backup step). `disable-model-invocation` keeps it out of automatic triggering.
- **0.3.2**: From a transifyr.app/buy/ eval, where runs with the skills took about 1.7× as long as without, partly because runs wrote their own screenshot and color-conversion scripts. New `design/scripts/screenshot.mjs` screenshots any width over the DevTools protocol (Chrome's `--screenshot` flag can't go below ~500px), several widths per call, `--full`, `--eval`, serves local files itself (`--root` for root-relative assets), and prints an `overflow` line (exit 1) when the page scrolls sideways; `restyle` step 5 uses it instead of the old Chrome command. `redesign` step 7 gains a rendered-page check with it, which adds a step rather than saving time. `design`, `restyle`, and `redesign` say `contrast.mjs` takes colors as written (hex, `rgb()`, `oklch()`) so runs stop writing converters. `restyle` drops the audit table (`principle | file:line | tell | fix`) and goes from the scanner output to edits; `redesign`'s audit becomes working notes. Both reports list only what the page doesn't show: flagged behavior and proof, changes to protected items, placeholders, and checks that couldn't run.
- **0.3.1**: Consistency and correctness pass from an isolated 0.2.0 vs 0.3.0 eval. Cross-skill paths use `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/` (the documented variable for files shared between a plugin's skills), and ui-interaction says where the design references live. `overlays.md` is split into `overlays.md` (modals, menus, context menus, tooltips), `navigation.md` (tabs, navigation, scroll restoration, sticky headers), and `gestures.md` (drag, resize, swipe, pull to refresh), so a modal no longer loads gesture rules. Fixed contradictions: typed-name confirm and empty filter chips use `aria-disabled` instead of `disabled`; touch targets are 44px under `pointer: coarse` and 24px otherwise; the tool accent no longer covers focus; weights are 400/600 everywhere; soft-premium full-bleed bands stay square; brutalist and editorial-minimal say what they override. restyle: input borders at 3:1, value sizes from the type scale, a `code` group for behavior tells (flagged, not changed), a contrast step, conditional pointers to design references, the redesign ask-once rule, and no em dashes; `tailwind.md` uses the project's primary token, drops radius overrides of Tailwind defaults, and fixes an example that failed contrast. design: the design read opens the summary, the Checks of loaded references run before it, the Tailwind v4 `text-text-muted` naming trap, easing names that don't shadow Tailwind's, and alpha inks in the dark token example. Scripts: `scan_tells.py` and `preserve_check.py` exit 2 on a missing path instead of reporting clean, `aria-disabled` and awaited clipboard writes are no longer flagged, build output and minified files are skipped, weight 500 is flagged; `preserve_check.py` fixes meta-description parsing; `contrast.mjs` accepts `rgb()` and clamps alpha.
- **0.3.0**: `design` gains `typography.md` (scale, inks, weights, long text, numbers) and `radius.md` (roles, concentric nesting, edge-flush corners), loaded for every new surface or token work, plus `cards.md`, `avatars.md`, and `dark-mode.md` loaded when the screen needs them. Tool radius is sm 4 / md 6 / lg 12. The marketing profile sets radius from a per-element table (band 16px, card 12px, button and input 8px, chip and tag 6px, full-bleed bands square, no pills by default) instead of a 16–24px range; styles list only the rows they override (`soft-premium` raises bands, large cards, and the bezel shell to 16–24px and keeps pills for the primary CTA and floating nav; `editorial-minimal` goes smaller with no pills). `ui-interaction` adds `settings.md` (apply model and save bar, settings search, modified state, danger zone), an inline edit section, context menus, tables on narrow widths, selection that names its scope, badges, copy to clipboard, scroll restoration, sticky headers, resize handles, pull to refresh, and "explain, don't disable" in the baseline. The `restyle` scanner adds rules for pure-black surfaces, pulsing dots, zebra stripes, rounded edge-flush sheets, random colors, hand-rolled compact numbers, un-awaited clipboard writes, scroll-to-top, mouse-event drags, `disabled` for validity or busy, strings cut in JS, `break-all`, Enter without `isComposing`, and page-wide context menu blocking.
- **0.2.1**: Skill paths use `${CLAUDE_SKILL_DIR}` instead of a `<skill-dir>` placeholder. `redesign` snapshots the source folder to a temp dir before editing instead of using `git stash`, lists classes that tests and analytics use during the audit, updates an existing `DESIGN.md` with the new direction, and gives full paths to the contrast script and the ui-interaction skill. `design` parses the style argument first, runs the marketing tell scan from its workflow, and reports contrast pairs that still fail. `restyle` decides hierarchy in a fixed order (state page, ordered peers, primary or equal), leaves a `TODO` instead of adding props, and writes the audit as a fixed-column table. `ui-interaction` splits verification into steps, defines when to skip the state note, and drops rules that repeat the always-loaded baseline.
- **0.2.0**: `ui-visual` renamed to `design`, with styles (`editorial-minimal`, `soft-premium`, `brutalist`) on top of the tool and marketing profiles. New `redesign` skill with `preserve_check.py`. Marketing profile extended (design read, layout, imagery, copy tells); scanner covers marketing and code tells.
