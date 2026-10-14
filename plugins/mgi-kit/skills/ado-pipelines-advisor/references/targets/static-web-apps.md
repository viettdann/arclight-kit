# Static Web Apps

Every example below is the `steps:` of a `runOnce.deploy` hook unless it says otherwise. Service connections are Azure Resource Manager connections with workload identity federation. Deployment jobs, environments, approvals and output variables are in [deployment.md](../deployment.md).

`AzureStaticWebApp@0` authenticates with the deployment token (`azure_static_web_apps_api_token`, or the same-named env var), not a service connection. With `skip_app_build: true`, `app_location` is the build output folder and `output_location` is `''` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/azure-static-web-app-v0?view=azure-pipelines)). With `skip_api_build: true`, Oryx does not install the API's dependencies, so ship `node_modules` or the API returns 500 on a green run. The task is Linux-only and runs `docker run` of the SWA client ([source](https://github.com/microsoft/azure-pipelines-tasks/blob/master/Tasks/AzureStaticWebAppV0/launch-docker.sh)), so a container job needs `mapDockerSocket: true`.

```yaml
steps:
- download: current
  artifact: site
- task: AzureStaticWebApp@0
  inputs:
    workingDirectory: $(Pipeline.Workspace)/site
    app_location: /dist
    api_location: /api
    output_location: ''
    skip_app_build: true
    skip_api_build: true
    azure_static_web_apps_api_token: $(SWA_DEPLOYMENT_TOKEN)
```
