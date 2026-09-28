# claude-ux-skills

Claude Code marketplace with one plugin, `arclight`.

## Which skill

| Situation | Skill |
| --- | --- |
| Nothing exists yet: new page, screen, or project; tokens, themes, dark mode, `DESIGN.md` | `arclight:design` |
| It exists and you want a new look (new style or direction), keeping content, URLs, and behavior | `arclight:redesign` |
| It exists and looks generated; keep the layout, remove the AI tells | `arclight:restyle` |
| Behavior and states: forms, tables, overlays, feedback, destructive actions | `arclight:ui-interaction` (used alongside the others) |

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

Optional runtimes: `node` for `design`'s contrast checker, `python3` for `restyle`'s tell scanner and `redesign`'s preserve check. Without them the skills still work and say what wasn't machine-checked.

## Changes

- **0.2.1**: Skill paths use `${CLAUDE_SKILL_DIR}` instead of a `<skill-dir>` placeholder. `redesign` snapshots the source folder to a temp dir before editing instead of using `git stash`, lists classes that tests and analytics use during the audit, updates an existing `DESIGN.md` with the new direction, and gives full paths to the contrast script and the ui-interaction skill. `design` parses the style argument first, runs the marketing tell scan from its workflow, and reports contrast pairs that still fail. `restyle` decides hierarchy in a fixed order (state page, ordered peers, primary or equal), leaves a `TODO` instead of adding props, and writes the audit as a fixed-column table. `ui-interaction` splits verification into steps, defines when to skip the state note, and drops rules that repeat the always-loaded baseline.
- **0.2.0**: `ui-visual` renamed to `design`, with styles (`editorial-minimal`, `soft-premium`, `brutalist`) on top of the tool and marketing profiles. New `redesign` skill with `preserve_check.py`. Marketing profile extended (design read, layout, imagery, copy tells); scanner covers marketing and code tells.
