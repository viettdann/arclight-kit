# Templates

Include and `extends` templates, typed parameters, `each`/`if`/`insert`, cross-repo templates, limits, error messages and library layout. Unmarked behavior and every quoted error message were verified with `scripts/preview.py`; "observed" and "unverified" mark the rest.

## Contents

1. [Kinds of template and what a template file may contain](#1-kinds-of-template-and-what-a-template-file-may-contain)
2. [When to use `extends`](#2-when-to-use-extends)
3. [Typed parameters](#3-typed-parameters)
4. [`each`](#4-each)
5. [`if`/`elseif`/`else` and `${{ insert }}`](#5-ifelseifelse-and--insert-)
6. [Templates in other repositories](#6-templates-in-other-repositories)
7. [Template context: what a template can see](#7-template-context-what-a-template-can-see)
8. [Paths](#8-paths)
9. [Limits](#9-limits)
10. [Error messages](#10-error-messages)
11. [Library layout](#11-library-layout)

## 1. Kinds of template and what a template file may contain

| Kind | Referenced from | Template file top level |
|---|---|---|
| Step | `steps: - template: x.yml` | `parameters`, `steps` |
| Job | `jobs: - template: x.yml` | `parameters`, `jobs` |
| Stage | `stages: - template: x.yml` | `parameters`, `stages` |
| Variable | `variables: - template: x.yml` | `parameters`, `variables` only ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)) |
| Extends | `extends: template: x.yml` (instead of `stages`/`jobs`/`steps`) | `parameters`, `variables`, `resources`, one of `stages`/`jobs`/`steps`, or a nested `extends` |

- `pool`, `pr` and `schedules` at the top of any template fail with "Unexpected value 'pool'" (`'pr'`, `'schedules'`). Put `pool` in the entry file or on the stage/job.
- `trigger` in an include template, and `variables` at the top of a job include template, fail with "Unexpected value 'trigger'" (`'variables'`); use job- or stage-level `variables:` inside the template.
- `trigger` in an `extends` template is accepted and silently ignored; only the entry file's trigger counts (none there = default CI).
- `resources.repositories` declared in an `extends` template are merged into the pipeline's resources.
- An `extends` template may itself `extends` another template (verified two levels, across repos).
- The entry file keeps `trigger`, `pr`, `schedules`, `name`, `pool`, `variables`, `resources`, `parameters` next to `extends`; `stages`/`jobs`/`steps` next to `extends` fail with "Unexpected value 'jobs'" ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/extends?view=azure-pipelines)).
- A job template used under `steps:` fails with "/jobs/build.yml@templates (Line: 30, Col: 1): Unexpected value 'jobs'". The error names the template file, not the caller.
- Templates must exist when the run starts; they cannot come from an artifact ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)).

## 2. When to use `extends`

Use `extends` when the template must own the pipeline's outer structure (mandatory security steps, allowed pools, step filtering) or a protected resource has a **Required template** check ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/templates?view=azure-devops)). Use include templates for plain reuse.

- Required template check: set under Approvals and checks on the protected resource, with repository, ref and path of the template. Only a pipeline that extends that template passes; include templates never satisfy it ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops#required-template)).
- Pin the template repo to a tag so a template change does not reach every pipeline at once ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/templates?view=azure-devops)).
- Controls a template can impose on user steps: `values:` on parameters (pools, images), `target: <container>`, `target.commands: restricted`, `target.settableVariables`, step rewriting with `each` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/templates?view=azure-devops)).
- Docs trap: the security page's example `eq(variables['Build.SourceBranchName'], 'refs/heads/main')` never matches (`SourceBranchName` is `main`); compare `Build.SourceBranch` to `refs/heads/main`.

## 3. Typed parameters

Each parameter needs `name` and `type`; `default` makes it optional. Scalars declared without a type are strings, so `eq(true, parameters.x)` is true for the string `false` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)).

| Type | Accepts | Behavior |
|---|---|---|
| `string` | a scalar; `values:` restricts it | A list or map fails "The 'project' parameter is not a valid String."; `5` and `true` are accepted and stringified |
| `number` | number-like string; `values:` restricts it | `abc` fails "The 'outputFetchDepth' parameter value 'abc' is not a valid Number."; `'3'` accepted |
| `boolean` | `true`/`false`, case-insensitive | `True`, `"TRUE"` accepted; `yes` fails "... value 'yes' is not a valid Boolean."; renders as `True`/`False` in strings |
| `object` | any YAML | Booleans inside an object render as `True` (`CI: true` becomes `CI=True` in `env`); quote them, `CI: 'true'` |
| `step` | one step mapping | A list fails "The 'one' parameter is not a valid Step." |
| `stepList` | sequence of steps | A job in it fails "The 'extra' parameter is not a valid StepList." plus "Unexpected value 'job'" |
| `job` / `jobList` | one job / sequence of jobs | `jobList` also accepts `deployment:` jobs and `templateContext` |
| `deployment` / `deploymentList` | deployment jobs | Observed: a plain `job:` in a `deploymentList` is not rejected; do not rely on the type as a guard |
| `stage` / `stageList` | stages | A job in a `stageList` fails "... is not a valid StageList." |
| `stringList` | multi-select list, root pipeline only | Each item is checked against `values:` ("The 'regions' parameter value 'XX' is not a valid value."); not available in templates, use `object` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/template-parameters?view=azure-devops)) |

- `default` must be a literal: `default: ${{ variables.x }}` fails "A template expression is not allowed in this context" ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/template-parameters?view=azure-devops)).
- No default and no value: "A value for the 'project' parameter must be provided." Every root parameter needs a default for CI, PR and scheduled runs; a template parameter without a default forces the caller to pass a value.
- `default: ''` is fine for template parameters; only a root parameter given `""` at queue time fails "The 's' parameter is not a valid String."
- `values:` failure: "The 'reviewDepth' parameter value 'extreme' is not a valid value."
- A caller passing an undeclared name fails "Unexpected parameter 'foo'", so renaming a template parameter breaks every caller on the next run.
- `${{ parameters.flag }}` prints `True`; use `lower(parameters.flag)` when a CLI wants `true`/`false` (e.g. `--auto-complete ${{ lower(parameters.autoCompletePullRequest) }}`).
- `templateContext` on items of a `jobList`/`deploymentList`/`stageList` carries extra data to the template (`job.templateContext.x`); it passes through into `finalYaml` unless filtered out ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/template-parameters?view=azure-devops)).

## 4. `each`

`${{ each x in collection }}` iterates a sequence (items) or a mapping (`x.key`, `x.value`) ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/template-expressions?view=azure-devops)).

- Over a string: "(Line: 7, Col: 5): Expected a sequence or mapping. Actual value 'dev'". Declare list parameters as `object` (templates) or `stringList` (root).
- Over `parameters` itself: yields every parameter as `key`/`value`; an object value in a string position fails "Unable to convert from Object to String. Value: Object", wrap it in `convertToJson()`.
- Over a map into a mapping, e.g. derived variable names:

```yaml
parameters:
  - name: tags
    type: object
    default:
      team: platform
      tier: gold
stages:
  - stage: Build
    variables:
      ${{ each pair in parameters.tags }}:
        tag_${{ pair.key }}: ${{ pair.value }}
    jobs:
      - job: b
        steps:
          - checkout: none
```

- Over a list in an `object` parameter feeding a job template, derive a unique job name from the item (`job: scan_${{ replace(sub, '-', '_') }}`) so each iteration compiles.
- A `stepList` is normalized before `each` sees it: `script:` arrives as `task: CmdLine@2`, `bash:` as `task: Bash@3`, `checkout: none` as `task: 6d15af64-176c-496d-b583-fd2ae21d4df4@1` with `condition: false`. Filter on `step.task`, never on the shortcut key.

Wrap every user step (pre-step plus an injected key):

```yaml
parameters:
  - name: userSteps
    type: stepList
    default: []
steps:
  - ${{ each step in parameters.userSteps }}:
      - task: Bash@3
        displayName: before ${{ step.displayName }}
        inputs:
          targetType: inline
          script: |
            set -euo pipefail
            date
      - ${{ each pair in step }}:
          ${{ pair.key }}: ${{ pair.value }}
        continueOnError: true
```

Injecting a key the step already has fails "'timeoutInMinutes' is already defined". To override a key, skip it in the copy loop and add your own:

```yaml
parameters:
  - name: userSteps
    type: stepList
    default: []
steps:
  - ${{ each step in parameters.userSteps }}:
      - ${{ each pair in step }}:
          ${{ if ne(pair.key, 'timeoutInMinutes') }}:
            ${{ pair.key }}: ${{ pair.value }}
        timeoutInMinutes: 10
```

Reject a task (docs pattern; fails "(Line: 15, Col: 5): Unexpected value 'CmdLine@2'" and, through normalization, also rejects `script:` steps) ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)):

```yaml
parameters:
  - name: buildSteps
    type: stepList
    default: []
steps:
  - ${{ each step in parameters.buildSteps }}:
      - ${{ each pair in step }}:
          ${{ if ne(pair.value, 'CmdLine@2') }}:
            ${{ pair.key }}: ${{ pair.value }}
          ${{ if eq(pair.value, 'CmdLine@2') }}:
            '${{ pair.value }}': error
```

Wrap jobs: copy every key except `steps`, then emit `steps:` with pre-steps, `- ${{ job.steps }}`, post-steps ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/template-expressions?view=azure-devops)). Inserting a list into a list flattens it.

## 5. `if`/`elseif`/`else` and `${{ insert }}`

- Conditional insertion works in sequences and mappings, in templates and in the root file ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/template-expressions?view=azure-devops)). An `else` with no earlier `if` fails "The expression directive 'else' is not supported in this context". Observed: an `else` separated from its `if` by a plain step still binds to it; keep `if`/`elseif`/`else` adjacent.

```yaml
parameters:
  - name: target
    type: string
    default: staging
    values: [dev, staging, prod]
steps:
  - ${{ if eq(parameters.target, 'dev') }}:
      - task: Bash@3
        inputs:
          targetType: inline
          script: |
            set -euo pipefail
            echo dev
  - ${{ elseif eq(parameters.target, 'staging') }}:
      - task: Bash@3
        inputs:
          targetType: inline
          script: |
            set -euo pipefail
            echo staging
  - ${{ else }}:
      - task: Bash@3
        inputs:
          targetType: inline
          script: |
            set -euo pipefail
            echo prod
```

- `${{ insert }}: ${{ parameters.obj }}` merges a mapping into a mapping next to literal keys (works in `variables:` and `env:`). A whole mapping can also be assigned, `env: ${{ parameters.testEnv }}`, which keeps secret mappings identical across steps.

```yaml
parameters:
  - name: testEnv
    type: object
    default:
      API_URL: $(API_URL)
steps:
  - task: Bash@3
    inputs:
      targetType: inline
      script: |
        set -euo pipefail
        ./run-tests.sh
    env:
      OWN: y
      ${{ insert }}: ${{ parameters.testEnv }}
```

- Choosing a variable group at compile time works because `Build.SourceBranch` is known then: `- ${{ if eq(variables['Build.SourceBranch'], 'refs/heads/deploy/dev') }}:` then `- group: x` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)).
- Select a template by parameter, `- template: jobs/${{ parameters.tpl }}.yml@templates`, or wrap `- template:` lines in `${{ if }}`. A macro does not work: `template: $(name).yml` fails "File /.azure/$(name).yml not found".
- Escape a literal `${{`: `${{ 'my${{value' }}` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/template-expressions?view=azure-devops)).

## 6. Templates in other repositories

```yaml
resources:
  repositories:
    - repository: templates
      type: git
      name: Platform/pipeline-templates
      ref: refs/tags/v2.3.0
extends:
  template: pipelines/service.yml@templates
  parameters:
    serviceName: api
```

- `name` is `<project>/<repo>` for Azure Repos (`<repo>` alone for the same project), `<owner>/<repo>` for GitHub with `endpoint`; another organization needs an Azure Repos/TFS service connection in `endpoint` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)). Cross-project within the org resolves at compile time without extra setup; runtime checkout of that repo is a job-token question, see security.md.
- `ref` pins a branch (`refs/heads/x`), tag (`refs/tags/x`) or 40-char commit SHA ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)). A bare name is prefixed with `refs/heads/`, so a bare tag `v1.0.0` fails "Could not get the latest source version for repository <repo> hosted on Azure Repos using ref refs/heads/v1.0.0."; write `refs/tags/...`.
- No `ref`: docs say `refs/heads/main`; observed: the repository's default branch (a `master`-default repo resolved `refs/heads/master`). Always set `ref` for a shared library.
- `ref: ${{ parameters.x }}` and `${{ variables.x }}` work; `ref: $(x)` is not expanded and fails "... using ref refs/heads/$(x).". `name` accepts no expressions ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/resources-repositories-repository?view=azure-pipelines)). The template-expressions page claim that expressions do not work in `repositories` is outdated.
- Repositories are resolved once at run start; only YAML comes from the template repo, and scripts it references are not on the agent unless a step checks that repo out ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)).
- Inside a template from another repo, `checkout: self` still means the pipeline's own repo; `x.yml@self` points back to the consuming repo ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)).
- Repository aliases a template checks out must be declared by the consumer (or by an `extends` template's `resources`); otherwise "Checkout of repository 'tools' is not supported. Only 'self', 'none', or a repository alias are supported." List the required aliases at the top of such a template.
- Protected resources named in the template (variable groups, service connections, environments) are looked up in the consuming pipeline's project and must be authorized there; a group from the template's project fails "Variable group  was not found or is not authorized for use."
- A template missing on the pinned ref fails "File /templates/nope.yaml not found in repository https://dev.azure.com/.../<repo> branch refs/heads/main version <sha>."; the message shows the ref and commit actually used, the fastest way to check a pin.

## 7. Template context: what a template can see

- `parameters`: only the template's own. A root parameter with the same name does not fill it ("A value for the 'project' parameter must be provided." despite a root default).
- `variables` in `${{ }}`: variables defined in YAML so far (entry file and variable templates) plus predefined variables available in templates, such as `Build.SourceBranch`, `Build.Reason` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/template-expressions?view=azure-devops)). Not available: variable-group values, UI/queue-time variables, output variables.
- A macro passed as a parameter stays text (`timeout: $(someMacro)` expands at runtime); it cannot drive `${{ if }}`, `each`, `ref`, template paths or anything compile-time.
- Variables defined inside a template (job or stage `variables:`) are ordinary runtime variables of that scope; a variable template inserts its variables where it is referenced (root, stage or job) ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)).
- A job template with a fixed job name included twice in one stage fails "The job name build appears more than once. Job names must be unique within a pipeline."; once per stage compiles. Derive the name from a parameter: `job: scan_${{ replace(parameters.name, '-', '_') }}`.

## 8. Paths

- A path starting with `/` is from the root of the repo that holds the including file; any other path is relative to the including file, also across repos ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)).
- `x.yml@alias` switches repo; nested relative references inside that file stay in that repo.
- Preview (`scripts/preview.py --yaml`): the override is parsed as if it lived at the host pipeline's YAML path, so relative paths resolve from the host's folder, and templates come from the self repo at `--ref`. To test a new template, push it to a branch and pass `--ref`, or reference an existing file through a repository resource.
- Line numbers in errors point into the file named in the message: `/.azure/azure-pipelines.yaml (Line: 4, Col: 1)` or `/jobs/build.yml@templates (Line: 3, Col: 1)`.

## 9. Limits

From the templates page ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)), not reproduced:

- At most 100 separate YAML files included, directly or indirectly.
- At most 100 levels of template nesting.
- At most 20 MB of memory while parsing, typically 600 KB to 2 MB of YAML on disk; large `each` expansions over big objects are the likely way to hit it (unverified).

## 10. Error messages

Path prefixes shortened.

| Cause | Message |
|---|---|
| Required parameter missing | `A value for the 'project' parameter must be provided.` |
| Undeclared parameter passed | `(Line: 12, Col: 12): Unexpected parameter 'foo'` |
| Value outside `values:` | `The 'reviewDepth' parameter value 'extreme' is not a valid value.` |
| List/map to `string` | `The 'project' parameter is not a valid String.` |
| Bad boolean / number | `The 'build' parameter value 'apples' is not a valid Boolean.` / `... 'abc' is not a valid Number.` |
| Job in a `stepList` | `The 'extra' parameter is not a valid StepList.` + `Unexpected value 'job'` |
| List to `step` | `The 'one' parameter is not a valid Step.` |
| Expression in `default` | `A template expression is not allowed in this context` |
| `each` over a string | `Expected a sequence or mapping. Actual value 'dev'` |
| Object in a string position | `Unable to convert from Object to String. Value: Object` |
| `else` without an `if` | `The expression directive 'else' is not supported in this context` |
| Duplicate injected key | `'timeoutInMinutes' is already defined` |
| Template file missing | `File /templates/nope.yaml not found in repository <url> branch <ref> version <sha>.` |
| Branch or tag missing | `Could not get the latest source version for repository <repo> hosted on Azure Repos using ref <ref>.` |
| Wrong template kind or forbidden key | `<file> (Line: n, Col: 1): Unexpected value 'jobs'` (or `'pool'`, `'pr'`, `'schedules'`, `'trigger'`, `'variables'`) |
| `stages`/`jobs` next to `extends` | `Unexpected value 'jobs'` |
| Undeclared repo alias | `Checkout of repository 'tools' is not supported. Only 'self', 'none', or a repository alias are supported.` |
| Same job twice in a stage | `The job name build appears more than once. Job names must be unique within a pipeline.` |
| Group not in the consuming project | `Variable group  was not found or is not authorized for use.` |
| Environment not found | `Job d: Environment dev could not be found. The environment does not exist or has not been authorized for use.` |
| YAML anchor | `Anchors are not currently supported. Remove the anchor 'x'` |

## 11. Library layout

- Central templates repo; consumers pin `ref: refs/tags/vMAJOR.MINOR.PATCH`. Branch pins (`refs/heads/main`) pick up every change on the next run and cannot be rolled back per consumer; use them only for the library's own test pipelines. A moving major tag (`refs/tags/v2`) works if the library team retags deliberately.
- Breaking changes (bump the major): renaming or removing a parameter (callers fail "Unexpected parameter"), adding a parameter without a default, narrowing `values:`, renaming jobs or stages (breaks callers' `dependsOn` and `dependencies.X.outputs`).
- Layout:

```text
pipeline-templates/
  pipelines/service.yml        # extends entry point: stages, security steps, stepList hooks
  stages/build.yml
  jobs/deploy-webapp.yml
  steps/node-setup.yml
  variables/common.yml
```

- One thin entry file per consumer holding only what cannot live in a template: `trigger`/`pr`/`schedules`, `resources` that must exist for policies or triggers, `pool`, `name`, queue-time parameters, then `extends` with parameters.
- A same-repo template is read from the branch being built, so each branch runs its own copy. A template that diverges across long-lived branches (e.g. a renamed parameter) breaks on the next merge; keep templates identical on branches that run the pipeline, or pin a repository resource to a tag even for the same repo (`ref: ${{ parameters.templatesRef }}`).
- Name files by kind (`*.jobs.yml`, `*.steps.yml`); an `app.yml` containing `jobs:` invites `stages: - template: app.yml`, which fails "Unexpected value 'jobs'".
- Before merging a library change, preview every consumer against the candidate ref: `scripts/preview.py ... --yaml consumer.yml` with the consumer's `ref:` edited to the candidate branch.
