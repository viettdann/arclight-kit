# Bicep

Every example below is the `steps:` of a `runOnce.deploy` hook unless it says otherwise. Service connections are Azure Resource Manager connections with workload identity federation. Deployment jobs, environments, approvals and output variables are in [deployment.md](../deployment.md).

Pick one task and use it for both what-if and deploy, so the preview and the change run the same engine:

| Need | Task |
|---|---|
| What-if before deploy, deployment stacks | `BicepDeploy@0`: `type: deployment`, `operation: whatIf` or `create`, `scope`, `azureResourceManagerConnection`, `subscriptionId`, `resourceGroupName`, `templateFile`, `parametersFile` (`.json` or `.bicepparam`) ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/bicep-deploy-v0?view=azure-pipelines)) |
| Deploy only, or an existing ARM task pipeline | `AzureResourceManagerTemplateDeployment@3`, below |

```yaml
steps:
- checkout: self
- task: BicepDeploy@0
  inputs:
    type: deployment
    operation: whatIf
    scope: resourceGroup
    azureResourceManagerConnection: sc-infra-prod
    subscriptionId: $(subscriptionId)
    resourceGroupName: rg-app-prod
    templateFile: infra/main.bicep
    parametersFile: infra/main.prod.bicepparam
```

Use `AzureResourceManagerTemplateDeployment@3` with a `.bicep` in `csmFile` and a `.bicepparam` in `csmParametersFile` (since 3.235.0; its `using` must point to the local Bicep file). `deploymentScope` is `Resource Group`, `Subscription` or `Management Group`; `subscriptionId` is required except at management group scope ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-resource-manager-template-deployment-v3?view=azure-pipelines), [source](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/add-template-to-azure-pipelines)). The task has no what-if (`deploymentMode: Validation` only validates); when what-if is needed, run `az deployment group what-if --resource-group <rg> --template-file main.bicep --parameters main.prod.bicepparam` in `AzureCLI@3` before the deploy step ([source](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deploy-what-if)).

```yaml
steps:
- checkout: self
- task: AzureResourceManagerTemplateDeployment@3
  inputs:
    deploymentScope: Resource Group
    azureResourceManagerConnection: sc-infra-prod
    subscriptionId: $(subscriptionId)
    action: Create Or Update Resource Group
    resourceGroupName: rg-app-prod
    location: westeurope
    templateLocation: Linked artifact
    csmFile: infra/main.bicep
    csmParametersFile: infra/main.prod.bicepparam
    deploymentMode: Incremental
    deploymentName: app-$(Build.BuildId)
    deploymentOutputs: armOutputs
```
