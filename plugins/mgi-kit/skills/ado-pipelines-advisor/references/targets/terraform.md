# Terraform

Contents: auth methods table, step template `/templates/steps/terraform.yaml`, Plan/Apply pipeline, lock file note.

Every example below is the `steps:` of a `runOnce.deploy` hook unless it says otherwise. Service connections are Azure Resource Manager connections with workload identity federation. Deployment jobs, environments, approvals and output variables are in [deployment.md](references/deployment.md).

No built-in task: `TerraformTaskV4@4` comes from the Microsoft DevLabs Marketplace extension. Terraform is not preinstalled on hosted Ubuntu images, so install a pinned version ([source](https://github.com/actions/runner-images/tree/main/images/ubuntu)). Run the CLI from `AzureCLI@3` so the job references the service connection, which OIDC requires ([source](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/service_principal_oidc)).

Workload identity auth, two ways:

| Method | Env vars | Notes |
|---|---|---|
| Provider requests tokens itself (preferred) | `ARM_USE_OIDC=true`, `ARM_CLIENT_ID`, `ARM_TENANT_ID`, `ARM_SUBSCRIPTION_ID`, `ARM_ADO_PIPELINE_SERVICE_CONNECTION_ID` (azurerm also reads `ARM_OIDC_AZURE_SERVICE_CONNECTION_ID`), `SYSTEM_ACCESSTOKEN`, `SYSTEM_OIDCREQUESTURI` | Fresh tokens for long applies. Without the service connection id, azurerm falls back to the GitHub OIDC flow. The azurerm backend reads the same variables ([source](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/service_principal_oidc), [source](https://developer.hashicorp.com/terraform/language/backend/azurerm)) |
| Pass the task's token | `addSpnToEnvironment: true` exposes `servicePrincipalId`, `idToken`, `tenantId`; set `ARM_OIDC_TOKEN=$idToken` | Learn says `addSpnToEnvironment` applies to secret-based connections only, but the AzureCLIV3 source also sets `idToken` for WIF. The token cannot be refreshed; the task refreshes its own `az` session every 8 minutes, "2 minutes before IdToken expiry" ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-cli-v3?view=azure-pipelines), [source](https://github.com/microsoft/azure-pipelines-tasks/blob/master/Tasks/AzureCLIV3/azureclitask.ts)) |

After a WIF login, `AzureCLI@3` exports `AZURESUBSCRIPTION_SERVICE_CONNECTION_ID`, `AZURESUBSCRIPTION_CLIENT_ID` and `AZURESUBSCRIPTION_TENANT_ID` to the script (task source, not in Learn) ([source](https://github.com/microsoft/azure-pipelines-tasks/blob/master/Tasks/AzureCLIV3/azureclitask.ts)). `System.OidcRequestUri` is a predefined variable ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops)). The backend block needs `use_oidc = true` (or `ARM_USE_OIDC`) and `use_azuread_auth = true` so state access uses Entra ID instead of a storage key ([source](https://developer.hashicorp.com/terraform/language/backend/azurerm)).

Plan and apply in separate stages: the plan file is an artifact, an environment approval sits between them, apply runs only when the plan has changes, and `lockBehavior: sequential` keeps runs from interleaving. A saved plan holds sensitive values in cleartext, readable by anyone who can read the run's artifacts. `-detailed-exitcode` returns 0 for no changes, 1 for an error, 2 for changes ([source](https://developer.hashicorp.com/terraform/cli/commands/plan)).

Step template `/templates/steps/terraform.yaml`, used by both stages so auth and version cannot drift (a multi-line `commands` string expands correctly inside the block scalar):

```yaml
parameters:
- name: stepName
  type: string
- name: commands
  type: string
steps:
- task: Bash@3
  displayName: Install Terraform
  inputs:
    targetType: inline
    script: |
      set -euo pipefail
      # pinned so plan and apply use the same version
      curl -fsSLo /tmp/tf.zip "https://releases.hashicorp.com/terraform/$(terraformVersion)/terraform_$(terraformVersion)_linux_amd64.zip"
      sudo unzip -o /tmp/tf.zip terraform -d /usr/local/bin
- task: AzureCLI@3
  name: ${{ parameters.stepName }}
  inputs:
    azureSubscription: sc-infra-prod
    scriptType: bash
    scriptLocation: inlineScript
    workingDirectory: infra
    inlineScript: |
      set -euo pipefail
      export ARM_ADO_PIPELINE_SERVICE_CONNECTION_ID="$AZURESUBSCRIPTION_SERVICE_CONNECTION_ID"
      export ARM_CLIENT_ID="$AZURESUBSCRIPTION_CLIENT_ID" ARM_TENANT_ID="$AZURESUBSCRIPTION_TENANT_ID"
      # separate assignment: export VAR=$(cmd) hides a failing cmd from set -e
      ARM_SUBSCRIPTION_ID=$(az account show --query id -o tsv); export ARM_SUBSCRIPTION_ID
      terraform init -input=false
      ${{ parameters.commands }}
  env:
    ARM_USE_OIDC: 'true'
    SYSTEM_ACCESSTOKEN: $(System.AccessToken)
    SYSTEM_OIDCREQUESTURI: $(System.OidcRequestUri)
```

Pipeline:

```yaml
variables:
  terraformVersion: '1.16.4'
stages:
- stage: Plan
  jobs:
  - job: Plan
    steps:
    - checkout: self
      fetchDepth: 1
    - template: /templates/steps/terraform.yaml
      parameters:
        stepName: plan
        commands: |
          rc=0; terraform plan -input=false -detailed-exitcode -out=tfplan || rc=$?
          [ "$rc" -eq 1 ] && exit 1
          echo "##vso[task.setvariable variable=hasChanges;isOutput=true]$([ "$rc" -eq 2 ] && echo true || echo false)"
    - task: PublishPipelineArtifact@1
      inputs:
        targetPath: infra/tfplan
        artifact: tfplan
- stage: Apply
  dependsOn: Plan
  condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'), eq(dependencies.Plan.outputs['Plan.plan.hasChanges'], 'true'))
  lockBehavior: sequential
  jobs:
  - deployment: Apply
    environment: infra-prod
    strategy:
      runOnce:
        deploy:
          steps:
          - checkout: self
            fetchDepth: 1
          - download: current
            artifact: tfplan
          - template: /templates/steps/terraform.yaml
            parameters:
              stepName: apply
              commands: terraform apply -input=false "$(Pipeline.Workspace)/tfplan/tfplan"
```

Commit `.terraform.lock.hcl` so the apply stage's `init` picks the same providers the plan used. If the state changed between plan and apply, Terraform refuses the stale plan; rerun from Plan.
