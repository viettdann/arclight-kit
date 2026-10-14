# Review checklist

Walk this list in Review mode and Optimize mode. Each item says how to detect it, its default severity, the fix, and where the rule and its source live. Raise or lower a severity when the context warrants it (a deploy step, a prod branch, a PR-only pipeline) and say why.

## Contents

1. [Severity rubric](#severity-rubric)
2. [How to run a review](#how-to-run-a-review)
3. [Compile-time failures](#compile-time-failures)
4. [Correctness](#correctness)
5. [Triggers](#triggers)
6. [Security](#security)
7. [Deployment](#deployment)
8. [Performance](#performance)
9. [Maintainability and defaults](#maintainability-and-defaults)
10. [Finding format](#finding-format)

## Severity rubric

| Severity | Meaning | Examples |
|---|---|---|
| Critical | The pipeline does not compile, leaks a secret, or lets untrusted code reach credentials or production | anchor in YAML, `ManualValidation@1` in an agent job, secret literal, fork builds with secrets |
| High | Runs but does the wrong thing silently, or removes a security control | custom condition without `succeeded()`, output variable read with the wrong key, secret expected in env without `env:`, prod deploy in a plain job |
| Medium | Works today but is fragile, wasteful by a measured amount, or misleading to the next reader | `pr:` on Azure Repos, cache without a measurement, `fetchDepth: 0` without a reason, unpinned template repo |
| Low | Deviates from the defaults or house style without changing behavior | `script:` shortcut, outdated but supported task major, missing `timeoutInMinutes` |

## How to run a review

1. `scripts/task-versions.py check <file>...` for task majors, deprecated tasks, renamed or removed inputs, unlisted tasks, shortcut steps. Unlisted in-house or Marketplace tasks: `scripts/task-versions.py org --org <org>`. Pasted YAML: save it to a temp file for the check and report `detect.py` as not run.
2. `scripts/preview.py ... --yaml <file>` when a token is available: a 400 is a Critical finding with the server message; a clean result proves template expansion only, not runtime behavior (`$[ ]` placement and conditions are not checked by preview).
3. Read the YAML against the tables below. Include templates the file references; a finding in a template names the template file.
4. Report findings in the [format](#finding-format), most severe first. Say what you could not check (runtime-only behavior, branch policies, UI settings) instead of guessing.

## Compile-time failures

All Critical. Preview reports them with the message shown, so quote it.

| ID | Detect | Fix | Rule |
|---|---|---|---|
| X1 | YAML anchor or alias (`&x`, `*x`, `<<:`) | Repeat the value, or a template/parameter | "Anchors are not currently supported" ([templates.md](templates.md#10-error-messages), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/?view=azure-pipelines)) |
| X2 | `ManualValidation@1` (or any agentless task) in a job without `pool: server` | Own job with `pool: server` | "not valid for the given job target" ([deployment.md](deployment.md#manualvalidation-in-an-agentless-job), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/manual-validation-v1?view=azure-pipelines)) |
| X3 | `steps:` directly under `deployment:` | `strategy: runOnce: deploy: steps:` | "Unexpected value 'steps'" ([deployment.md](deployment.md#deployment-jobs), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/jobs-deployment?view=azure-pipelines)) |
| X4 | Top-level `pool`, `pr`, `schedules` in a template; `trigger` in an include template | Move to the entry file or onto jobs | "Unexpected value 'pool'" ([templates.md](templates.md#1-kinds-of-template-and-what-a-template-file-may-contain), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)) |
| X5 | Parameter without `default` in a pipeline with CI, schedule or completion triggers | Add a default; string defaults cannot be `''` if users run it from the UI, use `' '` and `trim()` | "A value for the 'x' parameter must be provided" ([execution-model.md](execution-model.md#queue-time-values), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runtime-parameters?view=azure-devops)) |
| X6 | `iif()` with two arguments | Pass three | "Unexpected symbol" ([expressions-conditions.md](expressions-conditions.md#function-catalog), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)) |
| X7 | Template or `@alias` that does not exist at the resolved ref; relative path wrong for the including file | Fix the path (relative to the including file, `/` for repo root) or the `ref` | "File ... not found in repository ... branch ..." ([templates.md](templates.md#8-paths), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops)) |
| X8 | Parameter value outside `values:`, wrong type, unknown parameter passed to a template | Match the declaration | "is not a valid ..." ([templates.md](templates.md#10-error-messages), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/template-parameters?view=azure-devops)) |
| X9 | Compile-time use of runtime-only functions (`succeeded()`, `counter()`, `dependencies`) inside `${{ }}` | Runtime expression or condition | "Unrecognized value" ([expressions-conditions.md](expressions-conditions.md#literals-and-contexts), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)) |

## Correctness

| ID | Detect | Sev | Fix | Rule |
|---|---|---|---|---|
| C1 | `condition:` without a status function (`succeeded()`, `failed()`, `always()`, `not(canceled())`, `dependencies.X.result`) | High | `and(succeeded(), <custom>)` | Custom condition replaces the implicit `succeeded()` ([expressions-conditions.md](expressions-conditions.md#conditions), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions?view=azure-devops)) |
| C2 | Output variable key that does not match the producer: deployment job without the `<job>.` or `Deploy_<resource>.` prefix, matrix without `<leg>.`, `stageDependencies` in a stage condition, `dependencies.<stage>` in a job, consumer without direct `dependsOn` on the producer, producer step without `name:` or `isOutput=true` | High | Use the [output variable matrix](expressions-conditions.md#output-variable-matrix); dump `convertToJson(dependencies)` when unsure | Silently empty ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)) |
| C3 | `$(var)` in a compile-time position: `trigger`, `pr`, `schedules`, `resources` (incl. `ref:`), `- group:`, `checkout: git://...@$(x)`, template paths, `environment` from a group value | High | `${{ parameters.x }}` or `${{ variables.x }}` over a literal variable | Macros are not expanded there ([execution-model.md](execution-model.md#where-macros-and-runtime-expressions-are-not-expanded), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)) |
| C4 | `$[ ]` that is not the entire value, or used in a task input | High | Whole value inside `variables`, then `$(thatVar)`; `format()` for composites | Runtime expression must be the entire value; preview does not catch it ([execution-model.md](execution-model.md#the-three-syntaxes), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)) |
| C5 | `${{ variables.x }}` where `x` comes from a variable group, a `$[ ]`, a `setvariable`, or a runtime-only predefined variable (`Build.BuildId`, `System.PullRequest.PullRequestId`, `System.AccessToken`) | High | Runtime condition or `$(x)`; or a parameter | Empty or the unevaluated text at compile time ([execution-model.md](execution-model.md#availability-matrix), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops)) |
| C6 | Boolean parameter compared to `'true'`/`'false'` strings | High | Bare `${{ if parameters.flag }}` or `eq(parameters.flag, true)` | `'false'` casts to True ([expressions-conditions.md](expressions-conditions.md#type-casting), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)) |
| C7 | Inline script with more than one command and no `set -euo pipefail` | Medium; High before a deploy/publish/push | First line `set -euo pipefail` | `Bash@3` and `CmdLine@2` run bash without errexit (observed in run logs) ([execution-model.md](execution-model.md#undefined-variables), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/bash-v3?view=azure-pipelines)) |
| C8 | `export VAR=$(cmd)` or `local v=$(cmd)` relying on `set -e` | Medium | Assign, then export | The builtin's status hides `cmd`'s failure ([deployment.md](targets/terraform.md), [source](https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html)) |
| C9 | `$(maybeUnset)` inside a bash script body | Medium | Declare a default variable, map it with `env:`, read `${VAR:-}` | Undefined macro stays literal and bash runs it as command substitution ([execution-model.md](execution-model.md#undefined-variables), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)) |
| C10 | Secret or `System.AccessToken` read from the environment without an `env:` mapping on that step | High | `env: NAME: $(secret)` | Secrets are not exported ([security.md](security.md#secret-variables-and-masking), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-secret-variables?view=azure-devops)) |
| C11 | `succeededOrFailed()` after a dependency that can be skipped | Medium | `not(canceled())` or test `dependencies.X.result` including `Skipped` | Skip cascades ([expressions-conditions.md](expressions-conditions.md#conditions), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)) |
| C12 | Stage condition that reads that stage's own `variables:` or group | Medium (verify) | Gate on root variables, upstream outputs, or `${{ if }}` | Condition runs before the stage; behavior for stage variables is unverified ([expressions-conditions.md](expressions-conditions.md#stage-conditions-and-stage-variables), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runs?view=azure-devops)) |
| C13 | Versions compared as strings (`gt(variables.v, '1.9.0')`) | Medium | Version literals or split numbers | String order ([expressions-conditions.md](expressions-conditions.md#type-casting), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)) |
| C14 | `UseNode@1` without `version`, or `NodeTool@0` | High | `UseNode@1` with `version: '24.x'` unless the repo pins one | Default is `10.x`; NodeTool@0 deprecated ([task-versions.md](task-versions.md#table), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/use-node-v1?view=azure-pipelines)) |
| C15 | Deprecated task or major, removed input (`check` reports `deprecated`, `renamed-input`, `removed-input`) | High | The replacement in task-versions.md | ([task-versions.md](task-versions.md#table), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/?view=azure-pipelines)) |
| C16 | Task major whose handler is Node 6/10/16 only | High | Latest major (Node24 handler) | Handlers removed from the agent on 2026-11-24 ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/nodejs-runners?view=azure-devops), [source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2026/sprint-279-update#test-pipeline-tasks-without-unsupported-nodejs-runners)) |
| C17 | `Docker@2` `buildAndPush` with `arguments` | High | `build` + `push`, or buildx from `Bash@3` | `arguments` is ignored for buildAndPush ([deployment.md](targets/acr.md), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/docker-v2?view=azure-pipelines)) |
| C18 | Linux container job that runs `docker` without `mapDockerSocket: true` | High | Set it on the container resource, or build outside the container | Not mounted from agent 5.279.0 ([security.md](security.md#container-jobs), [source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2026/sprint-279-update)) |
| C19 | Cross-repo build validation that derives the PR repo from `Build.Repository.*`, `System.TeamProject` or a task input's default | High | Pass the target project and repo explicitly | Those describe the runner repo/project ([triggers.md](triggers.md#cross-repo-build-validation-cross-run), observed) |
| C20 | `templateParameters`/`--param` for an `object` or `stringList` sent as a JSON array or object | High | Send YAML or JSON text | Arrays are ignored silently, objects fail (verified with preview.py, [source](https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/preview/preview?view=azure-devops-rest-7.1)) |
| C21 | Same variable name in two groups, or a group and inline variable, at one scope | Medium | Unique names, or intended winner last | Last wins, "may be unpredictable" ([execution-model.md](execution-model.md#precedence-and-collisions), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/variable-groups?view=azure-devops)) |
| C22 | Stage or job with no `dependsOn` and a default or `succeeded()` condition after a stage that can be skipped (PR-only validation, `${{ if }}`-gated, manual) | High | Explicit `dependsOn` on the stages it really needs, or `in(dependencies.X.result, 'Succeeded', 'Skipped')` | The implicit dependency on the previous stage makes it skip too, so e.g. push to main never builds or deploys ([expressions-conditions.md](expressions-conditions.md#conditions), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/stages?view=azure-devops)) |

## Triggers

| ID | Detect | Sev | Fix | Rule |
|---|---|---|---|---|
| T1 | `pr:` block on an Azure Repos Git pipeline | Medium | `pr: none` or remove; filters go into the Build validation policy | Ignored on Azure Repos ([triggers.md](triggers.md#pr-triggers), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/pr?view=azure-pipelines)) |
| T2 | No `trigger:` on a PR-only, scheduled, completion-triggered or deploy pipeline | High for deploys, else Medium | `trigger: none` | Implied CI on every branch unless disabled at org/project ([triggers.md](triggers.md#ci-triggers), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops)) |
| T3 | `trigger`, `schedules` or pipeline-resource `trigger` inside a template | Medium | Move to the entry file | Only the root file's triggers count ([triggers.md](triggers.md#ci-triggers), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/pipeline-triggers?view=azure-devops)) |
| T4 | Schedule whose output depends on external state without `always: true` | Medium | `always: true` | Skipped when no commit since the last successful scheduled run ([triggers.md](triggers.md#scheduled-triggers), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/scheduled-triggers?view=azure-devops)) |
| T5 | Cron that looks like local time, no UTC comment | Low | UTC value with the local time in a comment | Cron is UTC ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/scheduled-triggers?view=azure-devops)) |
| T6 | Completion trigger expected to filter on paths, or downstream pipeline with its own CI trigger in the same repo | Medium | Filter upstream or in a condition; `trigger: none` downstream | No path filter on completion triggers ([triggers.md](triggers.md#pipeline-completion-triggers), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/pipeline-triggers?view=azure-devops)) |
| T7 | YAML `trigger.paths` and the branch policy path filter disagree, or a policy path not starting with `/` or `*` | Medium | Align them | Independent filters ([triggers.md](triggers.md#build-validation-branch-policy), [source](https://learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies?view=azure-devops)) |
| T8 | Cross-repo build validation without the PR repo declared under `resources.repositories` | Critical | Declare it; add `uses: repositories: [alias]` to the job | Required for the policy and the token scope ([triggers.md](triggers.md#cross-repo-build-validation-cross-run), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/multi-repo-checkout?view=azure-devops)) |
| T9 | Cross-repo run fetching `System.PullRequest.SourceRepositoryUri` | Medium | Fetch `refs/pull/<id>/merge` from the target repo URL | Points at the fork for fork PRs ([triggers.md](triggers.md#cross-repo-build-validation-cross-run)) |

## Security

| ID | Detect | Sev | Fix | Rule |
|---|---|---|---|---|
| S1 | Secret, PAT, key or connection string literal in YAML or a committed file | Critical | Key Vault-linked group; rotate the value | ([security.md](security.md#secret-variables-and-masking), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/secrets?view=azure-devops)) |
| S2 | GitHub fork PR builds with secrets or "same permissions as regular builds" | Critical | Turn both off; require a comment | ([security.md](security.md#fork-pull-requests), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/github?view=azure-devops)) |
| S4 | Secret as a CLI argument, `$(secret)` inline in a script, a secret in `${{ }}` or a runtime parameter | High | `env:` mapping | Lands in process listings, script files or expanded YAML ([security.md](security.md#secret-variables-and-masking), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-secret-variables?view=azure-devops)) |
| S5 | Derived secret (base64 Basic header, JSON with a token) printed, or `set -x`/`curl -v` near secrets | High | `##vso[task.setsecret]` first; no tracing | Only exact forms are masked ([security.md](security.md#secret-variables-and-masking), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/logging-commands?view=azure-devops)) |
| S6 | `persistCredentials: true` in a job with later third-party or untrusted steps | High | Per-command `git -c http.extraheader=...` | Token stays in `.git/config` ([security.md](security.md#checkout-credentials), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps-checkout?view=azure-pipelines)) |
| S7 | ARM service connection with a secret or certificate; registry admin user/password (`ACR_USER`/`ACR_PASS`) | High | WIF connection; managed identity pull | ([security.md](security.md#workload-identity-federation), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/connect-to-azure?view=azure-devops)) |
| S8 | Protected resources opened to all pipelines; subscription-wide Contributor | High | Per-pipeline permissions; resource-group scope | ([security.md](security.md#service-connection-hygiene), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/service-endpoints?view=azure-devops)) |
| S9 | Step printing untrusted text (PR titles, API or LLM output) without `target.commands: restricted` | Medium | `commands: restricted` + `settableVariables` | Logging-command injection ([security.md](security.md#templates-checks-and-step-restrictions), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/target?view=azure-pipelines)) |
| S10 | `AzureKeyVault@2` with `SecretsFilter: '*'` or `RunAsPreJob: true` without need | Medium | List the names | ([security.md](security.md#key-vault), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-key-vault-v2?view=azure-pipelines)) |
| S11 | Queue-time variable feeding a script | Medium | Typed runtime parameter with `values:` | ([security.md](security.md#secret-variables-and-masking), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/inputs?view=azure-devops)) |
| S12 | Security enforced only by a YAML `condition` or `ManualValidation@1` | Medium | Checks on the resource (branch control, required template, approval) | YAML can be edited by the PR ([security.md](security.md#fork-pull-requests), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops)) |

## Deployment

| ID | Detect | Sev | Fix | Rule |
|---|---|---|---|---|
| D1 | Deploy, migrate or publish steps in a plain `job:` | High for prod, Medium otherwise | `deployment:` job on an `environment` with checks | Only deployment jobs get environment approvals, locks and history ([deployment.md](deployment.md#deployment-jobs), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)) |
| D2 | Prod stage without branch condition or branch control | High | `eq(variables['Build.SourceBranch'], 'refs/heads/main')` plus Branch control check | ([deployment.md](deployment.md#promotion-dev-to-prod), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops)) |
| D3 | Stateful step (migration, terraform apply) without `lockBehavior: sequential` or an exclusive lock | Medium | `lockBehavior: sequential` on the stage | ([deployment.md](deployment.md#approvals-checks-and-locks), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops)) |
| D4 | Image or package rebuilt per environment instead of promoted | Medium | Build once, promote the same tag or artifact | Prod runs what was tested ([deployment.md](deployment.md#promotion-dev-to-prod)) |
| D5 | Deployment job relying on repo files without `- checkout: self` | High | Add the checkout | Deployment jobs do not clone ([deployment.md](deployment.md#deployment-jobs), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)) |
| D6 | Deployment job downloading every artifact implicitly | Low | `- download: current` with `artifact:`, or `download: none` | ([deployment.md](deployment.md#deployment-jobs), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps-download?view=azure-pipelines)) |
| D7 | Deploy without a post-deploy health check, or one that only waits for HTTP 200 of any version | Medium | Health check that asserts the deployed version | ([deployment.md](deployment.md#post-deploy-health-check)) |
| D8 | Deploy via CLI where the target's deploy task works (`AzureWebApp@1`, `AzureWebAppContainer@1`, `AzureFunctionApp@2`, `AzureResourceManagerTemplateDeployment@3`) | Low | The deploy task | Default 1 ([deployment.md](deployment.md#targets)) |
| D9 | Terraform through the DevLabs Marketplace task, or plan and apply in one unapproved job | Medium | CLI from `AzureCLI@3` with WIF; plan artifact, approval, apply | ([deployment.md](targets/terraform.md), [source](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/service_principal_oidc)) |

## Performance

Back every performance finding with `scripts/step-durations.py` numbers, or say it is unmeasured.

| ID | Detect | Sev | Fix | Rule |
|---|---|---|---|---|
| P1 | `Cache@2` with no recorded before/after measurement | Medium | Measure hit rate, hit cost, miss cost, baseline; delete it if it does not win | Default 4 ([performance.md](performance.md#2-cache2-measure-before-adding), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/caching?view=azure-devops)) |
| P2 | `Cache@2` on `node_modules` followed by `npm ci` | Medium | Cache the npm download cache or drop the cache | `npm ci` deletes `node_modules` ([performance.md](performance.md#2-cache2-measure-before-adding), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/caching?view=azure-devops)) |
| P3 | `fetchDepth` or `fetchTags` not set; `fetchDepth: 0` without a stated reason | Medium | `fetchDepth: 1` (or the history the step needs), `fetchTags: false`; try `fetchFilter: tree:0` | Defaults vary per definition (observed full clones and `--tags`) ([performance.md](performance.md#3-checkout), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps-checkout?view=azure-pipelines)) |
| P4 | Job that never reads the repo but checks it out | Low | `checkout: none` | ([performance.md](performance.md#3-checkout)) |
| P5 | Path gating in YAML `pr:` on Azure Repos, or a Detect job whose own cost exceeds what it skips | Medium | Policy path filter; cheaper Detect (`fetchDepth: 2`) | ([performance.md](performance.md#4-skip-work-path-filters-and-detect-gating)) |
| P6 | Extra jobs whose fixed cost (init + checkout + install) exceeds the work they parallelize | Medium | Merge jobs or cut fixed cost | ([performance.md](performance.md#5-jobs-matrix-parallel-slicing-fan-out-job-cost)) |
| P7 | Large artifacts, build artifacts (`PublishBuildArtifacts@1`), no `.artifactignore` | Low | `PublishPipelineArtifact@1`, minimal path, `.artifactignore` | ([performance.md](performance.md#6-artifacts), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/artifacts/pipeline-artifacts?view=azure-devops)) |
| P8 | Job without `timeoutInMinutes` | Low | Set one near 2× the p95 | Default 60 min on hosted agents ([performance.md](performance.md#8-timeouts-and-workspace), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/phases?view=azure-devops)) |

## Maintainability and defaults

| ID | Detect | Sev | Fix | Rule |
|---|---|---|---|---|
| M1 | `script:`, `bash:`, `pwsh:`, `powershell:` step shortcuts (`check` reports `shortcut`) | Low | `Bash@3` `targetType: inline` or `CmdLine@2` | Default 2 |
| M2 | Task major below latest, not deprecated (`check` reports `outdated`) | Low | Bump after reading the latest major's inputs, or keep with a reason | Default 5 ([task-versions.md](task-versions.md)) |
| M3 | CLI step where a native task covers the case and has not been shown to fail on it | Low | The task | Default 1; CLI is the fallback when no task exists or the task is wrong or fails |
| M5 | Template from another repo without a pinned `ref` (tag or SHA) | Medium | `ref: refs/tags/vN` | Without `ref` the repo's default branch is used (verified with preview.py) ([templates.md](templates.md#6-templates-in-other-repositories)) |
| M6 | Same template file diverging across long-lived branches | Medium | One source (template repo or merge back) | ([templates.md](templates.md)) |
| M7 | Copy-pasted stages or jobs differing only by environment | Low | Stage/job template with parameters, `each` over an `object` | ([templates.md](templates.md#4-each)) |
| M8 | Linux image other than `ubuntu-26.04`, `ubuntu-24.04` or `ubuntu-latest` (e.g. `ubuntu-22.04`, deprecated, retired 2027-04-17) | Medium | `ubuntu-26.04` | Never flag or recommend changing `ubuntu-latest` or `ubuntu-24.04` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/hosted?view=azure-devops), [source](https://github.com/actions/runner-images/issues/14254)) |
| M9 | Comments that restate self-explanatory YAML, or wrong comments (claims contradicted by docs or runs) | Low | Delete or correct; keep comments on non-obvious constraints | |
| M10 | Unquoted booleans in string contexts (`CI: true` reaches the process as `True`) | Low | Quote: `'true'` | ([templates.md](templates.md)) |

## Finding format

Group by severity, most severe first. One finding per item:

```text
[High] C1 azure-pipelines.yml:42 (stage Deploy)
  condition: eq(variables['Build.SourceBranch'], 'refs/heads/main')
  Runs after a failed or canceled Build stage, because a custom condition replaces succeeded().
  Fix: condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
  Rule: expressions-conditions.md#conditions
```

- Quote the offending line exactly, with its line number (`task-versions.py check` prints line numbers).
- Give a fix that can be pasted. When several items share one root cause, report it once and list the lines.
- End with one line on what was not checked (runtime-only behavior, branch policies, UI settings, unlisted tasks) and, for Optimize, the measurements used.
