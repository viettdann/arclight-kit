# Quality review

Review the changes for hacky patterns. Category `quality` throughout.

1. **Redundant state**: state duplicating existing state, cached values that could be derived, observers or effects that could be direct calls
2. **Parameter sprawl**: new parameters bolted onto a function instead of generalizing or restructuring what is there
3. **Copy-paste with slight variation**: near-duplicate blocks that should be unified behind a shared abstraction. Flag only when a fix to one block would need the same fix in the other; blocks that change for different reasons stay separate
4. **Leaky abstractions**: internal details exposed that should stay encapsulated, or existing abstraction boundaries broken
5. **Stringly-typed code**: raw strings where the codebase already has constants, string-union enums, or branded types
6. **Placeholders**: `// ...`, `// rest of code`, `// implement here`, `// similar to above`, a bare `...` for omitted code, stub bodies, or a `TODO` the user or active skill did not ask for. Fix: write the missing code.
7. **Unsearchable code**: a new exported name that is a bare generic verb or noun (`validate`, `diff`, `handler`), a new synonym for a term the codebase already spells one way, an event name, flag, error code, or log key assembled by interpolation, an error message without a literal prefix that greps back to the throw site, a name the diff left stale after changing its behavior. Fix: rename or write the literal in full; never rename a serialized or string-based contract name.
8. **Leftovers**: debug output (`console.log`, `print`, `debugger`, `Debug.WriteLine`) and new suppressions added to get green (`any`, `as unknown as`, `@ts-ignore`, `# type: ignore`, `#pragma warning disable`, `!` null-forgiving). Fix: remove the output; fix the type instead of suppressing it.
9. **Speculative abstraction**: an interface with one implementation, a factory or strategy for two branches, a parameter or option no caller sets, config for a value that never changes, scaffolding for a later feature no task asks for. Fix: inline or delete.
10. **Defensive code out of place**: a try/catch, null check, or fallback that the surrounding code in the same file doesn't use, guarding a value its callers already validate or its type already guarantees. Fix: remove it; checks at a trust boundary stay.
