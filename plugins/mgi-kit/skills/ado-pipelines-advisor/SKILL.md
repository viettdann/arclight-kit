---
name: ado-pipelines-advisor
description: Write, optimize, review, and preview Azure DevOps (Azure Pipelines) YAML from verified rules: templates, extends, parameters, ${{ }} / $[ ] / $( ) expressions, output variables, conditions, triggers, deployment jobs and environments, service connections, secrets, caching, task versions, failed runs. Use when editing azure-pipelines.yml or pipeline templates, when a pipeline doesn't trigger, skips a stage, has an empty variable, or fails at template expansion, or a run failed, even if the user never says "Azure Pipelines". Not for a deployed app failing at runtime (see mgi-kit:azure-diagnose).
---

# Azure Pipelines advisor

Five modes: **Write** a pipeline or template, **Optimize** an existing one, **Review** one for defects, **Preview** its server-side expansion, **Diagnose** a failed run. Diagnose needs only [Mode routing](#mode-routing) and [Scripts](#scripts); the YAML rules below matter only when the cause is in the YAML.

## Environment

- Azure DevOps Services, Azure Repos Git, Microsoft-hosted Linux agents.
- Deploy targets, one pattern file each in `references/targets/`: App Service (code, containers), Functions, ACR, Bicep, Terraform, VMs over SSH, Static Web Apps.
- Azure service connections use workload identity federation.

## The user's instructions come first

- What the user states (scope, what to ignore, how to pin, which tasks to avoid, what exists) overrides everything below. A settled choice is not reopened, re-argued or caveated.
- Scope is the pipeline. Check every tool the YAML calls against its real CLI: build it and run its `--help` (or read its option parser) so each flag, parameter and path the YAML passes exists. Skip this when the user says to assume the happy path. Never run its tests, probe its behavior or audit its code unless asked.
- What the pipeline references (variable groups, branches, tags, permissions, connections) is assumed to exist: not looked up, not listed as a precondition or risk.
- Pin only what the user or the repo pins, the same way (a tag stays a tag). No SHA pins, `global.json`, lock files or `--locked-mode` the repo does not already have.
- A correction changes only what it names. "Fewer tasks" never drops what the job needs to run; "why X?" asks for the reason, not a reversal.
- Lead with the verdict and stay on the question: no prerequisite lists or skipped-check notes unless they change what the user must do.

## Defaults

These take precedence over doc examples and over patterns in the user's existing pipelines, whose comments can be wrong: check a claim against the references before repeating it.

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

Load only what the task needs: find the section in the file's Contents and read that section, never `cat` a whole reference.

| Mode | Load | Output |
|---|---|---|
| Write | The sections you need of [execution-model.md](references/execution-model.md#availability-matrix) and [expressions-conditions.md](references/expressions-conditions.md#conditions), plus the topic files below | Run `detect.py` on the repo first and ask the user about every WARN line their instructions do not already answer. Complete YAML following the defaults and the detected package managers and version pins, then `task-versions.py check` on it and `preview.py` when a token, a host pipeline and the pushed templates exist (ask as in [Credentials](#scripts) about a missing token). Never ask the user to push or commit for a preview. |
| Optimize | [performance.md](references/performance.md), [review-checklist.md](references/review-checklist.md#performance) | Measurements from `step-durations.py` (before), ranked changes with the expected saving, the YAML diff, and how to re-measure. No speedup claim without numbers: with no credentials or run history, mark changes "unmeasured" and give the before/after commands. |
| Review | [review-checklist.md](references/review-checklist.md), then the reference each finding points to | `detect.py` on the repo when it is checked out, then findings by severity in the checklist's [finding format](references/review-checklist.md#finding-format), each with the offending line and a pasteable fix, then one line on what was not checked. |
| Preview | [execution-model.md](references/execution-model.md#predefined-variables-at-compile-time), [templates.md](references/templates.md#10-error-messages) | Run `preview.py`; explain the `finalYaml` (what the templates and `${{ }}` produced) or the expansion error and its fix. Clean means expansion only (`Build.Reason` is `Manual`; conditions, `$[ ]`, macros unevaluated). |
| Diagnose | Only the reference the failure points to | Run `run-failure.py` with the run ID, or the pipeline by `--pipeline NAME` (it lists the candidates when a name is ambiguous; ask which). Its first line shows the latest runs: when a later run of the same branch succeeded, lead with "already green since run N" and keep the diagnosis short. Raise `--lines` once if the tail is all cleanup. Then classify: **pipeline** (YAML, variables, task inputs, connection) → the YAML line and its fix (the file is `process.yamlFilename` of `_apis/build/definitions/{id}`; read it at the run's commit with `git show <sourceVersion>:<path>` in the local repo, and compare with the last green run's commit for what changed); **code or test** (compiler error, failing test, app exception) → the file and error, handed to `arc-kit:debug`; **target** (the app, database, or Azure resource refused or failed after deploy) → `mgi-kit:azure-diagnose` with the resource name; **transient** (agent lost, timeout, 5xx from a service) → say so, with the evidence, and that a re-run is the fix. One verdict first, then the evidence lines. |

A Write answer may end with **Traps avoided**: at most 3 bullets, a non-obvious rule the YAML follows and what silently breaks without it. No wishlist of repo additions (lint, tests, lockfiles, pins).

Topic lookup: templates, extends, parameters, `each` → [templates.md](references/templates.md). Triggers, schedules, completion and cross-repo runs → [triggers.md](references/triggers.md). Secrets, tokens, WIF, settings, forks → [security.md](references/security.md). Environments, approvals, app settings from variables → [deployment.md](references/deployment.md). URLs for anything else → [doc-map.md](references/doc-map.md).

## Scripts

Python 3.11+. `scripts/<name>.py` here and in the references means `python3 ${CLAUDE_SKILL_DIR}/scripts/<name>.py`, and `references/` means `${CLAUDE_SKILL_DIR}/references/`; run from the user's repo. All are read-only; `detect.py` and `task-versions.py check` are offline.

| Script | Use |
|---|---|
| `scripts/detect.py [DIR] [--json]` | Per project root: package manager, install command, Node/.NET/Python pins, lockfiles, solutions, feeds, Dockerfiles, bake, IaC, existing pipelines. WARN lines need the user's answer; INFO lines give the default to apply. |
| `scripts/task-versions.py check FILE.yml...` | Outdated or deprecated tasks, renamed or removed inputs, unlisted tasks, shortcut steps, with line numbers. `check --markdown FILE.md` does the same over fenced `yaml` blocks. |
| `scripts/task-versions.py refresh` / `org --org ORG` | Latest majors from Learn; an organization's installed tasks (in-house and Marketplace too) with deprecated/preview flags. |
| `scripts/preview.py --org ORG --project P --pipeline-id ID [--yaml FILE] [--param k=v]... [--ref BRANCH]` | Server-side expansion (`previewRun: true`, nothing queued). `--yaml` replaces only the root file; templates resolve from the host pipeline's folder at `--ref`, so unpushed template edits are not previewed ([templates.md](references/templates.md#8-paths)). `--param` takes `object`/`stringList` as YAML or JSON text. `--list [--repo NAME]` finds a host pipeline. |
| `scripts/auth-check.py --org ORG` | Exit 0 and the identity when the credential authenticates. |
| `scripts/step-durations.py --org ORG --project P --pipeline-id ID [--top N] [--reason R]` | n/min/median/max seconds per job and step over recent runs; `--builds a,b,c` for before/after sets. |
| `scripts/run-failure.py --org ORG --project P (--build ID \| --pipeline-id ID \| --pipeline NAME) [--branch REF] [--lines N]` | The pipeline's latest runs, the run's template validation errors, then each failed step's path, issues, and log tail without image-pull noise. A pipeline takes its latest failed run. |

Credentials: the scripts read `AZURE_DEVOPS_EXT_PAT`, else `az login`, asking az for a token in the organization's own tenant (read from the org, or `ADO_TENANT`) whatever the default subscription is. If either works, run `scripts/auth-check.py --org ORG` and name the identity. Otherwise never pick a token: after the offline work, ask once whether to skip live checks, use a workspace `.env` key, or have the user `export AZURE_DEVOPS_EXT_PAT=...` or `az login`, plus the preview host pipeline ID (or offer `preview.py --list`). List `.env` keys with `cut -s -d= -f1 .env`; shell state does not persist, so prefix each command with `AZURE_DEVOPS_EXT_PAT="$(sed -n 's/^KEY=//p' .env | head -1 | tr -d "\"'")"`. Never print a secret (no `cat`, `source`, `echo` or `Read` of `.env`) or ask for the PAT in chat. PAT scopes: Build (Read) for preview, durations and run-failure, Agent Pools (Read) for `task-versions.py org`. Org and project come from the repo remote (`https://dev.azure.com/{org}/{project}/_git/{repo}`) or `ADO_ORG`/`ADO_PROJECT`.

## Live docs

Fetch only what the references lack: the page from [doc-map.md](references/doc-map.md) or a task's `docs` link in [task-versions.md](references/task-versions.md), with `&accept=text/markdown`, and a WebFetch prompt that extracts just the input or key you need from the `azure-pipelines` moniker block. If a fetch fails, answer from the references marked "not verified against live docs". Where docs and observations disagree the references record both; prefer the observation and say so.
