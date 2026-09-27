# claude-ux-skills

Claude Code marketplace with one plugin, `arclight`:

| Skill | Use for |
| --- | --- |
| `arclight:ui-visual` | Visual direction, design tokens, dark mode, `DESIGN.md` |
| `arclight:ui-interaction` | Behavior and states: forms, tables, overlays, feedback, destructive actions |
| `arclight:restyle` | De-templating an existing screen that looks AI-generated |

## Install

```bash
claude plugin marketplace add viettdann/claude-ux-skills
claude plugin install arclight@claude-ux-skills
```

Optional runtimes: `node` for `ui-visual`'s contrast checker, `python3` for `restyle`'s scanner. Without them the skills still work and say what wasn't machine-checked.
