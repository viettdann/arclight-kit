# Reconnaissance

## Phase 1: Map the source and plan coverage

Write `run-metadata.json` and apply the budget gate in `SKILL.md` first. If the gate fails, record the incomplete status and launch nothing.

Launch four `arc-kit:security-reader` agents in parallel, one per prompt below. Each returns facts with repository-relative `path:line` references as one JSON object (`{"facts": [...], "gaps": [...]}`, each fact a short statement plus its references) and writes nothing.

**1a: Product, stack, and structure**

```text
Role: reconnaissance. Read the target at <target>, scope <scope>. Return:
1. Product type, users, operators, and ordinary trust-sensitive actions.
2. Languages, frameworks with their pinned versions, build system, runtimes, and deployment models visible in the repository.
3. Entry points and subsystem boundaries.
4. Comparable software or protocol visible from documentation and dependencies; say so when none is source-grounded.
5. Dependency source installed on disk (node_modules, vendored code, package caches) that can settle framework behavior by reading.
Return only source facts.
```

**1b: Principals, authority, and controls**

```text
Role: reconnaissance. Read all source in <scope> that establishes identity, authorization, isolation, and privilege. Map:
1. Each lower-trust principal and the actions it has by design.
2. Authentication or peer identity at each entry surface.
3. Per-resource authorization and tenant or owner scope.
4. Process, browser, workload, CI, plugin, model/tool, device, or local-IPC authority.
5. Privilege changes, confirmation, revocation, recovery, and fallback paths.
6. Which controls are source-visible and which depend on a deployment fact the repository doesn't show.
Return trust boundaries and control locations. Do not infer live reachability.
```

**1c: Entry surfaces, copies, and sinks**

```text
Role: reconnaissance. Inventory every place in <scope> where external or lower-trust input enters: HTTP/browser, RPC/message/protocol, files/archive/document, CLI/env/config, plugins/dependencies/CI, cloud events/IAM selectors, model context/tool arguments, mobile/deep-link/webview, and local IPC. For each surface, follow major transformations, stored or derived copies, and security-relevant sinks. Record source-visible limits and parallel paths to the same effect. Be complete.
```

**1d: Tests and deployment visibility**

```text
Role: reconnaissance. Read tests, build definitions, manifests, packaging, and environment overlays in <scope>. Return:
1. Existing tests and fixtures that exercise trust boundaries, so a needs_validation test plan can extend them.
2. Boundaries with no test at all.
3. Deployed controls and attachments that source can't establish and that would be decisive for a finding.
4. The active source path for each deployment mode where the repository selects it deterministically.
```

Add a focused reconnaissance agent for each distinct deployment mode or subsystem these four don't map, after repeating the budget gate for it. If the gate blocks one, seed the unmapped area as a `deferred` unit with reason `budget_cannot_reserve_critics_and_validation` and disclose the gap.

## Prior-run input

Before selecting work, read every prior `coverage-ledger.json` and `findings.json` for the same repo and compare each prior record and unit with current source. A prior source ref alone doesn't prove a path unchanged.

- **Prior `confirmed`, relevant source unchanged**: carry it into the candidate set with the same fingerprint, linked to a current `planned` unit with `prior_status: "prior_confirmed_same_source"`. Put only that root cause on the hunter exclusion list. The Phase 3 verifier that re-checks it becomes the unit's owner; its re-check is the unit's first check and moves the unit to `candidate`.
- **Prior `confirmed`, relevant source changed**: a current `planned` unit with `prior_status: "prior_confirmed_changed_source"`. Don't exclude the root cause from hunting; it stays confirmed only if current validation re-establishes it.
- **Prior `needs_validation`, trace still supported by current source**: carry it with the same fingerprint and its blocker, linked to a `planned` unit with `prior_status: "prior_needs_validation"`, owned by the Phase 3 verifier that re-checks it as above.
- **Prior `deferred`, `blocked`, `out_of_scope`, or changed-source units**: current `planned` work when now in scope. They never suppress a current unit.
- **Prior same-source `covered` units**: stay visible with `prior_status: "prior_covered_same_source"`; assign changed source and conflicts first, and let the coverage critic decide whether they need another pass.
- **Prior `rejected`**: suppresses only the unchanged failed claim, never coverage of its unit. Changed evidence makes it current work (`prior_rejected_claim_changed`).
- A prior `quick` or scoped ledger contributes only its recorded evidence and gaps, never an implied "the rest is fine".
- Record missing or incompatible ledgers; don't treat them as empty coverage.

Record the prior paths and source refs used in `run-metadata.json`; summarize only the coverage consequences in `architecture.md`.

## Architecture summary and companion selection

Write `<output-dir>/architecture.md`, about 1,000 words at most:

1. Product, principals, normal authority, and protected resources.
2. The comparable-software baseline from 1a when one is source-grounded: which security trade-offs it accepts. Use it to calibrate effort and severity, never to dismiss a finding; a shared defect pattern that has mattered in practice strengthens a finding. Omit when none exists.
3. Stack, pinned framework versions, deployment paths, and which framework behavior is readable on disk.
4. Entry surfaces and the important source-to-sink or lifecycle paths.
5. Trust boundaries and the strongest source-visible control on each.
6. Repository-relative starting paths.
7. Prior coverage gaps, changed-source and blocked revalidation targets, and same-source confirmed exclusions.
8. Selected companion files from `attack-classes.md` and the source-visible boundary that requires each.

Select a companion because reconnaissance found the boundary its `When to use this file` section describes, never because a language or dependency name appears. Don't exclude a visible boundary because another agent reviews a related class. Per-unit block selections live in the ledger, not here.

## Coverage ledger

Write `<output-dir>/coverage-ledger.json` as a top-level JSON array with one unit per material combination of entry surface, trust boundary, subsystem, and applicable attack class, at the granularity the profile sets. A scoped run keeps discovered excluded surfaces as `out_of_scope` units so a later full run turns them into work.

Each dimension has a human label and a stable source-derived value in `canonical_refs`: a repository-relative entry path plus exported scope, a route or message identity defined in source, the control that defines a boundary, a package path, or the exact attack-class block. A block reference is the file name, `#`, and the exact class name as written in bold or as a heading (`attack-classes.md#Access control`, `ai-and-llm.md#Core discipline`); never a slug or rendered anchor. Use the same reference for the same source object across runs even if its label changes.

Derive `coverage_id`:

1. Each reference is Unicode NFC, has visible content, no control, format, line or paragraph separator, or default-ignorable code point, and no surrounding whitespace.
2. Percent-encode its UTF-8 bytes per RFC 3986: only `A-Z a-z 0-9 - . _ ~` stay unescaped; every other byte becomes uppercase `%HH`.
3. Join the encoded `surface`, `boundary`, `subsystem`, and `attack_class` with `::`; append the encoded `lifecycle` when present.

Never put a wave, agent, verdict, severity, or line number into a reference or ID. Sort units by `coverage_id`. A duplicate ID is an error; one with different semantic fields is an identity collision, never merged or overwritten.

Each unit:

```json
{
  "coverage_id": "...",
  "canonical_refs": {
    "surface": "src/router.ts#POST /users/:id",
    "boundary": "src/authz.ts#requireOwner",
    "subsystem": "packages/api",
    "attack_class": "attack-classes.md#Access control"
  },
  "surface": "...",
  "boundary": "...",
  "subsystem": "...",
  "attack_class": "...",
  "starting_paths": ["repo/relative/path"],
  "ordinary_attack_class_block": "attack-classes.md#Access control",
  "selected_companion_blocks": ["web-protocol-and-auth.md#Core discipline"],
  "excluded_blocks": [{"block": "file.md#section", "reason": "..."}],
  "prior_status": "new|prior_confirmed_same_source|prior_confirmed_changed_source|prior_needs_validation|prior_deferred|prior_blocked|prior_out_of_scope|prior_covered_same_source|prior_covered_changed_source|prior_rejected_claim_changed|none",
  "attempts": [],
  "wave": 1,
  "status": "planned",
  "agent_id": null,
  "reviewed_paths": [],
  "checks": [],
  "result_fingerprints": [],
  "unresolved": []
}
```

When lifecycle is material, add both `canonical_refs.lifecycle` and a human `lifecycle`. `ordinary_attack_class_block` is null only when no ordinary block applies. `selected_companion_blocks` holds each applicable companion class plus that companion's `Core discipline`, `Universal moves`, and `Validation rules`; `excluded_blocks` holds every considered but unselected block with the source fact that excludes it. `prior_status` is `new` for a surface first seen when compatible prior ledgers exist and `none` when there are none. Extra bookkeeping fields are allowed; the fields above stay stable.

Each entry in `checks` is `{"agent_id", "reviewed_paths", "invariant", "result"}`: the agent that read the code, the paths it read, the control it checked, and what source established. The unit's `reviewed_paths` is exactly the union of its checks' paths. A unit's `agent_id` is its assignment owner; verifier checks can sit beside the hunter's in one unit.

| Status | `agent_id` | `reviewed_paths` / `checks` | `result_fingerprints` | `unresolved` |
|---|---|---|---|---|
| `planned` | null | empty | empty | empty |
| `not_applicable`, `out_of_scope`, `deferred` | null | empty | empty | nonempty reason |
| `in_progress` | owner | empty | empty | empty |
| `blocked` | owner | both nonempty | empty | nonempty blocker |
| `covered` | owner | both nonempty | empty | empty |
| `candidate` | owner | both nonempty | nonempty | optional |

Agent IDs are lowercase and match `^[a-z0-9][a-z0-9_-]{0,63}$` (`recon-1a`, `hunter-w1-03`, `verifier-07`), and never a Windows device name such as `con` or `nul`.

`attempts` archives a `blocked`, `covered`, or `candidate` assignment a critic reopens: before reassigning, append its exact `wave`, `status`, `agent_id`, `reviewed_paths`, `checks`, `result_fingerprints`, and `unresolved`, plus the critic's `reassignment_reason`. Archived waves strictly increase and stay below the current wave. The next assignment increments `wave`, uses a fresh owner, and starts with empty live evidence; never copy archived checks into it. If profile or budget stops the reassignment, increment `wave` and set the live unit to `deferred` with no owner, empty evidence, and the reason.

The ledger is the coverage claim. An architecture summary, an agent count, or "auth reviewed" is not coverage; only the paths and checks in a structured result close a unit.

Run `node ${CLAUDE_SKILL_DIR}/scripts/validate-coverage-ledger.cjs <output-dir>/coverage-ledger.json` after seeding, after every update, and before Phase 6, and fix every error before assigning work or claiming coverage. It rejects input over 5 MiB, 64 nesting levels, 10,000 units, or 1,000 entries in a nested list, and prints at most 100 errors.
