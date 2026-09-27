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

- **0.2.0**: `ui-visual` renamed to `design`, with styles (`editorial-minimal`, `soft-premium`, `brutalist`) on top of the tool and marketing profiles. New `redesign` skill with `preserve_check.py`. Marketing profile extended (design read, layout, imagery, copy tells); scanner covers marketing and code tells.
