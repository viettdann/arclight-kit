# Deployment

Deployment jobs, environments, checks and locks, and an index of the per-target patterns in `targets/` (Azure DevOps Services, Microsoft-hosted Linux agents).

## Contents

1. [Deployment jobs](#deployment-jobs)
2. [Strategies and lifecycle hooks](#strategies-and-lifecycle-hooks)
3. [Environments](#environments)
4. [Approvals, checks and locks](#approvals-checks-and-locks)
5. [ManualValidation in an agentless job](#manualvalidation-in-an-agentless-job)
6. [Output variables out of deployment jobs](#output-variables-out-of-deployment-jobs)
7. [Promotion dev to prod](#promotion-dev-to-prod)
8. [App configuration from variables](#app-configuration-from-variables)
9. [Targets](#targets): one file per target under `targets/`
10. [Post-deploy health check](#post-deploy-health-check)
11. [Container jobs that run docker](#container-jobs-that-run-docker)

## Deployment jobs

A deploy step belongs in a `deployment:` job, not a plain `job:`. Only a deployment job records deployment history on an environment, and only a stage that uses an environment waits for its approvals and checks ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops)).

| Rule | Detail |
|---|---|
| Shape | `deployment:` + `environment:` + `strategy:` with at least one hook; `steps:` directly under the job fails with "Unexpected value 'steps'" ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/jobs-deployment?view=azure-pipelines)) |
| Name | A-Z, a-z, 0-9, `_`. Avoid `deploy`: the schema reserves it, and a clash can leave the run stuck at "Job is pending" even though it compiles ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)) |
| No checkout | A deployment job does not clone the repo. Add `- checkout: self` when the deploy needs repo files (IaC, scripts) ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)) |
| Automatic download | The `deploy` hook (and only that hook) gets an injected download of every artifact of the current run and of every `resources.pipelines` resource. Use `- download: none`, or `- download: current` with `artifact:` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps-download?view=azure-pipelines)) |
| Artifact path | Current run: `$(Pipeline.Workspace)/<artifact>`. Pipeline resource: `$(Pipeline.Workspace)/<resource alias>/<artifact>` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps-download?view=azure-pipelines)) |
| Workspace | `$(Pipeline.Workspace)`. `workspace: clean: all` only matters on self-hosted agents ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)) |
| Pool | Hooks inherit the job `pool`. VM-resource environments need no pool (steps run on the VM); Kubernetes resources need one ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)) |
| Variables | `Environment.Name`, `Environment.Id`, `Strategy.Name` exist inside the job ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops)) |

Wrong: no approval can gate it and the environment shows no history.

```text
- stage: Deploy
  jobs:
  - job: DeployAppService
    steps:
    - checkout: none
    - task: AzureWebAppContainer@1
```

Fix:

```yaml
stages:
- stage: Deploy
  jobs:
  - deployment: DeployAppService
    environment: app-prod
    strategy:
      runOnce:
        deploy:
          steps:
          - download: none
          - task: AzureWebAppContainer@1
            inputs:
              azureSubscription: sc-app-prod
              appName: app-api-prod
              containers: myacr.azurecr.io/api:$(Build.BuildId)
```

## Strategies and lifecycle hooks

| Strategy | Targets | Hooks and order | Notes |
|---|---|---|---|
| `runOnce` | Anything, resource-less included | `preDeploy`, `deploy`, `routeTraffic`, `postRouteTraffic` once each, then `on: success` or `on: failure` | Default for App Service, Functions, Bicep, Terraform, SSH ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)) |
| `rolling` | VM resources only | Same hooks, run per batch of `maxParallel` VMs (number or `x%`) | Retrying a stage redeploys every VM, not only failed ones ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)) |
| `canary` | Kubernetes | `preDeploy` once; `deploy`/`routeTraffic`/`postRouteTraffic` per entry of `increments: [10, 20]`; then success/failure | `strategy.action`, `strategy.increment` feed `KubernetesManifest@1` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)) |

Each hook becomes its own agent or server job, chosen by the hook's `pool` (`pool: server` makes it agentless) ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)). Use `postRouteTraffic` for the health check and `on: failure` for rollback, for example a slot swap back.

## Environments

| Kind | When | Syntax | Behavior |
|---|---|---|---|
| Resource-less | App Service, Functions, SWA, Bicep, Terraform, SSH targets: the common case here | `environment: app-prod` | Holds approvals, checks, permissions and deployment history ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/environments?view=azure-devops)) |
| VM resource | Agent registered on the VM | `environment: {name: app-prod, resourceType: VirtualMachine, tags: web}` | Steps run on the VM; enables `rolling` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)) |
| Kubernetes resource | AKS namespace | `environment: app-prod.bookings` | Tasks inherit the cluster connection from the resource ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/environments?view=azure-devops)) |

- A dot means `environment.resource`: `app.prod` targets resource `prod` in environment `app`. A missing resource fails expansion with "Resource nosuchresource does not exist in environment staging." ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/jobs-deployment-environment?view=azure-pipelines)).
- A missing environment is created on the first run when the queuing user is known, and the pipeline fails otherwise ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/environments?view=azure-devops)). Create prod environments by hand, with their approvals, before the first run can auto-create an unprotected one.
- Choose the environment name with a parameter or `${{ }}`. `environment: $(envName)` resolves only when `envName` is a YAML variable; otherwise the literal `$(envName)` is looked up ("Environment $(envName) could not be found") or auto-created under that literal name.
- Restrict **Pipeline permissions** on prod environments. The first run of a new pipeline then waits for a one-time "Permit" ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/environments?view=azure-devops)).

## Approvals, checks and locks

Checks are set on the resource in the web UI, never in YAML, so editing the YAML cannot remove them. They can sit on environments, service connections, repositories, variable groups, secure files and agent pools; a stage starts only after every check on every resource it uses passes ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops)).

| Check | Use | On timeout |
|---|---|---|
| Approvals | Prod gate; one member of an approver group is enough; can block self-approval; can be deferred | Stage skipped |
| Business hours | Deploy windows | Stage failed |
| Branch control | Only `refs/heads/main` (fully qualified) may use the resource | Stage failed |
| Required template | The pipeline must `extends:` a given template (typically set on service connections) | Pipeline fails |
| Invoke Azure Function / Invoke REST API | External gate (change ticket, scanner); a non-zero "time between evaluations" makes the decision non-final | Stage skipped |
| Query Azure Monitor alerts | Block promotion while alerts fire | Stage failed |
| Exclusive lock | One run at a time on the resource; paired with `lockBehavior` | - |

Order of evaluation: static checks (branch control, required template, evaluate artifact), pre-check approvals, dynamic checks, post-check approvals, exclusive lock. Checks see only predefined variables; to pass an earlier stage's output to a check, write it to a linked variable group ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops)).

`lockBehavior` (pipeline root or stage) decides how runs queue behind an exclusive lock ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/stages-stage?view=azure-pipelines)):

| Value | Effect | Use for |
|---|---|---|
| `runLatest` (default) | Only the newest waiting run gets the lock; older waiting runs are canceled | Cumulative releases (app images) |
| `sequential` | Every run takes the lock in turn | Non-cumulative changes: Terraform, DB migrations |

A `lockBehavior` on a stage creates a stage-level lock by itself, with no environment check needed; at stage level `runLatest` cancels only runs of the same branch ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/stages-stage?view=azure-pipelines), [source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2024/sprint-243-update#exclusive-lock-check-at-stage-level)). Put it on every stateful stage (Terraform apply, DB migrations) so two runs cannot interleave; see the Apply stage in [Terraform](targets/terraform.md).

## ManualValidation in an agentless job

`ManualValidation@1` pauses inside a stage. It runs only in an agentless job (`pool: server`); in an agent job, expansion fails with "Step references task 'ManualValidation' at version '<version>' which is not valid for the given job target." ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/manual-validation-v1?view=azure-pipelines)).

| Input | Note |
|---|---|
| `notifyUsers` | Required. `''` is accepted but then nobody is told a run is waiting; list the approvers or a group (`[org]\group`), keeping `''` for test runs only ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/manual-validation-v1?view=azure-pipelines)) |
| `approvers` | Users, groups or teams who may act; left empty, anyone with Queue builds permission can |
| `allowApproversToApproveTheirOwnRuns` | Default `true` on Services; set `false` for a four-eyes check |
| `onTimeout` | `reject` (default) or `resume`; fires at the task `timeoutInMinutes` or after 30 days, whichever comes first |
| Job `timeoutInMinutes` | Must be longer than the task's, because the job default is 60 |

```yaml
jobs:
- job: WaitForApproval
  pool: server
  timeoutInMinutes: 1500
  steps:
  - task: ManualValidation@1
    timeoutInMinutes: 1440
    inputs:
      notifyUsers: 'release-lead@example.com'
      approvers: 'release-lead@example.com'
      allowApproversToApproveTheirOwnRuns: false
      instructions: 'Review the plan output in the previous job, then resume.'
      onTimeout: reject
```

Prefer an environment approval for prod: it lives outside the YAML and is audited, while anyone who can edit the pipeline can delete `ManualValidation@1`. Use the task for a pause inside a stage or when you cannot administer the environment. `retryCountOnTaskFailure` works on server tasks (`InvokeRESTAPI`, `AzureFunction`), max 10, but not on `ManualValidation` ([source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2024/sprint-240-update#retries-for-server-tasks)).

## Output variables out of deployment jobs

The full matrix is in [expressions-conditions.md](expressions-conditions.md). For deployment jobs the key adds a prefix: the job name for `runOnce`, `Deploy_<resource>` when the environment has a resource ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops)).

| Consumer | runOnce, resource-less | With resource `vm1` |
|---|---|---|
| Job, same stage | `dependencies.Web.outputs['Web.out.url']` | `dependencies.Web.outputs['Deploy_vm1.out.url']` |
| Variable in another stage | `stageDependencies.Dev.Web.outputs['Web.out.url']` | `stageDependencies.Dev.Web.outputs['Deploy_vm1.out.url']` |
| Stage condition | `dependencies.Dev.outputs['Web.Web.out.url']` | `dependencies.Dev.outputs['Web.Deploy_vm1.out.url']` |

Canary uses `<hook>_<increment>` and rolling uses `<hook>_<resource>` as the prefix. Task-defined outputs (here `AppServiceApplicationUrl` of `AzureWebAppContainer@1`) are read the same way as `isOutput=true` variables ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-web-app-container-v1?view=azure-pipelines)). A plain job producer keeps the usual `<step>.<var>`.

```yaml
stages:
- stage: Dev
  jobs:
  - deployment: Web
    environment: app-dev
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureWebAppContainer@1
            name: webapp
            inputs:
              azureSubscription: sc-app-dev
              appName: app-api-dev
              containers: myacr.azurecr.io/api:$(Build.BuildId)
- stage: Smoke
  dependsOn: Dev
  variables:
    devUrl: $[ stageDependencies.Dev.Web.outputs['Web.webapp.AppServiceApplicationUrl'] ]
  jobs:
  - job: Check
    steps:
    - checkout: none
    - task: Bash@3
      inputs:
        targetType: inline
        script: |
          set -euo pipefail
          curl -fsS "$(devUrl)/health"
```

## Promotion dev to prod

Build once and deploy the same artifact or image tag stage by stage; never rebuild per environment or per branch. Gate prod with an environment approval, the branch rule in the stage `condition`, and a Branch control check on the prod environment, which YAML cannot bypass. Keep `succeeded()` in the custom condition ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions?view=azure-devops)).

```yaml
stages:
- stage: Build
  jobs:
  - job: Build
    steps:
    - template: /templates/steps/build-web.yaml
    - task: PublishPipelineArtifact@1
      inputs:
        targetPath: $(Build.ArtifactStagingDirectory)/web
        artifact: web
- stage: Dev
  dependsOn: Build
  condition: and(succeeded(), ne(variables['Build.Reason'], 'PullRequest'))
  jobs:
  - template: /templates/deploy-web.yaml
    parameters:
      environment: app-dev
      serviceConnection: sc-app-dev
      appName: app-web-dev
- stage: Prod
  dependsOn: Dev
  condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
  jobs:
  - template: /templates/deploy-web.yaml
    parameters:
      environment: app-prod
      serviceConnection: sc-app-prod
      appName: app-web-prod
```

`/templates/deploy-web.yaml` is a job template holding the deployment job from [App Service code](targets/app-service-code.md), with `environment`, `serviceConnection` and `appName` as parameters. Pass the service connection as a template parameter, not a variable: "Service connections cannot be specified by variable" ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops)), and a literal name is resolved and authorized at compile time. A variable-group value (`azureSubscription: '$(azureSubscription)'`) does run; whether checks on that connection are then evaluated is (unverified).

Stage properties for release stages:

- `isSkippable: false`: the stage cannot be deselected in **Stages to run**; use it on compliance stages injected by `extends` templates ([source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2024/sprint-242-update#unskippable-stages)).
- `trigger: manual`: "Manually triggered stages have no dependencies and can be run at any time. The pipeline run completes when there are only manually triggered stages left to execute." ([source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2024/sprint-243-update#manually-triggered-yaml-pipeline-stages)).
- `group: EU Deployment\Italy` (backslash nests) groups stages in the **Stages** tab, which shows the last run deployed per stage; "A stage needs to have a name to show up in the *Stages* tab." That view shows the first `resources.pipelines` artifact per run, so declare CD inputs as pipeline resources, not `DownloadPipelineArtifact@2` with a hard-coded run id ([source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2026/sprint-271-update#deployment-history-for-stages), [schema](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/stages-stage?view=azure-pipelines)).
- To audit who ran or reran a manual prod stage, use `Build.StageRequestedBy`/`Build.StageRequestedById`, not `Build.RequestedFor` ([source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2025/sprint-253-update#identity-of-user-who-requested-a-stage-to-run)).

## App configuration from variables

- .NET reads environment variables as configuration, `__` separating levels: `ConnectionStrings__Default` becomes `ConnectionStrings:Default` ([source](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/configuration/?view=aspnetcore-9.0#non-prefixed-environment-variables)). Set runtime values as app settings on the target (`appSettings` on `AzureWebApp@1`, `AzureFunctionApp@2`, `AzureWebAppContainer@1`, format `-Key value -Other "a b"`) or as container env, instead of generating `appsettings.json`.
- Secret app settings are Key Vault references: `@Microsoft.KeyVault(SecretUri=https://<vault>.vault.azure.net/secrets/<name>/)`, resolved by the app's managed identity with Key Vault Secrets User ([source](https://learn.microsoft.com/en-us/azure/app-service/app-service-key-vault-references)).
- A build-time `.env` (frontend `NEXT_PUBLIC_*`, `VITE_*`) is written by a `Bash@3` step from an explicit key list; secrets reach it only through that step's `env:`.
- A script that reads variables from the environment gets upper-cased names with `.` turned into `_` ([execution-model.md](execution-model.md#variable-names-and-environment-variables)); it restores the original casing from its own key list.

## Targets

One working pattern per Azure target, one file each; read only the target in use.

| Target | File |
|---|---|
| App Service code and slots | [targets/app-service-code.md](targets/app-service-code.md) |
| ACR build and push | [targets/acr.md](targets/acr.md) |
| App Service containers | [targets/app-service-containers.md](targets/app-service-containers.md) |
| Azure Functions | [targets/functions.md](targets/functions.md) |
| Bicep | [targets/bicep.md](targets/bicep.md) |
| Terraform | [targets/terraform.md](targets/terraform.md) |
| Azure VM over SSH | [targets/vm-ssh.md](targets/vm-ssh.md) |
| Static Web Apps | [targets/static-web-apps.md](targets/static-web-apps.md) |

## Post-deploy health check

Put it in `postRouteTraffic` or right after the deploy step. Check that the new version answers, not only that something answers: an old container can keep returning 200 while the new one fails to start, so polling for any HTTP 200 is not enough. `curl --retry-all-errors` (curl 7.71+) also retries on connection refused and HTTP errors.

```yaml
steps:
- task: Bash@3
  displayName: Health check
  inputs:
    targetType: inline
    script: |
      set -euo pipefail
      for i in $(seq 1 30); do
        body=$(curl -fsS "$APP_URL/health" || true)
        # the app reports its build id, so a still-running old version does not pass
        if printf '%s' "$body" | grep -q "\"build\":\"$(Build.BuildId)\""; then echo "healthy after $i tries"; exit 0; fi
        sleep 10
      done
      echo "##vso[task.logissue type=error]$APP_URL did not report build $(Build.BuildId) within 5 minutes"
      exit 1
  env:
    APP_URL: $(web.AppServiceApplicationUrl)
```

For an `on: failure` rollback on App Service, swap the slots back with `AzureAppServiceManage@0` `Action: Swap Slots`.

## Container jobs that run docker

From agent 5.279.0, a Linux container job no longer gets `/var/run/docker.sock` mounted by default. A container job that runs `docker`, `Docker@2`, or a task that calls docker (such as `AzureStaticWebApp@0`) must set `mapDockerSocket: true`. The socket gives the container root on the host, so set it only where needed ([source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2026/sprint-279-update), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/container-phases?view=azure-devops)). The key works on a container resource and on the inline `container:` form ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/jobs-job-container?view=azure-pipelines)). Self-hosted agents can restore the old default temporarily with the host env var `AZP_AGENT_DEFAULT_MAP_DOCKER_SOCKET_TO_FALSE=false`. Reference the resource from the job with `container: tools`.

```yaml
resources:
  containers:
  - container: tools
    image: mcr.microsoft.com/azure-cli:latest
    mapDockerSocket: true
```
