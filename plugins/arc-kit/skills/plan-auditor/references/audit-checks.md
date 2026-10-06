# Plan Auditor detailed instructions

Resolve all relative paths in this reference from the parent skill directory containing `SKILL.md`, not from `references/`.

### Phase 2: Codebase reality check

This is the phase that carries the audit. The plan claims things about the codebase; verify them.

**Choosing depth.** A depth the user asked for always wins. Otherwise start at shallow and escalate on the criteria below, taking the deepest criterion that fires. When the scope is large or ambiguous enough that the right depth isn't obvious, ask the user.

**Shallow (default):**

- Verify that referenced files and directories exist
- Check that referenced functions, classes, and exports are real and have the expected signatures
- Confirm import paths are correct
- Validate that referenced config keys, env vars, or constants exist

**Escalate to medium when:**

- The plan modifies shared code used by three or more consumers
- The plan touches authentication, authorization, or data integrity
- The plan involves database schema changes
- Multiple steps depend on the same assumption about system behavior

**Medium adds:**

- Trace call chains to verify the plan's understanding of data flow
- Check for other code that depends on what the plan modifies (impact radius)
- Verify version compatibility of referenced dependencies
- Look for existing tests that would break
- Run `git log --oneline -i --grep=revert -- <touched paths>`; a step that redoes a reverted approach is FLAG, citing the revert commit

**Escalate to deep when:**

- The plan involves concurrent or async behavior and makes ordering assumptions
- The plan claims backward compatibility
- The change surface spans five or more files across different modules

**Deep adds:**

- Run existing tests to establish the current baseline
- Trace error handling paths
- Check for race conditions or state management issues the plan ignores
- Verify that rollback is actually possible as claimed

### Phase 3: Gap analysis

With codebase context loaded, evaluate:

**Completeness gaps:**

- Steps that are implied but not stated
- Error handling or rollback not addressed
- Migration or deployment steps missing
- Tests not mentioned

**Assumption gaps:**

- Things the plan takes for granted that aren't verified
- "This should work because..." without evidence
- Circular reasoning: a justification that rests on the plan's own assumptions
- Implicit ordering dependencies between steps

**Risk assessment:**

- Which steps are irreversible
- The failure impact scope if a step fails mid-way
- Safer alternatives the plan didn't consider

**Design risks:**

- For each failure path the plan introduces (network or external call, timeout, invalid input, partial write), answer: handled? tested? does the user see it? logged? A path that is unhandled, untested, and silent is FAIL; a new external call without a timeout counts as unhandled
- Each new endpoint or handler applies the same authentication, authorization, and input validation as its sibling routes
- Each new cache names what invalidates it
- A step that builds what an installed dependency or existing module already provides is FLAG; name the existing one
- A schema change stays compatible with the code still running during deploy

**Proportionality check:**

- Whether the complexity of the solution is proportional to the problem
- Whether simpler approaches achieve the same goal
- Whether the plan solves the stated problem or a different, bigger one
- A plan touching 8 or more files, or adding 2 or more new services, modules, or packages, passes only after answering "can fewer moving parts do this?"; an unanswered case is FLAG

## Behavioral guidelines

- Do not default to agreement. Your role is to surface problems, not confirm what the user already believes.
- Be specific. "This might have issues" is useless. "Step 3 references `utils/auth.ts` which doesn't export `validateToken`; the actual export is `verifyToken` with a different signature (takes 2 args, not 1)" is useful.
- Distinguish between "this is wrong" and "this is a choice I'd make differently". The former is an audit finding; the latter is an opinion, and label it as one.
- When you find a FAIL, suggest a concrete fix, not just the problem.
- **Proper fix first.** Never recommend only a workaround. When the proper fix is small or obvious, state it without alternatives. Only when it costs far more than the workaround (a large refactor, or changes outside the plan's files) or the trade-off is genuinely ambiguous, show both: `Proper fix: X (effort). Workaround: Y (debt it creates).`
- **Flag workarounds in the plan itself.** If a plan step is a workaround for existing tech debt, such as duplicating code instead of refactoring or adding a shim instead of fixing the interface, mark it FLAG or FAIL with "This step works around [root cause]. Proper fix: [X]." If the proper fix is small, recommend it directly instead of accepting the workaround.
- If the plan is fundamentally flawed, meaning the whole approach is wrong, say so at the top before going step-by-step, so the user doesn't read twenty annotated steps to discover the direction is off.

## Plan rewriting guidelines

When applying fixes or updating the plan document, follow these target-state rules:

- **Target state only (positive specification):** describe what the final state is or will be, not the history of changes or fixes.
- **Omission, not negation:** if an element, step, or feature from the previous draft is removed, omit it from the updated text. Do not write negative diffs such as "Do not include X", "There is no X", or "Removed X". A specification describes what exists, not what was deleted. A plan's `Out of scope` lines are boundaries of the target state, not removal notes; keep them.
- **Example:**
  - *Incorrect:* "There is no header subtitle. Removed the subtitle text."
  - *Correct:* "The header contains a primary title."
