# App Service code and slots

Every example below is the `steps:` of a `runOnce.deploy` hook unless it says otherwise. Service connections are Azure Resource Manager connections with workload identity federation. Deployment jobs, environments, approvals and output variables are in [deployment.md](../deployment.md).

`AzureWebApp@1` deploys a zip or folder. With a slot: deploy to `staging`, check it, then swap with `AzureAppServiceManage@0` (`SwapWithProduction` defaults to `true`) ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-web-app-v1?view=azure-pipelines), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-app-service-manage-v0?view=azure-pipelines), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/targets/webapp?view=azure-devops)). The task sets the output `AppServiceApplicationUrl`; that it holds the slot URL after a slot deploy is unverified.

```yaml
steps:
- task: AzureWebApp@1
  name: web
  inputs:
    azureSubscription: sc-app-prod
    appType: webAppLinux
    appName: app-web-prod
    deployToSlotOrASE: true
    resourceGroupName: rg-app-prod
    slotName: staging
    package: $(Pipeline.Workspace)/web/app.zip
- task: Bash@3
  displayName: Health check staging slot
  inputs:
    targetType: inline
    script: |
      set -euo pipefail
      curl -fsS --retry 20 --retry-delay 10 --retry-all-errors "$(web.AppServiceApplicationUrl)/health"
- task: AzureAppServiceManage@0
  inputs:
    azureSubscription: sc-app-prod
    Action: Swap Slots
    WebAppName: app-web-prod
    ResourceGroupName: rg-app-prod
    SourceSlot: staging
```
