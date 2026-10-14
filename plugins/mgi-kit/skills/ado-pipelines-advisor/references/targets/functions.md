# Azure Functions

Every example below is the `steps:` of a `runOnce.deploy` hook unless it says otherwise. Service connections are Azure Resource Manager connections with workload identity federation. Deployment jobs, environments, approvals and output variables are in [deployment.md](../deployment.md).

## Deploy

Use `AzureFunctionApp@2`; Flex Consumption needs it (v1 cannot deploy to it) with `appType: functionAppLinux` and `isFlexConsumption: true`. Flex has no slots, and `runtimeStack`/`deploymentMethod`/`deployToSlotOrASE` only apply when `isFlexConsumption` is `false` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-function-app-v2?view=azure-pipelines), [source](https://learn.microsoft.com/en-us/azure/azure-functions/functions-how-to-azure-devops)).

The task sets the output variable `AppServiceApplicationUrl`; name the step and read it like any `isOutput=true` variable, with the deployment-job prefix from another job ([deployment.md](../deployment.md#output-variables-out-of-deployment-jobs)), instead of looking the host name up with `az` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-function-app-v2?view=azure-pipelines)).

```yaml
steps:
- task: AzureFunctionApp@2
  name: func
  inputs:
    azureSubscription: sc-app-prod
    appType: functionAppLinux
    isFlexConsumption: true
    appName: func-orders-prod
    package: $(Pipeline.Workspace)/func/func.zip
```

## Package a Python app

Build job, not a deploy hook. Install dependencies into `.python_packages/lib/site-packages` and archive the whole function app root (the folder with `host.json`), never a hand-picked file list, which drops every module added later ([source](https://learn.microsoft.com/en-us/azure/azure-functions/functions-how-to-azure-devops)). Pin Python with `UsePythonVersion@0` to the repo's `.python-version` or the app's runtime version. `ArchiveFiles@2` has no exclude input, so when the root also holds `.git`, tests or pipelines, first copy the app with `CopyFiles@2` (`Contents` with `!` patterns such as `!.git/**`) into a staging folder and archive that ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/copy-files-v2?view=azure-pipelines), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/file-matching-patterns?view=azure-devops)).

```yaml
steps:
- checkout: self
  fetchDepth: 1
  fetchTags: false
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.12'
- task: Bash@3
  inputs:
    targetType: inline
    script: |
      set -euo pipefail
      pip install --target="./.python_packages/lib/site-packages" -r ./requirements.txt
- task: ArchiveFiles@2
  inputs:
    rootFolderOrFile: $(System.DefaultWorkingDirectory)
    includeRootFolder: false
    archiveFile: $(Build.ArtifactStagingDirectory)/func.zip
- task: PublishPipelineArtifact@1
  inputs:
    targetPath: $(Build.ArtifactStagingDirectory)/func.zip
    artifact: func
```
