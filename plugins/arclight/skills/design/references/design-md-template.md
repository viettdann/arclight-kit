# DESIGN.md template

Write this file at the repo root. It records decisions and their reasons; exact values live in the token file it points to, so there is one source of truth. Keep it under ~150 lines so every session can read it in full.

```markdown
# Design

## Product
- What it is, who uses it, the most frequent task, the costliest mistake a user can make.

## Surfaces, profiles, styles
| Surface | Path/route | Profile | Style |
| --- | --- | --- | --- |
| App | src/app/(app) | tool | none |
| Marketing | src/app/(marketing) | marketing | editorial-minimal |

## Tokens
- Source: `src/styles/tokens.css` (or Tailwind `@theme` file). Components use semantic tokens only.
- Themes: light, dark (or light only, and why).

## Decisions
- Accent: <color and why it fits the product>.
- Type: <families, base size per profile, scale>.
- Radius: <scale and the personality it gives>.
- Depth: <surface values vs shadows, per profile>.
- Motion: <duration range, spring allowed or not>.
- Icons: <library, stroke, default size>.

## Behavior conventions
- Destructive actions: <undo vs confirm policy>.
- Toasts: <position, durations>.
- Forms: <validation timing, label placement>.
- Inline edit: blur commits (ui-interaction default); list exceptions.

## Components
- Library: <shadcn/Radix/own>, location of primitives, rule for when to create a new component.

## Don'ts
- Project-specific things that have gone wrong before.
```
