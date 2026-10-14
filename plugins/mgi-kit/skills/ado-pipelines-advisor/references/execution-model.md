Purpose: when each part of an Azure Pipelines YAML run is evaluated, which values exist at each point, and which variable syntax is legal where.

"(preview)" marks a claim checked through the Runs Preview API, which runs template expansion only; runtime claims cite docs.

## Contents

1. [Run sequence](#run-sequence)
2. [Availability matrix](#availability-matrix)
3. [Predefined variables at compile time](#predefined-variables-at-compile-time)
4. [The three syntaxes](#the-three-syntaxes)
5. [Where macros and runtime expressions are not expanded](#where-macros-and-runtime-expressions-are-not-expanded)
6. [Undefined variables](#undefined-variables)
7. [Secrets](#secrets)
8. [Precedence and collisions](#precedence-and-collisions)
9. [Queue-time values](#queue-time-values)
10. [Setting variables from steps](#setting-variables-from-steps)
11. [Variable names and environment variables](#variable-names-and-environment-variables)
12. [Traps](#traps)

## Run sequence

| # | Phase | What happens | What exists |
|---|---|---|---|
| 1 | Compile (template expansion) | Templates are inserted, `${{ }}` evaluated, `${{ if }}`/`${{ each }}` resolved, parameters validated. Works on the YAML text only ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runs?view=azure-devops)) | Parameters, statically defined `variables`, predefined variables marked "available in templates" |
| 2 | Resource authorization, per stage | Service connections, environments, agent pools, variable groups, repositories are authorized before the stage runs, so their names cannot come from stage/job variables or group values ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runs?view=azure-devops)) | Compile-time values only for resource names |
| 3 | Stage selection | Stage `dependsOn` and `condition` evaluated ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runs?view=azure-devops)) | `dependencies.<stage>.result/outputs`, pipeline-level variables, predefined variables |
| 4 | Job selection | `strategy: matrix`/`parallel` expanded into runtime jobs, then job `condition` evaluated, then an agent requested ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runs?view=azure-devops)) | `dependencies.<job>`, `stageDependencies.<stage>.<job>`, `$[ ]` variables |
| 5 | Job start on the agent | Variables expanded once at job start ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)) | Everything above plus agent variables |
| 6 | Each step | Step `condition` evaluated, then `$( )` macros in its inputs expanded again, then the step runs in its own process ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runs?view=azure-devops)) | Variables set by earlier steps via `task.setvariable` |

Consequences:

- Nothing computed inside a stage, job or step is visible to that same stage's, job's or step's `condition`; a `$[ ]` variable defined in a job cannot gate that job ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions?view=azure-devops)).
- Variables cannot feed `strategy.matrix` values (`some_variable: $(a)` does not work) because they are expanded after the matrix is built; an output variable from a previous job can ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- Parameters exist only during template parsing; to use one at runtime, copy it into a variable with `${{ parameters.x }}` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runtime-parameters?view=azure-devops)).

## Availability matrix

Columns: `${{ }}` = compile time; `$[ ]` = runtime expression in `variables`/`condition`; `$( )` = macro in task inputs and scripts; env = automatically exported to the step environment.

| Source | `${{ }}` | `$[ ]` / condition | `$( )` | env |
|---|---|---|---|---|
| Runtime/template parameters | yes | no (`parameters` is not a runtime context; embed `${{ parameters.x }}`) ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)) | no, embed `${{ }}` | no |
| YAML variable with a literal value | yes, scope-aware: a step sees root, its stage and its job variables; another stage does not see them (preview) | yes | yes | yes |
| YAML variable whose value is `$[ ]` or `$( )` | the unevaluated text, e.g. `$[ eq(...) ]` or `$(Build.BuildId)` (preview) | yes | yes | yes |
| Variable group values | no: `${{ variables['groupVar'] }}` is empty even when the group resolves (preview) | yes ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/variable-groups?view=azure-devops)) | yes | non-secret only |
| Variable group name in `- group:` | name may come from `${{ }}` over parameters, literal variables or compile-time predefined variables (preview) | n/a | not expanded | n/a |
| Pipeline settings (UI) variables, queue-time variables | unverified | yes | yes | non-secret only |
| Predefined, "available in templates" | yes, see next section | yes | yes | yes |
| Predefined, runtime only (`Build.BuildId`, `Agent.*`, `System.JobName`) | empty string (preview) | yes (agent-scoped ones only in step conditions) | yes | yes |
| Secret variables | never use | yes | yes (masked) | no, map with `env:` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-secret-variables?view=azure-devops)) |
| `task.setvariable` (no `isOutput`) | no | later steps' conditions, same job ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions?view=azure-devops)) | later steps, same job | later steps |
| Output variable (`isOutput=true`) | no | same job: `variables['step.var']`; other jobs/stages via `dependencies`/`stageDependencies`, see [expressions-conditions.md](expressions-conditions.md) | same job: `$(step.var)`; elsewhere only after mapping into a variable ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-variables-scripts?view=azure-devops)) | after mapping |

## Predefined variables at compile time

The predefined variables page has an "Available in templates?" column ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops)). Values in a preview:

| Available at compile time | Preview value | Runtime only (empty at compile time) |
|---|---|---|
| `Build.SourceBranch` | the self ref | `Build.BuildId`, `Build.BuildNumber` |
| `Build.SourceBranchName` | last segment of the ref | `Build.Repository.Provider`, `Build.SourcesDirectory`, `Build.ArtifactStagingDirectory` |
| `Build.Reason` | `Manual` (preview is always a manual run) | `Build.TriggeredBy.*`, `Build.SourceVersionMessage` |
| `Build.SourceVersion` | commit SHA | `System.PullRequest.PullRequestId`, `.PullRequestNumber`, `.SourceBranch`, `.TargetBranch` |
| `Build.Repository.Name`, `.ID`, `.Uri` | repo name | `System.JobName`, `System.StageName`, `System.JobAttempt` |
| `Build.DefinitionName`, `Build.RequestedFor`, `Build.QueuedBy` | as expected | `Agent.*` (the agent does not exist yet) |
| `System.TeamProject`, `System.DefinitionId`, `System.CollectionUri` | as expected | `System.Debug` unless set in YAML |
| `System.PullRequest.IsFork` | `False` | `System.AccessToken`: docs say "Yes", preview returns null (`length()` fails with "Kind 'Null' not supported"); never use it at compile time |
| `System.PipelineStartTime` | run start timestamp (not in the docs table) | |

- Index syntax is required for dotted names: `${{ variables['Build.SourceBranch'] }}`; names are case-insensitive (`variables['build.sourcebranch']` works) ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- Preview always evaluates `Build.Reason` as `Manual` and `Build.SourceBranch` as the `--ref`, so a `${{ if eq(variables['Build.Reason'], 'Schedule') }}` branch cannot be previewed; pass the value as a parameter when a branch must be checked.

## The three syntaxes

| Syntax | Evaluated | Legal position | Not found | Context |
|---|---|---|---|---|
| `${{ expr }}` | compile time | key or value, anywhere in YAML | empty string | `parameters`, literal `variables`, compile-time predefined variables ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)) |
| `$[ expr ]` | runtime, before the stage/job | value of a `variables` entry, and `strategy.matrix` (dynamic matrix, [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/phases?view=azure-devops)); must be the entire value | empty string | `variables`, `dependencies`, `stageDependencies`, `counter`, `pipeline.startTime`; no `parameters` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)) |
| `$(name)` | runtime, before each task | value only (right side), in `stages`/`jobs`/`steps` task inputs, `env:`, `displayName` of steps | left verbatim as `$(name)` | all runtime variables, expanded recursively ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)) |

- `condition:` takes a bare runtime expression without `$[ ]`; `${{ }}` inside it is substituted first: `and(succeeded(), ${{ eq(parameters.flag, true) }})` becomes `and(succeeded(), True)` (preview).
- `key: $[ variables.x ] suffix` and `prefix $[ variables.x ]` are invalid per docs ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)). Preview keeps them, and `$[ ]` in a task input, verbatim without error, so a clean preview proves nothing about `$[ ]` placement.
- `$( )` and `$[ ]` never work as keys: `$(key): value` is invalid; only `${{ }}` can produce a key ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- Macros are expanded once at job start and again before each step; a `task.setvariable` in step N is seen by `$( )` from step N+1 ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- Do not put secrets in `${{ }}`: the value is written into the expanded YAML ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).

## Where macros and runtime expressions are not expanded

Use `${{ }}` over parameters or literal variables in all of these:

| Position | Why | Source |
|---|---|---|
| `trigger`, `pr`, `schedules` | compile-time keywords | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops) |
| `resources` (including `repositories[].ref`, `pipelines[].source`) | compile-time; preview keeps `ref: refs/heads/$(br)` literally | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops) |
| `checkout: git://Project/Repo@$(var)` | repository reference is compile-time | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops) |
| `- group: $(name)` | groups are resolved while loading the YAML; `$(gname)` fails with "Variable group  was not found or is not authorized", `${{ variables.gname }}` resolves | preview |
| service connection, environment, pool names from stage/job variables or groups | authorized before the stage starts | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runs?view=azure-devops) |
| `strategy.matrix` leg values | expanded before variables exist | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops) |
| template paths, `extends`, parameters passed to templates | template expansion runs on text only | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runs?view=azure-devops) |

```yaml
parameters:
- name: compilerRef
  type: string
  default: refs/heads/main
resources:
  repositories:
  - repository: compiler
    type: git
    name: MyProject/compiler
    ref: ${{ parameters.compilerRef }}
variables:
- ${{ if eq(variables['Build.SourceBranch'], 'refs/heads/main') }}:
  - group: app-prod
- ${{ else }}:
  - group: app-dev
steps:
- checkout: compiler
```

## Undefined variables

| Syntax | Undefined result |
|---|---|
| `${{ variables.x }}` | empty string (preview: `x${{ variables.noSuch }}x` became `xx`) |
| `$[ variables.x ]` | empty string ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)) |
| `$(x)` | the literal text `$(x)` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)) |

In a Bash step the verbatim `$(x)` is command substitution of a command named `x` ("x: command not found"). As an argument (`echo "v=$(x)"`) it expands to empty and the script continues even under `set -euo pipefail`; only a bare assignment (`V=$(x)`) aborts with exit 127. In `env: { X: $(x) }` the process receives the literal string `$(x)`, which is non-empty and therefore truthy.

Fix: declare a default in YAML before the group that may supply it (same scope, last definition wins), and read it through the environment.

```yaml
variables:
- name: API_BASE_URL
  value: ''
- group: app-settings
steps:
- task: Bash@3
  inputs:
    targetType: inline
    script: |
      set -euo pipefail
      if [ -z "${API_BASE_URL:-}" ]; then echo "##vso[task.logissue type=error]API_BASE_URL not set"; exit 1; fi
      curl -fsS "$API_BASE_URL/health"
  env:
    API_BASE_URL: $(API_BASE_URL)
```

## Secrets

- Secret variables (UI, variable group, Key Vault-linked group, `issecret=true`) are not exported to the step environment. Map each one per step with `env:` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-secret-variables?view=azure-devops)).
- Mapping a secret into a YAML variable (`variables: { G: $(mySecret) }`) does not make `$G` available either; only the step-level `env:` works ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- `$(mySecret)` inline in a script works but puts the value in the script file and possibly in command lines; prefer `env:` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- Substrings and structured parts of secrets are not masked; do not store JSON in a secret ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- Fork PR builds from GitHub get no secrets by default ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- Never pass secrets as runtime parameters; parameter values are expanded into the YAML ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runtime-parameters?view=azure-devops)).

```yaml
variables:
- group: app-secrets
steps:
- task: Bash@3
  inputs:
    targetType: inline
    script: |
      set -euo pipefail
      curl -fsS -H "Authorization: Bearer $API_TOKEN" https://example.invalid/api
  env:
    API_TOKEN: $(apiToken)
```

## Precedence and collisions

Highest first ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)):

1. Job-level YAML variable
2. Stage-level YAML variable
3. Root-level YAML variable
4. Variable set at queue time
5. Pipeline settings (UI) variable

- Same scope, same name: the last definition in the list wins, whether it comes from `name:`, `- group:` or `- template:` (preview for `name:`; docs for groups, [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/variable-groups?view=azure-devops)). The same page warns that two groups in one scope with the same variable "may be unpredictable": keep names unique across groups.
- A variable defined in YAML cannot be overridden at queue time, even if the UI marks it settable ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- `readonly: true` on a YAML variable, or `isreadonly=true` on `task.setvariable`, stops later steps from overwriting it; system variables and task output variables are always read-only ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/inputs?view=azure-devops)).
- `target.settableVariables: none` or a list restricts what a step may set ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- A step `env:` entry may not override a variable-group value of the same name (unverified); do not give an `env:` key the upper-cased name of an existing pipeline variable.

## Queue-time values

- Prefer runtime parameters for non-secret inputs: typed, validated, restricted with `values:` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- Queue-time variables exist only in the pipeline settings UI with "Let users override this value when running this pipeline", and only when the name is not also in YAML ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- With "Limit variables that can be set at queue time" on (org or project), the run API rejects any other variable with "You can't set the following variables (...)" ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/inputs?view=azure-devops)).
- Whether queue-time variables are visible to `${{ }}` is unverified; preview ignores `--var`, so it cannot settle this.
- Parameters without a default fail CI and scheduled runs; `default: ''` compiles but an explicit empty value is rejected at queue time.

## Setting variables from steps

`##vso[task.setvariable variable=NAME;isOutput=BOOL;isSecret=BOOL;isReadOnly=BOOL]value` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/logging-commands?view=azure-devops)):

| Form | Visible where | Reference |
|---|---|---|
| plain | later steps of the same job, not the current step ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)) | `$(NAME)`, env `NAME` upper-cased |
| `isOutput=true` | later steps of the same job, plus downstream jobs/stages that `dependsOn` the job | same job `$(stepName.NAME)`; other jobs via `dependencies`/`stageDependencies` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-variables-scripts?view=azure-devops)) |
| `isSecret=true` | as above, masked, not exported to env | map with `env:` |
| `isReadOnly=true` | as above, cannot be overwritten | |

- The producing step needs `name:` for `isOutput`; the key is `<stepName>.<var>`.
- The current step's environment is not updated, and its `$( )` macros were expanded before it started ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- Values are strings; no space around `=` in `isOutput=true` or the variable may not render ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-variables-scripts?view=azure-devops)).
- `isOutput` variables are usable in the same job as `$(stepName.var)`, as the docs example shows, despite a docs FAQ saying otherwise ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-variables-scripts?view=azure-devops)).
- Print `$[ convertToJson(dependencies) ]` from a downstream job to see the real output keys ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-variables-scripts?view=azure-devops)).

## Variable names and environment variables

- Names: letters, digits, `.`, `_`; no spaces; names starting with `endpoint`, `input`, `secret`, `path`, `securefile` (any case) are not delivered to tasks ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- Env name = upper-cased, `.` to `_`: `any.variable` becomes `ANY_VARIABLE`, `Build.SourceBranch` becomes `BUILD_SOURCEBRANCH` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)). An output `stepName.var` therefore maps to `STEPNAME_VAR` (derived, unverified).
- Property syntax `variables.x` needs a valid identifier; use `variables['a.b']` otherwise ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)).

## Traps

| Wrong | Fix |
|---|---|
| `ref: $(branch)` on a repository resource, `checkout: git://P/R@$(b)`, `- group: $(g)` | `${{ parameters.x }}` or `${{ variables.x }}` with a literal variable |
| `${{ variables.groupVar }}` to branch on a variable-group value | runtime: `condition: eq(variables['groupVar'], 'x')`, or move the switch to a parameter |
| `${{ variables['Build.BuildId'] }}`, `${{ variables['System.PullRequest.PullRequestId'] }}` | `$(Build.BuildId)` at runtime; these are empty at compile time |
| `version: $[ variables.major ].$(minor)` | whole-value only: `version: $[ format('{0}.{1}', variables.major, variables.minor) ]` inside `variables` |
| `inputs: { x: $[ ... ] }` in a task | define a variable with `$[ ]`, pass `$(thatVar)` |
| Job `variables: { go: $[ ... ] }` plus that job's `condition: eq(variables.go, 'true')` | compute it in an upstream job as an output variable, or at pipeline level |
| `script: echo $(maybeUnset)` | declare a default, pass via `env:`, use `${VAR:-}` |
| `env: { TOKEN: $(token) }` where `token` is not defined | the step gets the literal `$(token)`; declare `token: ''` first or fail fast on it |
| Reading a secret as `$MYSECRET` | `env: { MYSECRET: $(mySecret) }` on that step |
| `echo "##vso[task.setvariable variable=v]x"` then `echo $(v)` in the same script | read it in the next step |
| `strategy.matrix` built from `$(var)` | `matrix: $[ dependencies.Gen.outputs['step.legs'] ]` |
| Same variable in two groups at the same scope | rename, or put the intended winner last and keep names unique |
