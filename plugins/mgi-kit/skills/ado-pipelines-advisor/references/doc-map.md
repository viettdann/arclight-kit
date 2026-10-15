URL map for live lookups: where each Azure Pipelines fact lives, what to look up there, and how to fetch it.

## Contents

- [How to fetch](#how-to-fetch)
- [Hosted agents and images](#hosted-agents-and-images)
- [Scripts, variables, logging](#scripts-variables-logging)
- [Repositories and checkout](#repositories-and-checkout)
- [Tests and coverage](#tests-and-coverage)
- [YAML schema](#yaml-schema)
- [Process concepts](#process-concepts)
- [Service connections, environments, approvals](#service-connections-environments-approvals)
- [Tasks](#tasks)
- [REST API (read-only use)](#rest-api-read-only-use)
- [Release notes and announcements](#release-notes-and-announcements)

## How to fetch

- Fetch the page from this map or a task's `docs` link in [task-versions.md](task-versions.md), with a WebFetch prompt that extracts just the input or key needed from the `azure-pipelines` moniker block.
- Where docs and observations disagree the references record both; prefer the observation and say so.
- Learn pages (docs, YAML schema, task reference, REST reference, release notes): append `?accept=text/markdown`, or `&accept=text/markdown` when the URL already has a query. Lines end in CRLF (`tr -d '\r'`). Front matter carries `title:`, `description:` and `ms.date`. Pages hold several `::: moniker range="..."` blocks; for Azure DevOps Services read the block whose range includes `azure-pipelines`.
- Keep `?view=azure-devops` (docs) or `?view=azure-pipelines` (schema, tasks) or `?view=azure-devops-rest-7.1` (REST). Without it you may get another product version.
- GitHub files: use `https://raw.githubusercontent.com/<owner>/<repo>/main/<path>` for markdown (for example the runner-images readmes). For issues and releases use `https://api.github.com/repos/<owner>/<repo>/issues/<n>` and `.../releases/latest` (JSON; `.body` is markdown).
- Release notes: the index URL redirects to the roadmap, not a sprint list. Read `toc.json` (see the last table) and select `href` values matching `YYYY/sprint-NNN-update`.
- REST calls against the org: `curl -s -u ":$AZURE_DEVOPS_EXT_PAT" -H 'X-TFS-FedAuthRedirect: Suppress' ...`. That header turns a sign-in redirect into a 401. GET only; the only allowed POST is `scripts/preview.py`.

```bash
set -euo pipefail
curl -sL 'https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps-checkout?view=azure-pipelines&accept=text/markdown' | tr -d '\r' | sed -n '/^\*\*`fetchFilter`/,/^:::/p'
curl -sL 'https://learn.microsoft.com/en-us/azure/devops/release-notes/toc.json' | jq -r '.. | objects | select(.href? // "" | test("^20[0-9]{2}/sprint-[0-9]+-update$")) | .href' | sort -u | tail -5
```

## Hosted agents and images

| URL | Summary |
|---|---|
| https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/hosted?view=azure-devops | Image labels and `vmImage` values, what `-latest` resolves to, VM size, timeouts, IP ranges. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/hosted-deprecation-schedule?view=azure-devops | Deprecation and brownout dates per hosted image (can lag the runner-images announcements). |
| https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md | Preinstalled software and versions on `ubuntu-24.04` (Node, Python, Docker, Azure CLI, cached tools). |
| https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2604-Readme.md | Same for `ubuntu-26.04`; the header links current announcements. |
| https://github.com/actions/runner-images/releases | Image releases with software diffs (when a tool version changed). |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/nodejs-runners?view=azure-devops | Node task-handler support and removal dates on the agent. |
| https://github.com/microsoft/azure-pipelines-agent/releases | Agent release notes: behavior changes by agent version. |

## Scripts, variables, logging

| URL | Summary |
|---|---|
| https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/logging-commands?view=azure-devops | `##vso[...]` commands: `task.setvariable` (`isOutput`, `isSecret`, `isReadonly`), `task.logissue`, `task.complete`, `task.prependpath`, `build.updatebuildnumber`, `build.addbuildtag`, artifact upload. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops | Predefined variables (`Build.*`, `System.*`, `Agent.*`, `Pipeline.*`, `Environment.*`, `Resources.*`), which are available in templates and which are agent-scoped. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops | Defining variables, scopes, the three syntaxes, output variables across jobs and stages, queue-time variables. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-variables-scripts?view=azure-devops | Setting variables and output variables from Bash/PowerShell. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-secret-variables?view=azure-devops | Secret variables, mapping secrets into `env:`, masking. |

## Repositories and checkout

| URL | Summary |
|---|---|
| https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/multi-repo-checkout?view=azure-devops | Several `checkout` steps, path layout (`s/<repo>`), `ref` on repository resources, which repo triggers. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops | Azure Repos triggers (CI, PR through branch policies), shallow fetch and tag defaults, clean, sparse, job authorization scope, protected repositories. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/access-tokens?view=azure-devops | Job access token scope (project vs collection), "Protect access to repositories in YAML pipelines". |

## Tests and coverage

| URL | Summary |
|---|---|
| https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/publish-test-results-v2?view=azure-pipelines | `PublishTestResults@2`: formats (JUnit, NUnit, VSTest, xUnit, CTest), `mergeTestResults`, `failTaskOnFailedTests`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/publish-code-coverage-results-v2?view=azure-pipelines | `PublishCodeCoverageResults@2`: `summaryFileLocation`, any format, no `codeCoverageTool`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/test/review-code-coverage-results?view=azure-devops | Coverage tab, diff coverage on PRs, troubleshooting. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/test/review-continuous-test-results-after-build?view=azure-devops | Tests tab, flaky tests, test analytics. |

## YAML schema

Index: https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/?view=azure-pipelines (every keyword, with the full property list and supported versions).

| URL | Summary |
|---|---|
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/pipeline?view=azure-pipelines | Root: `stages`/`jobs`/`steps`/`extends`, `name`, `appendCommitMessageToRunName`, `lockBehavior`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/stages?view=azure-pipelines | Stage list; links to `stages.stage` and `stages.template`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/stages-stage?view=azure-pipelines | `stage`: `dependsOn`, `condition`, `trigger: manual`, `isSkippable`, `lockBehavior`, `group`, `templateContext`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/jobs?view=azure-pipelines | Job list: `job`, `deployment`, `template`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/jobs-job?view=azure-pipelines | `job`: `strategy` (`matrix`, `parallel`, `maxParallel`), `pool`, `container`, `services`, `workspace`, `timeoutInMinutes`, `uses`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/jobs-deployment?view=azure-pipelines | `deployment`: `environment`, `strategy` (`runOnce`, `rolling`, `canary`) with lifecycle hooks. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/jobs-deployment-strategy?view=azure-pipelines | Deployment strategies and hook order. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/jobs-job-container?view=azure-pipelines | Job `container:` (image name or resource reference). |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps?view=azure-pipelines | Step types: `task`, `script`, `bash`, `pwsh`, `powershell`, `checkout`, `download`, `downloadBuild`, `getPackage`, `publish`, `reviewApp`, `template`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps-task?view=azure-pipelines | `task`: `inputs`, `env`, `condition`, `continueOnError`, `retryCountOnTaskFailure`, `timeoutInMinutes`, `target`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps-checkout?view=azure-pipelines | `checkout`: `fetchDepth`, `fetchFilter`, `fetchTags`, `sparseCheckout*`, `clean`, `lfs`, `submodules`, `path`, `persistCredentials`, `workspaceRepo`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps-download?view=azure-pipelines | `download`: `current`, a pipeline resource, or `none`; `artifact`, `patterns`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/resources-repositories?view=azure-pipelines | Repository resources list. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/resources-repositories-repository?view=azure-pipelines | `repository`: `type`, `name`, `ref` (compile time), `endpoint`, `trigger`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/resources-pipelines?view=azure-pipelines | Pipeline resources list. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/resources-pipelines-pipeline?view=azure-pipelines | `pipeline` resource: `source`, `project`, `branch`, `version`, `tags`, `trigger` (branches, stages, tags). |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/resources-containers-container?view=azure-pipelines | Container resource: `image`, `endpoint`, `options`, `mapDockerSocket`, `mountReadOnly`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/trigger?view=azure-pipelines | CI trigger: `branches`, `paths`, `tags`, `batch`, `none`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/pr?view=azure-pipelines | PR trigger (GitHub, Bitbucket; ignored for Azure Repos Git): `branches`, `paths`, `autoCancel`, `drafts`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/schedules?view=azure-pipelines | Schedule list. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/schedules-cron?view=azure-pipelines | `cron` (UTC), `branches`, `always`, `batch`, `displayName`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/parameters?view=azure-pipelines | Parameter list. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/parameters-parameter?view=azure-pipelines | `parameter`: `type` (`string`, `stringList`, `number`, `boolean`, `object`, `step`/`job`/`stage`/`...List`, `deployment`), `default`, `values`, `displayName`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/variables?view=azure-pipelines | `variables`: map or list form, `name`/`value`, `group`, `template`, `readonly`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/pool?view=azure-pipelines | `pool`: `name`, `vmImage`, `demands`; `pool: server` for agentless jobs. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/extends?view=azure-pipelines | `extends`: `template` and `parameters`. |

## Process concepts

| URL | Summary |
|---|---|
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runs?view=azure-devops | Run sequence: expand templates, evaluate compile-time expressions, plan stages, request agents, run jobs. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops | Expression syntaxes, function catalog (`iif`, `trim`, `split`, `convertToJson`, `counter`, status functions), `dependencies`/`stageDependencies` contexts, type casting. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops | Stage/job/step/variable templates, `extends`, `@repo` references, limits (100 files, 100 nesting levels, 20 MB). |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/template-expressions?view=azure-devops | `${{ }}` in templates: `each`, `if`/`elseif`/`else`, insertion (`${{ insert }}`), escaping. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/template-parameters?view=azure-devops | Template parameters and `templateContext`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions?view=azure-devops | `condition:` on stages, jobs and steps; implicit `succeeded()`; `always()` vs `succeededOrFailed()`; skipped dependencies. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runtime-parameters?view=azure-devops | Queue-time parameters, data types (including `stringList`), `values`, conditionals on parameters, parameter security. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/phases?view=azure-devops | Jobs: agent/agentless/container jobs, `dependsOn`, `matrix`, `parallel` slicing, timeouts, workspace clean, artifact download. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/stages?view=azure-devops | Stages, stage dependencies and conditions, queuing policies. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops | Deployment jobs, strategies, output variable prefixes, auto-injected download. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/container-phases?view=azure-devops | Container jobs, Docker socket mapping, non-root images, `options`. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/resources?view=azure-devops | Resources: repositories, pipelines, containers, packages, webhooks; resource triggers and variables. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/pipeline-triggers?view=azure-devops | Pipeline completion triggers and branch resolution. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/scheduled-triggers?view=azure-devops | Cron schedules, `always`, `batch`, default-branch evaluation. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/release/caching?view=azure-devops | `Cache@2`: keys, `restoreKeys`, `cacheHitVar`, scopes per branch/PR, per-tool examples. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/artifacts/pipeline-artifacts?view=azure-devops | Publish and download pipeline artifacts, `.artifactignore`. |

## Service connections, environments, approvals

| URL | Summary |
|---|---|
| https://learn.microsoft.com/en-us/azure/devops/pipelines/library/service-endpoints?view=azure-devops | Service connection types, security (pipeline permissions, approvals on connections). |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/library/connect-to-azure?view=azure-devops | Azure Resource Manager connections; workload identity federation recommended, other auth kept for compatibility. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/release/configure-workload-identity?view=azure-devops | Manual WIF setup: issuer, subject, federated credential on an app or managed identity. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/environments?view=azure-devops | Environments, resources (Kubernetes, VM), deployment history, security. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops | Approvals and checks: approvals, branch control, business hours, exclusive lock, invoke REST/Azure Function, required template, evaluation order. |
| https://learn.microsoft.com/en-us/azure/devops/pipelines/security/overview?view=azure-devops | Pipeline security guidance: templates, secrets, forks, resources. |

## Tasks

| URL | Summary |
|---|---|
| https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/?view=azure-pipelines | Task index: every built-in `Name@N` with a link to its inputs page, grouped by category, deprecated majors marked. Source for `scripts/task-versions.py refresh`. |
| https://github.com/microsoft/azure-pipelines-tasks | Task source; `Tasks/<Name>V<N>/task.json` has inputs, aliases and Node handlers. Raw files are on raw.githubusercontent.com. |

## REST API (read-only use)

Index: https://learn.microsoft.com/en-us/rest/api/azure/devops/?view=azure-devops-rest-7.1 (auth, versioning, URL shape). Organization base: `https://dev.azure.com/{org}/{project}/_apis/...`.

| URL | Summary |
|---|---|
| https://learn.microsoft.com/en-us/rest/api/azure/devops/build/builds?view=azure-devops-rest-7.1 | Builds area operations. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/build/builds/list?view=azure-devops-rest-7.1 | `GET _apis/build/builds?definitions=&$top=&statusFilter=&queryOrder=`: last N runs of a definition. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/build/builds/get?view=azure-devops-rest-7.1 | One build: `queueTime`, `startTime`, `sourceBranch`, `sourceVersion`, `reason`, `triggerInfo`. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/build/timeline?view=azure-devops-rest-7.1 | Timeline area. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/build/timeline/get?view=azure-devops-rest-7.1 | `GET _apis/build/builds/{id}/timeline`: stage/phase/job/task records with times, results, `log.id`. Basis of the measurement snippet in [performance.md](performance.md#1-measure-a-pipeline). |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/build/builds/get-build-logs?view=azure-devops-rest-7.1 | `GET _apis/build/builds/{id}/logs`: list logs. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/build/builds/get-build-log?view=azure-devops-rest-7.1 | `GET _apis/build/builds/{id}/logs/{logId}`: plain-text log of one step (checkout flags, cache hit/miss). |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/build/definitions/get?view=azure-devops-rest-7.1 | One definition: YAML path, repository, `repository.properties.fetchDepth` (the shallow-fetch setting). |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/build/definitions/list?view=azure-devops-rest-7.1 | List definitions; `includeAllProperties=true` returns repository properties. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/pipelines/list?view=azure-devops-rest-7.1 | `GET _apis/pipelines`: pipeline ids and folders. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/runs?view=azure-devops-rest-7.1 | Runs area (Get, List, Run Pipeline). |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/runs/get?view=azure-devops-rest-7.1 | `GET _apis/pipelines/{id}/runs/{runId}`: `resources.repositories.*.refName`/`version`, `templateParameters`, `variables`. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/runs/list?view=azure-devops-rest-7.1 | `GET _apis/pipelines/{id}/runs`: up to 10000 runs. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/runs/run-pipeline?view=azure-devops-rest-7.1 | `POST .../runs`: queues a run. Never call it from this skill; body schema shared with Preview. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/preview?view=azure-devops-rest-7.1 | Preview area. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/preview/preview?view=azure-devops-rest-7.1 | `POST _apis/pipelines/{id}/preview` with `previewRun: true`: returns `finalYaml`, nothing queued. Wrapped by `scripts/preview.py`. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/logs?view=azure-devops-rest-7.1 | Pipelines logs area. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/logs/list?view=azure-devops-rest-7.1 | `GET _apis/pipelines/{id}/runs/{runId}/logs`: logs with signed download URLs (`$expand=signedContent`). |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/logs/get?view=azure-devops-rest-7.1 | One log of a run. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/distributedtask?view=azure-devops-rest-7.1 | Agents, pools, queues, variable groups, environments, task groups. The undocumented `GET https://dev.azure.com/{org}/_apis/distributedtask/tasks` lists installed task versions with `deprecated` and `preview` flags. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/distributedtask/variablegroups?view=azure-devops-rest-7.1 | Variable groups (names and non-secret values). |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/distributedtask/environments?view=azure-devops-rest-7.1 | Environments and deployment records. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/policy/configurations?view=azure-devops-rest-7.1 | Policy configurations area. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/policy/configurations/list?view=azure-devops-rest-7.1 | `GET _apis/policy/configurations`: build validation policies (`settings.buildDefinitionId`, `filenamePatterns` = path filter, `scope` = branch). This is where Azure Repos PR triggers really live. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/approvalsandchecks?view=azure-devops-rest-7.1 | Approvals and checks area. |
| https://learn.microsoft.com/en-us/rest/api/azure/devops/approvalsandchecks/check-configurations?view=azure-devops-rest-7.1 | Checks configured on environments, service connections, repositories. |

## Release notes and announcements

| URL | Summary |
|---|---|
| https://learn.microsoft.com/en-us/azure/devops/release-notes/toc.json | Sprint pages follow `release-notes/YYYY/sprint-NNN-update`; list them from this file (`href`, date in `toc_title`) and read the latest. |
| https://github.com/actions/runner-images/issues?q=label%3Aannouncement | Hosted image label moves, GA, deprecations and breaking tool changes; check "Platforms affected" for Azure DevOps. |
