# Task versions

Snapshot: 2026-09-28. Sources: the Azure DevOps Services section of the [task index](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/?view=azure-pipelines) for majors, and `GET https://dev.azure.com/{org}/_apis/distributedtask/tasks` (the `deprecated` and `preview` flags) for status. Each row links to the task reference page of its latest major; fetch it with `&accept=text/markdown` for inputs.

## How to use this table

- Write `Name@<Latest>`. A task missing here is looked up on its reference page before use, then added as a row, because `scripts/task-versions.py check` reports unlisted tasks.
- An older major is fine to keep when it is not deprecated and the latest major would change behavior; say so in the review instead of bumping blindly.
- Task names are case-insensitive (`bash@3` runs), but write them as listed.
- Marketplace and in-house tasks (for example `TerraformTaskV4@4`, `TfxInstaller@5`, an org's own review task) are not in the index. Check what the organization has installed with `scripts/task-versions.py org --org <org>`.
- Terraform has no built-in task: the Microsoft DevLabs extension provides `TerraformInstaller`/`TerraformTaskV4`. Run the Terraform CLI from `AzureCLI@3` (WIF) or `Bash@3` instead, see [deployment.md](deployment.md).

## Refresh

```text
scripts/task-versions.py refresh              # latest majors from Learn, TSV
scripts/task-versions.py org --org <org>      # installed majors, deprecated majors, preview flag
scripts/task-versions.py check --markdown references/*.md
```

Update `Latest`, `Older majors` and `Status` from those outputs, bump the snapshot date, then rerun `check` so every example still passes.

## Table

`Renamed inputs` lists `old->new` pairs that `check` flags when found on the latest major; `(removed)` means the input no longer exists. Input aliases (for example `azureSubscription` on `AzureFunctionApp@2`) are not renames.

| Task | Latest | Older majors | Status | Replacement | Renamed inputs (latest major) | Notes |
|---|---|---|---|---|---|---|
| `Bash` | `Bash@3` | - | current | - | - | Default shell step. Inline scripts run without errexit, so start with `set -euo pipefail`. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/bash-v3?view=azure-pipelines) |
| `CmdLine` | `CmdLine@2` | 1 | current | - | - | Runs bash on Linux, cmd on Windows; same missing errexit as Bash@3. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/cmd-line-v2?view=azure-pipelines) |
| `PowerShell` | `PowerShell@2` | 1 | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/powershell-v2?view=azure-pipelines) |
| `AzureCLI` | `AzureCLI@3` | 2, 1 (deprecated), 0 | current | - | - | v3 adds `connectionType: azureDevOps` (az devops with a WIF connection) and `allowNoSubscriptions`; v2 still works. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-cli-v3?view=azure-pipelines) |
| `AzurePowerShell` | `AzurePowerShell@5` | 4, 3 (deprecated), 2 (deprecated), 1 | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-powershell-v5?view=azure-pipelines) |
| `UseNode` | `UseNode@1` | - | current | - | versionSpec->version | `version` defaults to `10.x`, always set it. Marked preview in the org task list. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/use-node-v1?view=azure-pipelines) |
| `NodeTool` | `NodeTool@0` | - | deprecated | `UseNode@1` | - | Deprecated; move to UseNode@1 and rename `versionSpec` to `version`. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/node-tool-v0?view=azure-pipelines) |
| `UseDotNet` | `UseDotNet@2` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/use-dotnet-v2?view=azure-pipelines) |
| `UsePythonVersion` | `UsePythonVersion@0` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/use-python-version-v0?view=azure-pipelines) |
| `PythonScript` | `PythonScript@0` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/python-script-v0?view=azure-pipelines) |
| `GoTool` | `GoTool@0` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/go-tool-v0?view=azure-pipelines) |
| `Go` | `Go@0` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/go-v0?view=azure-pipelines) |
| `JavaToolInstaller` | `JavaToolInstaller@1` | 0 | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/java-tool-installer-v1?view=azure-pipelines) |
| `Maven` | `Maven@4` | 3 (deprecated), 2 (deprecated), 1 | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/maven-v4?view=azure-pipelines) |
| `Gradle` | `Gradle@4` | 3, 2 (deprecated), 1 | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/gradle-v4?view=azure-pipelines) |
| `Npm` | `Npm@1` | 0 | current | - | - | `ci` and `custom` commands; custom `.npmrc` setups are easier with Bash@3 + npmAuthenticate@0. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/npm-v1?view=azure-pipelines) |
| `npmAuthenticate` | `npmAuthenticate@0` | - | current | - | - | Lower-case `n` in the task name. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/npm-authenticate-v0?view=azure-pipelines) |
| `NuGetAuthenticate` | `NuGetAuthenticate@1` | 0 (deprecated) | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/nuget-authenticate-v1?view=azure-pipelines) |
| `NuGetCommand` | `NuGetCommand@2` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/nuget-command-v2?view=azure-pipelines) |
| `DotNetCoreCLI` | `DotNetCoreCLI@2` | 1, 0 (deprecated) | current | - | - | `command: custom` for anything the task does not model. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/dotnet-core-cli-v2?view=azure-pipelines) |
| `PipAuthenticate` | `PipAuthenticate@1` | 0 | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/pip-authenticate-v1?view=azure-pipelines) |
| `TwineAuthenticate` | `TwineAuthenticate@1` | 0 | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/twine-authenticate-v1?view=azure-pipelines) |
| `Docker` | `Docker@2` | 1, 0 (deprecated) | current | - | - | `buildAndPush` does not take `--build-arg` from `arguments`; use `build` then `push` when args are needed. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/docker-v2?view=azure-pipelines) |
| `DockerInstaller` | `DockerInstaller@0` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/docker-installer-v0?view=azure-pipelines) |
| `DockerCompose` | `DockerCompose@1` | 0 (deprecated) | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/docker-compose-v1?view=azure-pipelines) |
| `HelmInstaller` | `HelmInstaller@1` | 0 (deprecated) | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/helm-installer-v1?view=azure-pipelines) |
| `HelmDeploy` | `HelmDeploy@1` | 0 | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/helm-deploy-v1?view=azure-pipelines) |
| `KubernetesManifest` | `KubernetesManifest@1` | 0 (deprecated) | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/kubernetes-manifest-v1?view=azure-pipelines) |
| `AzureWebApp` | `AzureWebApp@1` | - | current | - | - | Code deploy to App Service (zip/folder/package). Containers use AzureWebAppContainer@1. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-web-app-v1?view=azure-pipelines) |
| `AzureWebAppContainer` | `AzureWebAppContainer@1` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-web-app-container-v1?view=azure-pipelines) |
| `AzureRmWebAppDeployment` | `AzureRmWebAppDeployment@5` | 4, 3 (deprecated), 2 | current | - | - | Superset of AzureWebApp@1 (slots, IIS, Web Deploy); pick AzureWebApp@1 unless a v5-only input is needed. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-rm-web-app-deployment-v5?view=azure-pipelines) |
| `AzureAppServiceManage` | `AzureAppServiceManage@0` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-app-service-manage-v0?view=azure-pipelines) |
| `AzureAppServiceSettings` | `AzureAppServiceSettings@1` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-app-service-settings-v1?view=azure-pipelines) |
| `AzureFunctionApp` | `AzureFunctionApp@2` | 1 | current | - | configurationStrings->(removed), startUpCommand->(removed), customWebConfig->(removed) | `azureSubscription` is an alias of `connectedServiceNameARM`. v2 adds `isFlexConsumption`. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-function-app-v2?view=azure-pipelines) |
| `AzureFunctionAppContainer` | `AzureFunctionAppContainer@1` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-function-app-container-v1?view=azure-pipelines) |
| `AzureStaticWebApp` | `AzureStaticWebApp@0` | - | current | - | - | Takes a deployment token, not a service connection. Marked preview in the org task list. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-static-web-app-v0?view=azure-pipelines) |
| `AzureContainerApps` | `AzureContainerApps@1` | 0 (deprecated) | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-container-apps-v1?view=azure-pipelines) |
| `AzureResourceManagerTemplateDeployment` | `AzureResourceManagerTemplateDeployment@3` | - | current | - | - | Deploys ARM JSON and Bicep (`csmFile: main.bicep`). [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-resource-manager-template-deployment-v3?view=azure-pipelines) |
| `BicepDeploy` | `BicepDeploy@0` | - | current | - | - | First-party; adds what-if, validate and deployment stacks over `AzureResourceManagerTemplateDeployment@3`. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/bicep-deploy-v0?view=azure-pipelines) |
| `AzureKeyVault` | `AzureKeyVault@2` | 1 (deprecated) | current | - | - | Secrets become secret variables; map them into `env:` explicitly. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-key-vault-v2?view=azure-pipelines) |
| `AzureFileCopy` | `AzureFileCopy@6` | 5, 4, 3 (deprecated), 2 (deprecated), 1 (deprecated) | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-file-copy-v6?view=azure-pipelines) |
| `ManualValidation` | `ManualValidation@1` | 0 | current | - | - | Agentless only (`pool: server`). v1 adds `approvers` and `allowApproversToApproveTheirOwnRuns`. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/manual-validation-v1?view=azure-pipelines) |
| `InvokeRESTAPI` | `InvokeRESTAPI@1` | 0 | current | - | - | Agentless (`pool: server`) or agent job. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/invoke-rest-api-v1?view=azure-pipelines) |
| `Delay` | `Delay@1` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/delay-v1?view=azure-pipelines) |
| `PublishTestResults` | `PublishTestResults@2` | 1 (deprecated) | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/publish-test-results-v2?view=azure-pipelines) |
| `PublishCodeCoverageResults` | `PublishCodeCoverageResults@2` | 1 (deprecated) | current | - | codeCoverageTool->(removed), reportDirectory->(removed), additionalCodeCoverageFiles->(removed) | v2 takes any format (Cobertura, JaCoCo, .coverage) through `summaryFileLocation`; there is no `codeCoverageTool`. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/publish-code-coverage-results-v2?view=azure-pipelines) |
| `PublishPipelineArtifact` | `PublishPipelineArtifact@1` | 0 | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/publish-pipeline-artifact-v1?view=azure-pipelines) |
| `DownloadPipelineArtifact` | `DownloadPipelineArtifact@2` | 1, 0 (deprecated) | current | - | - | `artifact`, `path`, `pipeline`, `source` are aliases, not renames. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/download-pipeline-artifact-v2?view=azure-pipelines) |
| `PublishBuildArtifacts` | `PublishBuildArtifacts@1` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/publish-build-artifacts-v1?view=azure-pipelines) |
| `DownloadBuildArtifacts` | `DownloadBuildArtifacts@1` | 0 | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/download-build-artifacts-v1?view=azure-pipelines) |
| `CopyFiles` | `CopyFiles@2` | 1 | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/copy-files-v2?view=azure-pipelines) |
| `ArchiveFiles` | `ArchiveFiles@2` | 1 | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/archive-files-v2?view=azure-pipelines) |
| `ExtractFiles` | `ExtractFiles@1` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/extract-files-v1?view=azure-pipelines) |
| `DeleteFiles` | `DeleteFiles@1` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/delete-files-v1?view=azure-pipelines) |
| `Cache` | `Cache@2` | - | current | - | - | Only with a measured gain, see performance.md. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/cache-v2?view=azure-pipelines) |
| `CacheBeta` | `CacheBeta@1` | 0 (deprecated) | deprecated | `Cache@2` | - | Superseded by Cache@2. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/cache-beta-v1?view=azure-pipelines) |
| `SSH` | `SSH@0` | - | current | - | - | Pair with CopyFilesOverSSH@0 for VM deploys. [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/ssh-v0?view=azure-pipelines) |
| `CopyFilesOverSSH` | `CopyFilesOverSSH@0` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/copy-files-over-ssh-v0?view=azure-pipelines) |
| `InstallSSHKey` | `InstallSSHKey@0` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/install-ssh-key-v0?view=azure-pipelines) |
| `DownloadSecureFile` | `DownloadSecureFile@1` | - | current | - | - | [docs](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/download-secure-file-v1?view=azure-pipelines) |
