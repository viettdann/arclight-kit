Purpose: expression functions, type casting, conditions, and the exact syntax for reading output variables across steps, jobs, stages, deployment jobs and matrices.

"(preview)" and the "Observed" column mark claims evaluated at compile time through the Runs Preview API; runtime-only claims (conditions, `dependencies`, output variables) cite docs. For when each syntax is evaluated, see [execution-model.md](execution-model.md).

## Contents

1. [Literals and contexts](#literals-and-contexts)
2. [Function catalog](#function-catalog)
3. [Type casting](#type-casting)
4. [Conditions](#conditions)
5. [Output variable matrix](#output-variable-matrix)
6. [Deployment jobs](#deployment-jobs)
7. [Matrix and parallel jobs](#matrix-and-parallel-jobs)
8. [Stage conditions and stage variables](#stage-conditions-and-stage-variables)
9. [Traps](#traps)

## Literals and contexts

- Literals: boolean `true`/`false` (case-insensitive), `null` (result of a dictionary miss, not writable), number, string in single quotes (`'It''s'`), version `1.2.3` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)).
- `${{ }}` contexts: `parameters`, `variables` (literal ones only). `$[ ]` and `condition:` contexts: `variables`, `dependencies`, `stageDependencies`, `pipeline.startTime`; no `parameters` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)).
- At compile time `succeeded()`, `always()`, `counter()`, `dependencies`, `pipeline.startTime` fail with "Unrecognized value: 'X'" (preview).
- Filtered array: `parameters.list.*` or `foo.*.id` selects all elements; `${{ join(',', parameters.list.*) }}` gives `a,b,c` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)).
- Multi-line `condition: |` (or `>`) is valid; whitespace between tokens is ignored ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)).

## Function catalog

All from the expressions page ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)).

| Function | Rule | Observed at compile time |
|---|---|---|
| `eq(a, b)` / `ne(a, b)` | right converted to left's type; `eq` is False and `ne` True when conversion fails; strings ordinal ignore-case | `eq('ABC','abc')` True, `eq(1,'abc')` False, `ne(1,'abc')` True |
| `gt ge lt le` | right converted to left's type, error if conversion fails | `gt('1.10.0','1.9.0')` False (string order), `gt(1.10.0, 1.9.0)` True (version literals) |
| `and(a, b, ...)`, `or(...)` | cast to Boolean, short-circuit, 2..N args | |
| `not(a)`, `xor(a, b)` | cast to Boolean | `xor(true,false)` True |
| `in(x, a, b, ...)`, `notIn(...)` | equality with ignore-case | `in('b','a','B')` True |
| `contains(s, sub)`, `startsWith`, `endsWith` | cast to string, ignore-case | `contains('refs/heads/Main','main')` True |
| `containsValue(collection, v)` | any array item or object property value equals `v` | True for object param values, `stringList`, and `'B'` in `[a,b,c]` |
| `iif(cond, a, b)` | a if cond is True else b | docs say 1..3 args, but `iif(false, 'yes')` fails "Unexpected symbol: ')'"; always pass 3 |
| `coalesce(a, b, ...)` | first value that is not null or empty | `coalesce('', variables.noSuch, 'fallback')` = `fallback` |
| `trim(s)` | strip leading/trailing whitespace | `trim('  a b  ')` = `a b` |
| `replace(s, old, new)` | replace all occurrences | `replace('refs/heads/feature/x','refs/heads/','')` = `feature/x` |
| `split(s, delim)` | array, keeps empty entries | `length(split('a,b,,c,', ','))` = 5; `split('a,b,,c', ',')[1]` = `b` |
| `join(sep, array)` | non-array argument returned as string; complex items become empty | `join(';', 'notarray')` = `notarray` |
| `format(fmt, args...)` | `{0}` placeholders, `{{`/`}}` escape, .NET date specifiers with `pipeline.startTime` | `format('{0}-{1}-{{x}}','a',2)` = `a-2-{x}` |
| `length(x)` | string, array or object length; null is an error | object with 2 keys = 2; `length(null)` fails "Kind 'Null' not supported" |
| `lower(s)`, `upper(s)` | | |
| `convertToJson(x)` | object to JSON text, for `env:` or a file | works on `object` and `stringList` params |
| `counter(prefix, seed)` | runtime only, only in a variable definition, per-pipeline, separate sequence per prefix | compile time: "Unrecognized value: 'counter'" |
| `always()` | True even when canceled; a critical failure such as failed checkout can still stop steps | condition only |
| `canceled()` | True if the run was canceled | condition only |
| `failed()` / `failed('A','B')` | step: `Agent.JobStatus` is Failed; job/stage: any (or named) previous dependency failed | condition only |
| `succeeded()` / `succeeded('A')` | step: status Succeeded or SucceededWithIssues; job/stage: all (or named) dependencies succeeded or partially; False on cancel | condition only |
| `succeededOrFailed()` | like `always()` but False on cancel | condition only |

Counter examples ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)):

```yaml
variables:
  major: 1
  minor: $[ counter(variables['major'], 100) ]
  daily: $[ counter(format('{0:yyyyMMdd}', pipeline.startTime), 1) ]
```

## Type casting

Conversion rules ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)):

| From | To Boolean | To number | To string |
|---|---|---|---|
| Boolean | - | False 0, True 1 | `False`, `True` |
| Null | False | 0 | `''` |
| Number | 0 False, else True | - | no separators |
| String | `''` False, any other string True (including `'false'` and `'0'`) | `''` 0, else Int32.TryParse | - |
| Version | True | - | `Major.Minor[.Build[.Revision]]` |

Observed (preview):

| Expression | Result | Why |
|---|---|---|
| `eq('true', true)` | True | right `true` to string `True`, ignore-case |
| `eq('false', true)` | False | |
| `eq(parameters.flag, 'false')` with boolean `flag: false` | False | right `'false'` to Boolean is True (non-empty); the test is inverted |
| `eq(parameters.flag, 'false')` with `flag: true` | True | same inversion |
| `eq(parameters.flag, false)` | correct | compare with a Boolean literal |
| `eq(parameters.num, '2')` with number `2` | True | |
| `eq('2.0', 2)` | False | right `2` to string `'2'` |
| `iif(parameters.s, ...)` with string `s: 'false'` | truthy branch | non-empty string |
| `${{ parameters.flag }}` rendered into YAML | `True` / `False` | Boolean to string |

- Boolean parameter: test it bare (`${{ if parameters.flag }}`) or against `true`/`false` literals, never against `'true'`/`'false'` strings.
- Variables are always strings: `eq(variables.isMain, true)` works because `true` becomes `'True'` and comparison ignores case ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions?view=azure-devops)); `eq(variables.x, 'true')` also works.
- Empty string and null are equal in conditions: `eq(variables.unset, '')` is True ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions?view=azure-devops)).
- Compare versions as version literals or split them; string comparison of `'1.10.0'` and `'1.9.0'` is lexical.

## Conditions

| Condition | Runs when | Note |
|---|---|---|
| none (implicit `succeeded()`) | all direct and indirect dependencies succeeded; for steps, nothing in the job failed so far | default ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions?view=azure-devops)) |
| `succeededOrFailed()` | dependencies succeeded or failed, not canceled | docs suggest `not(canceled())` when dependencies may be skipped ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)) |
| `not(canceled())` | anything except cancel, including skipped dependencies | the robust "run unless canceled" |
| `always()` | even when canceled | cleanup and notification only; set `cancelTimeoutInMinutes` for it to finish ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions?view=azure-devops)) |
| `failed()` | a dependency failed | |

- A custom `condition` replaces the implicit `succeeded()` entirely; without it the stage, job or step runs after failures and even after cancel. Write `and(succeeded(), <custom>)` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions?view=azure-devops)).
- If the parent (stage for a job, job for a step) is skipped, the child never runs, whatever its condition ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions?view=azure-devops)).
- A skipped dependency makes the default `succeeded()` False, so the skip cascades down the `dependsOn` chain; to run after a skipped dependency test `result` explicitly ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)).
- Canceling while stage 1 runs: a later stage with a status-free condition still runs; a job or step condition inside a stage whose own condition is default does not, because the stage is skipped ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions?view=azure-devops)).
- `result` values: `Succeeded`, `SucceededWithIssues`, `Skipped`, `Failed`, `Canceled` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)).

```yaml
jobs:
- job: a
  condition: false
  steps:
  - task: Bash@3
    inputs:
      targetType: inline
      script: |
        set -euo pipefail
        echo a
- job: c
  dependsOn: a
  condition: in(dependencies.a.result, 'Succeeded', 'SucceededWithIssues', 'Skipped')
  steps:
  - task: Bash@3
    inputs:
      targetType: inline
      script: |
        set -euo pipefail
        echo runs although a was skipped
```

Parameters in conditions: `${{ }}` is replaced before the condition is evaluated ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions?view=azure-devops)). `condition: and(succeeded(), ${{ eq(parameters.doThing, true) }})` compiles to `and(succeeded(), True)`. A condition that is only `${{ eq(parameters.x, true) }}` compiles to plain `True`, which drops `succeeded()`; to remove a job or step entirely, wrap it in `${{ if }}` instead.

```yaml
parameters:
- name: runE2E
  type: boolean
  default: false
steps:
- ${{ if parameters.runE2E }}:
  - task: Bash@3
    inputs:
      targetType: inline
      script: |
        set -euo pipefail
        npm run e2e
- task: Bash@3
  condition: and(succeeded(), eq(variables['Build.Reason'], 'PullRequest'))
  inputs:
    targetType: inline
    script: |
      set -euo pipefail
      echo pr only
```

## Output variable matrix

Producer: step `name: sel` in job `A` of stage `S1` runs `echo "##vso[task.setvariable variable=v;isOutput=true]x"`. Consumers must `dependsOn` the producer directly; outputs are only visible to direct dependents, so a stage two hops away needs `dependsOn` on `S1` too ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).

| Consumer | Where | Expression |
|---|---|---|
| Same job, later step | input/script | `$(sel.v)` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-variables-scripts?view=azure-devops)) |
| Same job, later step | step condition | `eq(variables['sel.v'], 'x')` |
| Other job, same stage | job `variables` | `$[ dependencies.A.outputs['sel.v'] ]` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)) |
| Other job, same stage | job `condition` | `and(succeeded(), eq(dependencies.A.outputs['sel.v'], 'x'))` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)) |
| Job in a later stage | job `variables` or job `condition` | `stageDependencies.S1.A.outputs['sel.v']` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)) |
| Later stage | stage `variables` | `$[ stageDependencies.S1.A.outputs['sel.v'] ]` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)) |
| Later stage | stage `condition` | `eq(dependencies.S1.outputs['A.sel.v'], 'x')` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)) |

- Stage conditions use `dependencies.<stage>.outputs['<job>.<step>.<var>']`; job-level expressions use `stageDependencies.<stage>.<job>.outputs['<step>.<var>']`. The expressions page's summary table shows `stageDependencies` for stage conditions, but its examples and the deployment-jobs page use `dependencies`; follow the examples ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)).
- The wrong context (`stageDependencies` in a stage condition, `dependencies.S1...` in a job) likely yields null, so the condition is silently False rather than an error (unverified).
- A missing output mapped with `$[ ]` becomes an empty string, not a literal macro ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- Dump the keys: `deps: $[ convertToJson(dependencies) ]` then print `$(deps)` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-variables-scripts?view=azure-devops)).

```yaml
stages:
- stage: Build
  jobs:
  - job: Package
    steps:
    - task: Bash@3
      name: manifest
      inputs:
        targetType: inline
        script: |
          set -euo pipefail
          echo "##vso[task.setvariable variable=version;isOutput=true]1.4.2"
- stage: Publish
  dependsOn: Build
  condition: and(succeeded(), ne(dependencies.Build.outputs['Package.manifest.version'], ''))
  variables:
    version: $[ stageDependencies.Build.Package.outputs['manifest.version'] ]
  jobs:
  - job: Show
    steps:
    - task: Bash@3
      inputs:
        targetType: inline
        script: |
          set -euo pipefail
          echo "$VERSION"
      env:
        VERSION: $(version)
```

## Deployment jobs

The key gains a prefix: the deployment job name for `runOnce` on an environment without a resource, `Deploy_<resourceName>` when the environment targets a resource ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)). Producer: `deployment: D`, step `name: s`, variable `v`, stage `S1`.

| Consumer | runOnce, no resource | runOnce, `resourceName: vm1` |
|---|---|---|
| Job, same stage | `dependencies.D.outputs['D.s.v']` | `dependencies.D.outputs['Deploy_vm1.s.v']` |
| Job, later stage | `stageDependencies.S1.D.outputs['D.s.v']` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)) | `stageDependencies.S1.D.outputs['Deploy_vm1.s.v']` (derived, unverified) |
| Stage condition, later stage | `dependencies.S1.outputs['D.D.s.v']` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)) | `dependencies.S1.outputs['D.Deploy_vm1.s.v']` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)) |

- Other strategies: canary `<hook>_<increment>` (e.g. `deploy_10.s.v`), rolling `<hook>_<resourceName>` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)).
- runOnce uses the job name whichever lifecycle hook set the variable ("for a runOnce job, specify the name of the job instead of the lifecycle hook", [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)); unverified for hooks other than `deploy`.
- The docs example for a resource environment shows both `<job>.<step>...` and `Deploy_<resource>.<step>...`; only the `Deploy_` form matches the stated rule. Check with `convertToJson(dependencies)` when it matters.
- A deployment job reading a regular job's output from an earlier stage uses the normal form: `$[ stageDependencies.Build.Package.outputs['manifest.version'] ]`.

## Matrix and parallel jobs

- Matrix leg names become part of the key: `dependencies.A.outputs['<leg>.<step>.<var>']`, e.g. `['debugJob.setvarStep.myOutputVar']` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)). The leg is appended to the job's display name ("Build Python35"), the job ID used in `dependencies` stays `A` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/jobs-job-strategy?view=azure-pipelines)).
- Leg names: ASCII letters, digits, `_`, start with a letter, at most 100 characters ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/jobs-job-strategy?view=azure-pipelines)).
- `parallel: N` slices: the docs example reads `dependencies.A.outputs['setvarStep.myOutputVar']` without a slice prefix and does not say which slice's value wins; unverified, dump `dependencies` before relying on it ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)).
- `dependencies.A.result` for a matrix job is the aggregate of its legs (unverified).

Dynamic matrix: `matrix` accepts a runtime expression whose value is a JSON object of legs; values are strings ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/phases?view=azure-devops)). Preview compiles it but cannot check the JSON.

```yaml
jobs:
- job: Gen
  steps:
  - task: Bash@3
    name: mtrx
    inputs:
      targetType: inline
      script: |
        set -euo pipefail
        legs='{"shard1":{"SHARD":"1"},"shard2":{"SHARD":"2"}}'
        echo "##vso[task.setvariable variable=legs;isOutput=true]$legs"
- job: Run
  dependsOn: Gen
  strategy:
    matrix: $[ dependencies.Gen.outputs['mtrx.legs'] ]
  steps:
  - task: Bash@3
    inputs:
      targetType: inline
      script: |
        set -euo pipefail
        echo "shard $SHARD"
```

Behavior for an empty or malformed JSON value is unverified; always emit at least one leg, e.g. a fallback `{"shard1":{"SHARD":"1"}}`.

## Stage conditions and stage variables

- A stage condition is evaluated before the stage starts; nothing computed during that stage is available to it ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions?view=azure-devops)), and variable groups are authorized before the stage runs ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runs?view=azure-devops)).
- Treat a stage's own `variables:` (literal or `- group:`) as invisible to that stage's `condition` (undocumented, consistent with the order above): put gating variables at root, compute them in an upstream stage as outputs, or decide at compile time with `${{ if }}`.
- A stage's variables can map a previous stage's outputs with `stageDependencies`, and its condition can test the same value with `dependencies` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)).

```yaml
variables:
  deployEnvs: dev
stages:
- stage: Dev
  condition: and(succeeded(), contains(variables['deployEnvs'], 'dev'))
  variables:
  - group: app-dev
  jobs:
  - job: Deploy
    steps:
    - task: Bash@3
      inputs:
        targetType: inline
        script: |
          set -euo pipefail
          echo "$(appUrl)"
```

## Traps

| Wrong | Fix |
|---|---|
| `condition: eq(variables['Build.SourceBranch'], 'refs/heads/main')` | `and(succeeded(), eq(...))`; otherwise it runs after failure and cancel |
| `condition: succeededOrFailed()` after a job that may be skipped | `not(canceled())`, or test `dependencies.X.result` with `'Skipped'` |
| `eq(parameters.flag, 'false')` on a boolean parameter | `eq(parameters.flag, false)` or `not(${{ parameters.flag }})` or `${{ if not(parameters.flag) }}` |
| `${{ if parameters.mode }}` on a string that may be `'false'` | `${{ if eq(parameters.mode, 'on') }}` |
| `iif(cond, 'a')` | `iif(cond, 'a', '')` |
| Stage condition `stageDependencies.S1.A.outputs['s.v']` | `dependencies.S1.outputs['A.s.v']` |
| Job condition `dependencies.S1.outputs['A.s.v']` for a previous stage | `stageDependencies.S1.A.outputs['s.v']` |
| Deployment output `dependencies.D.outputs['s.v']` | `dependencies.D.outputs['D.s.v']`, or `['Deploy_<resource>.s.v']` with a resource |
| Matrix output `dependencies.A.outputs['s.v']` | `dependencies.A.outputs['<leg>.s.v']` |
| Stage 3 reading stage 1 outputs with default `dependsOn` | `dependsOn: [S1, S2]` |
| `condition: ${{ eq(parameters.x, true) }}` alone | `and(succeeded(), ${{ eq(parameters.x, true) }})`, or `${{ if }}` around the item |
| `gt(variables.ver, '1.9.0')` for versions | split into numbers, or compare version literals at compile time |
| Avoiding `condition: \|` because "newlines stay in the expression" | A literal or folded block scalar condition is valid; whitespace between tokens is ignored |
