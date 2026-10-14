# Security

Secrets, identities, tokens, org/project pipeline settings and protected-resource controls for Azure Pipelines YAML, with a detect/fix checklist at the end.

- [Secret variables and masking](#secret-variables-and-masking)
- [Key Vault](#key-vault)
- [Workload identity federation](#workload-identity-federation)
- [Service connection hygiene](#service-connection-hygiene)
- [Pipeline settings](#pipeline-settings)
- [Job access token and build identities](#job-access-token-and-build-identities)
- [Checkout credentials](#checkout-credentials)
- [Fork pull requests](#fork-pull-requests)
- [Templates, checks and step restrictions](#templates-checks-and-step-restrictions)
- [Container jobs](#container-jobs)
- [Data-plane roles in IaC](#data-plane-roles-in-iac)
- [Checklist](#checklist)

## Secret variables and masking

Sources, best first: Key Vault-linked variable group or `AzureKeyVault@2`, variable group secret, pipeline UI secret; `##vso[task.setvariable ...;issecret=true]` only for derived values ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-secret-variables?view=azure-devops)). Never put a secret value in YAML.

Rules:

- Secrets are not exported to the environment. Map them per step with `env:`; a job-level `variables: X: $(secret)` doesn't pass the value ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)). Variable groups behave the same.
- Attach a variable group that holds secrets to the job that needs them, not to the stage or pipeline; every job in scope can map them, including deploy and health-check jobs that never should ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops#variable-scopes)).
- Don't pass secrets as command-line arguments; process listings and logs record them. Use `env:` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/secrets?view=azure-devops)). Also avoid `$(secret)` inside an inline script: macros are expanded before the task writes the script to `_temp/<guid>.sh`, so the value lands on disk.
- One secret per value; no JSON, YAML or multi-line blobs ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/secrets?view=azure-devops)).
- Az CLI prints secrets in JSON output; use `-o none` or `--query ... -o tsv` into a variable, never to stdout ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/secrets?view=azure-devops)).

Masking. Docs: substrings are never masked; in `{ "foo": "bar" }` as a secret, `bar` alone prints ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-secret-variables?view=azure-devops)). The rest comes from the agent source, not run-verified ([Worker.cs](https://github.com/microsoft/azure-pipelines-agent/blob/master/src/Agent.Worker/Worker.cs), [HostContext.cs](https://github.com/microsoft/azure-pipelines-agent/blob/master/src/Microsoft.VisualStudio.Services.Agent/HostContext.cs)):

| Masked | Not masked |
|---|---|
| Exact value, whitespace-trimmed, quote-trimmed | Any substring, a field inside a JSON secret |
| JSON-escaped, URI-escaped, backslash-escaped forms | Base64 of a composite, e.g. `base64("user:$PAT")` for a Basic header |
| Base64 of the whole value, for secret variables of the job | Base64 of `issecret` values set at runtime (only exact and escaped forms are added) |
| Credentials in URLs (`https://user:pass@host`, regex) | Hex, reversed, split, compressed or encrypted forms |
| Values registered with `##vso[task.setsecret]` from that point on | Anything printed before the `setsecret` line |

Register derived values before any output ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/logging-commands?view=azure-devops)):

```text
# wrong: the Basic header is not a registered secret, curl -v prints it
AUTH=$(printf ':%s' "$PAT" | base64 -w0); curl -v -H "Authorization: Basic $AUTH" "$URL"
# fix: register first, and do not trace headers
AUTH=$(printf ':%s' "$PAT" | base64 -w0); echo "##vso[task.setsecret]$AUTH"; curl -sS -H "Authorization: Basic $AUTH" "$URL"
```

Queue-time variables let anyone who can queue override values, or add new variables when **Limit variables that can be set at queue time** is off. Prefer typed runtime parameters with `values:`; pipelines can't modify parameters at runtime ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/inputs?view=azure-devops)). Mark YAML variables that must not change `readonly: true`; runtime ones with `isreadonly=true`.

Users with only **Queue build** can set `boolean`, `number` and `values:` parameters; free-text parameters and queue-time variables need **Edit queue build configuration** ([source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2024/sprint-237-update#edit-queue-build-configuration-permission)).

## Key Vault

Key Vault-linked variable group ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/link-variable-groups-to-key-vaults?view=azure-devops)):

- Only names are stored; values are fetched at run time, so rotation needs no pipeline change. Secrets added to or removed from the vault are not picked up until the group is edited.
- Secrets only; keys and certificates aren't supported.
- RBAC vaults work over the public endpoint only; behind a private endpoint use the access-policy model. The service connection needs **Key Vault Secrets User** (RBAC) or Get/List (access policy).
- The group is a protected resource: grant pipeline permissions per pipeline, not "open access".

`AzureKeyVault@2` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-key-vault-v2?view=azure-pipelines)): `SecretsFilter` defaults to `*`; list names instead. `RunAsPreJob: true` exposes the secrets to every step of the job, including steps before it.

```yaml
steps:
  - task: AzureKeyVault@2
    inputs:
      azureSubscription: sc-app-prod
      KeyVaultName: kv-app-prod
      SecretsFilter: 'DbPassword'
      RunAsPreJob: false
  - task: Bash@3
    inputs:
      targetType: inline
      script: |
        set -euo pipefail
        ./migrate.sh
    env:
      DB_PASSWORD: $(DbPassword)
```

## Workload identity federation

- Use WIF for every Azure Resource Manager connection; secrets and certificates are legacy ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/connect-to-azure?view=azure-devops)).
- Convert in place: **Project settings** > **Service connections** > connection > **Convert**. Works only for connections Azure DevOps created and that only one project uses. Revert is possible for 7 days ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/connect-to-azure?view=azure-devops)). Manually created app registrations need a federated credential added by hand ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/configure-workload-identity?view=azure-devops)).
- Issuer change: the Azure DevOps issuer `https://vstoken.dev.azure.com` retires on 2027-07-01 for public-cloud single-tenant apps and managed identities. New connections use the Entra issuer; flagged connections show **Update** ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/connect-to-azure?view=azure-devops)).
- Third-party and Marketplace tasks may not support WIF; wrap the tool in `AzureCLI@3` instead ([source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2024/sprint-240-update)).

`AzureCLI@3` with `addSpnToEnvironment: true` exposes `servicePrincipalId`, `tenantId` and `idToken` (WIF) or `servicePrincipalKey` (secret); the docs describe only the secret variant ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-cli-v3?view=azure-pipelines), [azureclitask.ts](https://github.com/microsoft/azure-pipelines-tasks/blob/master/Tasks/AzureCLIV3/azureclitask.ts)). It also sets `AZURESUBSCRIPTION_CLIENT_ID`, `AZURESUBSCRIPTION_TENANT_ID` and `AZURESUBSCRIPTION_SERVICE_CONNECTION_ID`. The ID token lives about 10 minutes (inferred from the task's refresh logic); longer jobs request a fresh one from `System.OidcRequestUri` ([source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2024/sprint-240-update)).

```yaml
steps:
  - task: AzureCLI@3
    displayName: Terraform apply
    inputs:
      connectionType: azureRM
      azureSubscription: sc-infra-prod
      scriptType: bash
      scriptLocation: inlineScript
      addSpnToEnvironment: true
      inlineScript: |
        set -euo pipefail
        # No Terraform task is built in; the CLI reuses the connection's federated token.
        export ARM_USE_OIDC=true ARM_CLIENT_ID="$servicePrincipalId" ARM_TENANT_ID="$tenantId" ARM_OIDC_TOKEN="$idToken"
        export ARM_SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
        terraform init -input=false
        terraform plan -input=false -out=tfplan
        terraform apply -input=false tfplan
```

Fresh token inside a long script ([source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2024/sprint-240-update)):

```text
curl -sS -X POST -H "Content-Length: 0" -H "Authorization: Bearer $SYSTEM_ACCESSTOKEN" "${SYSTEM_OIDCREQUESTURI}?api-version=7.1&serviceConnectionId=${AZURESUBSCRIPTION_SERVICE_CONNECTION_ID}" | jq -r .oidcToken
```

## Service connection hygiene

- Don't tick **Grant access permission to all pipelines**; authorize each pipeline under the connection's **Security** > **Pipeline permissions** ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/service-endpoints?view=azure-devops)).
- Scope Azure connections to a resource group, not the subscription; no subscription-wide Contributor ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/misc?view=azure-devops)).
- Review **Usage history**; **Disable** unused connections. Azure Pipelines may auto-disable connections unused for 100 days; pipelines that reference one then fail until it is re-enabled ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/service-endpoints?view=azure-devops)).
- Put approvals, branch control and required-template checks on production connections (see [checks](#templates-checks-and-step-restrictions)).
- GitHub connections: prefer the Azure Pipelines GitHub App limited to selected repos over OAuth or PAT ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/secure-access-to-repos?view=azure-devops)).

## Pipeline settings

**Organization settings** or **Project settings** > **Pipelines** > **Settings**. An org-level "on" can't be turned off per project. Current values: `GET https://dev.azure.com/{org}/{project}/_apis/build/generalsettings?api-version=7.1`; the field-to-label mapping is inferred from the names.

| Setting | API field | Target | Effect |
|---|---|---|---|
| Limit job authorization scope to current project for non-release pipelines | `enforceJobAuthScope` | on | YAML and classic build tokens become project-scoped ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/access-tokens?view=azure-devops)) |
| ... for release pipelines | `enforceJobAuthScopeForReleases` | on | Same for classic releases |
| Protect access to repositories in YAML pipelines | `enforceReferencedRepoScopedToken` | on | Token covers only referenced Azure Repos repos; GitHub not affected ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/secure-access-to-repos?view=azure-devops)) |
| Limit variables that can be set at queue time | `enforceSettableVar` | on | Only variables marked settable can be set when queueing, via UI or REST ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/inputs?view=azure-devops)) |
| Disable creation of classic build pipelines / release pipelines | `disableClassicBuildPipelineCreation` / `disableClassicReleasePipelineCreation` | on | Blocks new classic pipelines, task groups, deployment groups ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/approach?view=azure-devops)) |
| Enable shell tasks arguments validation | `enableShellTasksArgsSanitizing` | on after an audit | Rejects injectable `arguments` in Bash, PowerShell, AzureCLI, SSH and similar tasks ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/inputs?view=azure-devops)) |
| Disable implied YAML CI trigger | `disableImpliedYAMLCiTrigger` | on | No CI run for YAML without `trigger:` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops)) |
| Limit building PRs from forked GitHub repos | `forkProtectionEnabled`, `buildsEnabledForForks` | on, off | Fork PRs not built |

## Job access token and build identities

- Project scope: the identity is `<Project> Build Service (<org>)`. Collection scope: `Project Collection Build Service (<org>)`, which can reach every project ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/access-tokens?view=azure-devops)). Grant or deny on the one that matches the scope; changing the other has no effect.
- The project identity appears in permission pickers only after the pipeline has run once.
- Cross-project repo access with project scope: in the other project, add `<Project> Build Service` to a group with **View project-level information**, then grant **Read** on the repo (and on repos it uses as submodules). With **Protect access** on, also reference the repo from the job ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/access-tokens?view=azure-devops)). Alternative: define the pipeline in the target repo's project; the YAML can stay in another project's repo.
- The token is job-scoped and generated per job. In YAML it isn't in scripts unless mapped: `env: SYSTEM_ACCESSTOKEN: $(System.AccessToken)` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops)). Custom tasks that read it from the environment need the same mapping.
- `System.AccessToken` is Entra-issued: treat it as opaque, never decode it or depend on its claims ([source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2026/sprint-278-update#pipeline-builds-are-moving-to-microsoft-entra-issued-access-tokens)).
- Global PATs are retired; scripts calling Azure DevOps use an org-scoped PAT, `System.AccessToken` or an Azure DevOps service connection ([source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2026/sprint-270-update#retirement-of-global-personal-access-tokens-in-azure-devops)).
- Azure DevOps REST from an agentless job: `InvokeRESTAPI@1` with `connectionType: connectedServiceNameAzureDevOps` and `serviceConnection:`, not a generic connection holding a PAT ([source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2026/sprint-277-update#call-azure-devops-rest-apis-from-the-invoke-rest-api-task)).
- `az devops` and Entra tokens without a PAT: `AzureCLI@3` with `connectionType: azureDevOps` and `azureDevOpsServiceConnection:` pointing at an Azure DevOps service connection backed by a service principal or managed identity; `az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798` mints the token. Prefer it when a job needs another org or scoped permissions ([source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2026/sprint-275-update#access-azure-devops-with-microsoft-entra-authentication), [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/add-devops-entra-service-connection?view=azure-devops)).
- The checkout troubleshooting guide expects the build identity to hold **Read** and **Create tag** on the repo ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops)); pushing commits also needs **Contribute** (check the repo's **Security** tab for the identity that matches the scope).
- Restrict the identity per repo when a pipeline must not change code ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/access-tokens?view=azure-devops)).

## Checkout credentials

- Default checkout passes the token through an environment-backed header (`git --config-env=http.extraheader=env_var_http.extraheader fetch ...`, observed) and the post-job step cleans it; the token isn't written to `.git/config`.
- `persistCredentials: true` leaves the token in the repo's git config for every later step of the job, third-party tasks included ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps-checkout?view=azure-pipelines)). Use it only in a job whose later steps you control; otherwise pass the header per command:

```text
# wrong: persistCredentials: true on checkout, then any later step can read the token from .git/config
# fix: keep the default and authenticate one command
git -c http.extraheader="AUTHORIZATION: bearer $SYSTEM_ACCESSTOKEN" push origin "refs/tags/$tag"
```

- On self-hosted agents with `workspace: clean` off, a persisted header survives on disk after the job (the token itself should be expired by then; exact expiry unverified).

## Fork pull requests

- GitHub: by default, fork PR builds get no secret variables, no service connection credentials, no secure files and a restricted token. **Make secrets available to builds of forks** and **Make fork builds have the same permissions as regular builds** undo that; leave both off. New orgs default to not building fork PRs. **Securely build pull requests from forked repositories** forbids both overrides and requires a PR comment (`/azp run`) ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/github?view=azure-devops)).
- A fork PR runs the fork's YAML. Build fork PRs only on Microsoft-hosted agents; never on self-hosted agents that also run jobs with secrets ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/misc?view=azure-devops)).
- Azure Repos forks exist only inside the organization, and their PRs build "no different" from same-repo PRs ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops)). The GitHub fork protections don't apply, so assume secrets are available (inferred). Anyone with **Create Branch** can change pipeline YAML on a branch ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/misc?view=azure-devops)).
- Gate sensitive jobs on `System.PullRequest.IsFork` or on `Build.Reason`, and keep secrets in groups that only protected-branch runs reach:

```yaml
jobs:
  - job: publish
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'), ne(variables['Build.Reason'], 'PullRequest'))
    variables:
      - group: release-secrets
    pool:
      vmImage: ubuntu-26.04
    steps:
      - task: Bash@3
        inputs:
          targetType: inline
          script: |
            set -euo pipefail
            ./publish.sh
        env:
          PUBLISH_TOKEN: $(PUBLISH_TOKEN)
```

A job `condition` doesn't stop a PR from editing the condition in its own YAML. Real enforcement comes from the resource side: branch control or required-template checks on the variable group, connection or environment.

## Templates, checks and step restrictions

- `extends` from a template in a separate, protected repo pinned to a tag or branch (`ref: refs/tags/v1`). Make it enforceable with a **Required template** check on the protected resource (service connection, environment, pool, repo); the check fails any run that doesn't extend that template ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/templates?view=azure-devops), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops)).
- Templates can filter `stepList` parameters, for example drop `Bash@3`/`CmdLine@2`/`PowerShell@2` or inject scanning steps ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/templates?view=azure-devops)). The docs' own "main only" example compares `Build.SourceBranchName` with `refs/heads/main`, which never matches: compare `Build.SourceBranch` with `refs/heads/main`, or `Build.SourceBranchName` with `main`.
- Checks on environments and other protected resources ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals?view=azure-devops)): Approvals, **Branch control** (fully qualified `refs/heads/...`, optionally requiring branch protection), Business hours, Invoke REST API / Azure Function, Required template, Exclusive lock. Checks run when a stage that consumes the resource starts; only predefined variables are available to them.
- Deployments target an `environment` so its checks apply ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/environments?view=azure-devops)). A `ManualValidation@1` step lives in the YAML, so whoever edits the YAML can remove it; a check lives on the resource and can't be removed that way.
- `target.commands: restricted` blocks most logging commands (artifact upload, attachments) for a step; `setvariable` still works, so add `settableVariables` with an allow-list, or `none` to block all ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/target?view=azure-pipelines), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops)). Use it on steps that print untrusted text (PR titles, API responses, LLM output).

```yaml
steps:
  - task: Bash@3
    displayName: Summarize PR text
    target:
      commands: restricted
      settableVariables:
        - summaryPath
    inputs:
      targetType: inline
      script: |
        set -euo pipefail
        ./summarize.sh
```

## Container jobs

- From agent 5.279.0, Linux container jobs don't mount `/var/run/docker.sock` unless the container resource sets `mapDockerSocket: true` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/container-phases?view=azure-devops), [source](https://learn.microsoft.com/en-us/azure/devops/release-notes/2026/sprint-279-update)). Mapping the socket gives the container root on the host; set it only for Docker-in-container. `AZP_AGENT_DEFAULT_MAP_DOCKER_SOCKET_TO_FALSE=false` on a self-hosted agent restores the old default as a short-term fallback.
- `mountReadOnly` for `externals`, `tasks`, `tools` (and `work` when nothing writes there) ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/misc?view=azure-devops)).

```yaml
resources:
  containers:
    - container: build
      image: ubuntu:24.04
      # The job runs docker build against the host daemon.
      mapDockerSocket: true
      mountReadOnly:
        externals: true
        tasks: true
        tools: true
```

## Data-plane roles in IaC

A pipeline that deploys Bicep or Terraform also deploys the app identities' role assignments. Find them with `Microsoft.Authorization/roleAssignments` (Bicep) or `azurerm_role_assignment` (Terraform), and check each principal, role and scope against what the app code does. `Owner`, `Contributor` and `Reader` are management-plane roles: they grant no access to blobs, queues, secrets or messages, and the app fails at runtime with 403 even though the deploy succeeded ([source](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles)).

| The app | Role | Common mistake |
|---|---|---|
| Reads blobs | Storage Blob Data Reader | Reader |
| Reads and writes blobs | Storage Blob Data Contributor | Contributor |
| Issues user-delegation SAS | Storage Blob Delegator plus a Blob Data role | The Data role alone |
| Uses queues | Storage Queue Data Contributor | A Blob role |
| Functions host storage (identity-based `AzureWebJobsStorage`) | Storage Blob Data Owner; plus Storage Queue Data Contributor for blob triggers, Queue and Table Data Contributor for Durable | Storage Blob Data Contributor |
| Reads Key Vault secrets | Key Vault Secrets User | Key Vault Reader (metadata only) |
| Sends or receives Service Bus messages | Azure Service Bus Data Sender / Data Receiver | Contributor |
| Pulls from ACR | AcrPull | Contributor or the admin user |
| Grants roles itself (the deploy identity) | Role Based Access Control Administrator, conditioned to the roles it assigns | Owner or User Access Administrator |

Scope the assignment to the resource, not the resource group or subscription. A developer running the app locally needs the same data roles on their own identity.

## Checklist

| Detect | Severity | Fix |
|---|---|---|
| Secret value, PAT or connection string literal in YAML | Critical | Move to a Key Vault-linked group; rotate the value |
| Secret passed as a CLI argument or `$(secret)` inside an inline script | High | Map with `env:` and read the env var |
| Secret variable expected in the environment without `env:` mapping | Medium (silent empty value) | Add `env: NAME: $(secret)` on the step |
| Derived secret (base64 header, JSON with a token) printed or traced | High | `##vso[task.setsecret]` before use; no `set -x`/`curl -v` |
| JSON/YAML blob stored as one secret | Medium | One secret per value |
| `AzureKeyVault@2` with `SecretsFilter: '*'` | Medium | List the needed names |
| ARM connection using a secret or certificate | High | Convert to WIF |
| Script parses `servicePrincipalKey` on a WIF connection | Medium | Use `idToken` with `addSpnToEnvironment: true` |
| Connection, group, secure file or pool with "Grant access to all pipelines" / open access | High | Pipeline permissions per pipeline |
| Subscription-scoped Contributor connection | High | Scope to a resource group |
| Connection with no recent usage | Low | Disable, then delete |
| Job auth scope not limited, or Protect access to repos off | High | Turn on at org level |
| Classic pipeline creation allowed | Medium | Turn on both "Disable creation of classic" toggles |
| Shell task argument validation off | Low | Test pipelines that pass `arguments`, then turn it on |
| Queue-time variable feeding a script | Medium | Typed runtime parameter with `values:` |
| Script calling Azure DevOps with a PAT secret, or decoding `System.AccessToken` | Medium | `System.AccessToken` as an opaque bearer, or an Azure DevOps service connection |
| `persistCredentials: true` with later third-party steps | High | Per-command `-c http.extraheader=...` |
| Cross-project repo fetch failing with TF401019 | - | Grant `<Project> Build Service` View project info + repo Read; reference the repo in the job |
| GitHub fork builds with secrets or "same permissions" on | Critical | Turn both off; require a comment |
| Self-hosted agent building fork PRs | High | Microsoft-hosted pool |
| Production deployment not through an `environment` with checks | High | `deployment` job on an environment with approvals and branch control |
| Protected resource without a Required template check where templates are the control | Medium | Add the check |
| Step printing untrusted text without `target.commands: restricted` | Medium | Add `commands: restricted` and `settableVariables` |
| Linux container job running `docker` without `mapDockerSocket: true` | High (fails from 5.279.0) | Add it, or build outside the container |
| `mapDockerSocket: true` on a job that doesn't need Docker | Medium | Remove |
| App identity given Contributor or Reader for data access in deployed IaC | High (403 at runtime) | The data-plane role, scoped to the resource |
