# Azure Pipelines advisor

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.

Five modes: **Write** a pipeline or template, **Optimize** an existing one, **Review** one for defects, **Preview** its server-side expansion, **Diagnose** a failed run. Diagnose needs only [Mode routing](#mode-routing) and [Scripts](#scripts); the YAML rules below matter only when the cause is in the YAML.

## Environment

- Azure DevOps Services, Azure Repos Git, Microsoft-hosted Linux agents.
- Deploy targets, one pattern file each in `references/targets/`: App Service (code, containers), Functions, ACR, Bicep, Terraform, VMs over SSH, Static Web Apps.
- Azure service connections use workload identity federation.

## The user's instructions come first

- What the user states (scope, pins, tasks to avoid, what exists) overrides everything below; a settled choice is not reopened or caveated.
- Scope is the pipeline. Build each repo tool the YAML calls and check its `--help` (or option parser) for every flag and path passed, unless told to assume the happy path. No tests, probes or code audit unless asked.
- Groups, branches, tags, permissions and connections the YAML references exist: not looked up or listed as risks.
- Pins: keep the user's and the repo's as they are (a tag stays a tag); add no SHA pins, `global.json`, lock files or `--locked-mode`. Defaults 3 and 6 and template-repo tags (Hard rules) still apply.
- A correction changes only what it names: "fewer tasks" keeps what the job needs; "why X?" asks for the reason, not a reversal.
- Lead with the verdict; no prerequisite lists or skipped-check notes unless they change what the user must do.

## Defaults

These beat doc examples and the user's existing pipelines, whose comments can be wrong: check a claim against the references before repeating it.

1. **Native task first.** Deployments use the deploy task for their target. Fall back to the CLI (`AzureCLI@3` when it needs the service connection, else `Bash@3`) when no task exists or the task is wrong or fails for the case.
2. **Shell steps are `Bash@3` with `targetType: inline`** (`CmdLine@2` only to match an existing pipeline using it), never the `script:`/`bash:`/`pwsh:`/`powershell:` shortcuts. Every inline script starts with `set -euo pipefail`; neither task enables errexit.
3. **Toolchains are installed explicitly.** Node: `UseNode@1`, `version: '24.x'` (its default is `10.x`). .NET: `UseDotNet@2`, `version` from the project's `TargetFramework` (`net10.0` → `10.0.x`). A pin in the repo (`.nvmrc`, `engines`, `packageManager`, `global.json`) wins.
4. **`Cache@2` only with a before/after measurement showing a gain** ([performance.md](references/performance.md#2-cache2-measure-before-adding)); `node_modules` caches lost to plain `npm ci` when measured.
5. **Task majors come from [task-versions.md](references/task-versions.md).** A task missing there is looked up on its reference page before use.
6. **New YAML uses `vmImage: ubuntu-26.04`**; leave `ubuntu-latest`/`ubuntu-24.04` unflagged, flag other Linux images (`ubuntu-22.04` is deprecated).
7. `checkout` states `fetchDepth` and `fetchTags` explicitly (definition defaults vary); `checkout: none` where the repo is not read.
8. **Comments only where YAML cannot speak for itself**: a non-obvious constraint or a workaround. One line each. Most steps need none.

## Hard rules

Frequent silent failures; details and sources in the linked reference.

- **No side effects unless asked**: never queue a run, push, or change pipelines, policies or settings.
- **Never expose a credential**: no `cat`, `source`, `echo` or `Read` of `.env`, no PAT asked in chat, no token picked for the user ([security.md](references/security.md#script-credentials)).
- **Compile time vs runtime.** `${{ }}` runs at template expansion with parameters, literal variables and a subset of predefined variables; `$[ ]` runs before a stage/job with `variables`, `dependencies`, `stageDependencies`; `$( )` is expanded before each task. Variable-group values, `setvariable` values and runtime-only predefined variables (`Build.BuildId`, `System.PullRequest.*`, `System.AccessToken`) are empty inside `${{ }}` ([execution-model.md](references/execution-model.md#availability-matrix)).
- **Macros do not expand in** `trigger`, `pr`, `schedules`, `resources` (including repository `ref:`), `- group:` names, `checkout: git://...@ref`, template paths, or service connection/environment/pool names taken from groups. Use `${{ parameters.x }}` ([execution-model.md](references/execution-model.md#where-macros-and-runtime-expressions-are-not-expanded)).
- **An undefined `$(x)` stays literal.** In bash it becomes command substitution; in `env:` the process gets the text `$(x)`. Declare a default and read it through `env:` ([execution-model.md](references/execution-model.md#undefined-variables)).
- **Secrets are never in the environment unless mapped** with `env:` on that step; the same for `System.AccessToken`. Attach a secret group to the job that uses it ([security.md](references/security.md#secret-variables-and-masking)).
- **A runtime expression is the entire value**: `x: $[ ... ]`, never `x: v$[ ... ]`, never in a task input. ([execution-model.md](references/execution-model.md#the-three-syntaxes)).
- **A custom `condition` replaces the implicit `succeeded()`**: write `and(succeeded(), ...)`. **A skipped dependency makes `succeeded()` False**, including the implicit one on the previous stage: after a PR-only or `${{ if }}`-gated stage, give the next stage its own `dependsOn` or `in(dependencies.X.result, 'Succeeded', 'Skipped')` ([expressions-conditions.md](references/expressions-conditions.md#conditions)).
- **Output variables**: same job `$(step.var)`; other job `dependencies.<job>.outputs['<step>.<var>']`; job in a later stage `stageDependencies.<stage>.<job>.outputs['<step>.<var>']`; a stage condition `dependencies.<stage>.outputs['<job>.<step>.<var>']`. Deployment jobs add the job name (`<job>.<step>.<var>`, runOnce without resource) or `Deploy_<resource>.<step>.<var>`; matrix jobs add the leg name. The consumer must `dependsOn` the producer directly ([expressions-conditions.md](references/expressions-conditions.md#output-variable-matrix)).
- **Boolean parameters** are tested bare or against `true`/`false` literals; `eq(parameters.flag, 'false')` is inverted because `'false'` casts to True ([expressions-conditions.md](references/expressions-conditions.md#type-casting)).
- **Parameters need defaults** when CI, schedules or completion triggers start the pipeline; an empty string cannot be passed at queue time, so UI-facing optional strings use `default: ' '` plus `trim()` ([execution-model.md](references/execution-model.md#queue-time-values)).
- **YAML anchors are rejected.** Use templates, parameters or `each` ([templates.md](references/templates.md#10-error-messages)).
- **Deploys go in `deployment:` jobs on an `environment`**, which gives approvals, locks and history, and does not check out the repo. `ManualValidation@1` gives none of these and anyone editing the YAML can remove it; it needs an agentless job (`pool: server`) and a non-empty `notifyUsers` ([deployment.md](references/deployment.md#deployment-jobs)).
- **Triggers live only in the root file.** On Azure Repos Git the YAML `pr:` is ignored; PR runs come from Build validation branch policies. Without `trigger:` a pipeline runs on every push unless implied CI is disabled ([triggers.md](references/triggers.md#pr-triggers)).
- **Cross-repo build validation** (YAML in repo R validating PRs of repo T): declare T in `resources.repositories` plus `uses:` on the job; `self` is R's default branch, T is `refs/pull/<id>/merge`; pass T's project and repo explicitly since `Build.Repository.*` describes R ([triggers.md](references/triggers.md#cross-repo-build-validation-cross-run)).
- **Repository resources without `ref`** resolve to that repo's default branch. Pin shared template repos to a tag ([templates.md](references/templates.md#6-templates-in-other-repositories)).

## Mode routing

Load only what the task needs: read the section listed in the file's Contents, never `cat` a whole reference.

| Mode | Load | Output |
|---|---|---|
| Write | The sections you need of [execution-model.md](references/execution-model.md#availability-matrix) and [expressions-conditions.md](references/expressions-conditions.md#conditions), plus the topic files below | Run `detect.py` first; ask about each WARN line the user's instructions leave open. Complete YAML per the defaults and the detected package managers and pins, then `task-versions.py check` on it, and `preview.py` when a token, a host pipeline and the pushed templates exist (missing token: [Script credentials](references/security.md#script-credentials)); never ask the user to push or commit for one. |
| Optimize | [performance.md](references/performance.md), [review-checklist.md](references/review-checklist.md#performance) | Measurements from `step-durations.py` (before), ranked changes with the expected saving, the YAML diff, and how to re-measure. No speedup claim without numbers: with no credentials or run history, mark changes "unmeasured" and give the before/after commands. |
| Review | [review-checklist.md](references/review-checklist.md), then the reference each finding points to | `detect.py` on the repo when it is checked out, then findings by severity in the checklist's [finding format](references/review-checklist.md#finding-format), each with the offending line and a pasteable fix, then one line on what was not checked. |
| Preview | [execution-model.md](references/execution-model.md#predefined-variables-at-compile-time), [templates.md](references/templates.md#10-error-messages) | Run `preview.py`; explain the `finalYaml` (what the templates and `${{ }}` produced) or the expansion error and its fix. Clean means expansion only (`Build.Reason` is `Manual`; conditions, `$[ ]`, macros unevaluated). |
| Diagnose | Only the reference the failure points to | Run `run-failure.py` with the run ID, or the pipeline by `--pipeline NAME` (it lists the candidates when a name is ambiguous; ask which). Its first line shows the latest runs: when a later run of the same branch succeeded, lead with "already green since run N" and keep the diagnosis short. Raise `--lines` once if the tail is all cleanup. Then classify: **pipeline** (YAML, variables, task inputs, connection) → the YAML line and its fix (the file is `process.yamlFilename` of `_apis/build/definitions/{id}`; read it at the run's commit with `git show <sourceVersion>:<path>` in the local repo, and compare with the last green run's commit for what changed); **code or test** (compiler error, failing test, app exception) → the file and error, handed to `arc-kit:debug`; **target** (the app, database, or Azure resource refused or failed after deploy) → `mgi-kit:azure-diagnose` with the resource name; **transient** (agent lost, timeout, 5xx from a service) → say so, with the evidence, and that a re-run is the fix. One verdict first, then the evidence lines. |

A Write answer may end with **Traps avoided**: at most 3 bullets, a non-obvious rule the YAML follows and what silently breaks without it. No wishlist of repo additions (lint, tests, lockfiles, pins).

Topic lookup: templates, extends, parameters, `each` → [templates.md](references/templates.md). Triggers, schedules, completion and cross-repo runs → [triggers.md](references/triggers.md). Secrets, tokens, WIF, settings, forks → [security.md](references/security.md). Environments, approvals, app settings from variables → [deployment.md](references/deployment.md). URLs for anything else → [doc-map.md](references/doc-map.md).

## Scripts

Python 3.11+. `scripts/<name>.py` here and in the references means `python3 ./scripts/<name>.py`, and `references/` means `./references/`; run from the user's repo. All are read-only; `detect.py` and `task-versions.py check` are offline.

| Script | Use |
|---|---|
| `scripts/detect.py [DIR] [--json]` | Per project root: package manager, install command, Node/.NET/Python pins, lockfiles, solutions, feeds, Dockerfiles, bake, IaC, existing pipelines. WARN lines need the user's answer; INFO lines give the default to apply. |
| `scripts/task-versions.py check FILE.yml...` | Outdated or deprecated tasks, renamed or removed inputs, unlisted tasks, shortcut steps, with line numbers. `check --markdown FILE.md` does the same over fenced `yaml` blocks. |
| `scripts/task-versions.py refresh` / `org --org ORG` | Latest majors from Learn; an organization's installed tasks (in-house and Marketplace too) with deprecated/preview flags. |
| `scripts/preview.py --org ORG --project P --pipeline-id ID [--yaml FILE] [--param k=v]... [--ref BRANCH]` | Server-side expansion (`previewRun: true`, nothing queued). `--yaml` replaces only the root file; templates resolve from the host pipeline's folder at `--ref`, so unpushed template edits are not previewed ([templates.md](references/templates.md#8-paths)). `--param` takes `object`/`stringList` as YAML or JSON text. `--list [--repo NAME]` finds a host pipeline. |
| `scripts/auth-check.py --org ORG` | Exit 0 and the identity when the credential authenticates. |
| `scripts/step-durations.py --org ORG --project P --pipeline-id ID [--top N] [--reason R]` | n/min/median/max seconds per job and step over recent runs; `--builds a,b,c` for before/after sets. |
| `scripts/run-failure.py --org ORG --project P (--build ID \| --pipeline-id ID \| --pipeline NAME) [--branch REF] [--lines N]` | The pipeline's latest runs, the run's template validation errors, then each failed step's path, issues, and log tail without image-pull noise. A pipeline takes its latest failed run. |

Before any live script, read [Script credentials](references/security.md#script-credentials).

## Live docs

Fetch only what the references lack, as in [doc-map.md](references/doc-map.md#how-to-fetch). On a failed fetch, answer from the references, marked "not verified against live docs".