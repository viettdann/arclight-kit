# ACR build and push

Every example below is the `steps:` of a `runOnce.deploy` hook unless it says otherwise. Service connections are Azure Resource Manager connections with workload identity federation. Deployment jobs, environments, approvals and output variables are in [deployment.md](references/deployment.md).

Use `Docker@2` with a Docker Registry service connection of type Azure Container Registry, which supports workload identity federation ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/service-endpoints?view=azure-devops)). `buildAndPush` ignores `arguments`, so `--build-arg` needs separate `build` and `push` steps ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/docker-v2?view=azure-pipelines)). This runs in a regular build job. Never write secrets into the build context, where a `COPY` bakes them into a layer; pass them with BuildKit `--secret` or supply them at runtime ([source](https://docs.docker.com/build/building/secrets/)).

```yaml
steps:
- task: Docker@2
  inputs:
    command: build
    containerRegistry: sc-acr-myacr
    repository: api
    Dockerfile: apps/api/Dockerfile
    buildContext: .
    tags: $(Build.BuildId)
    arguments: --build-arg APP_VERSION=$(Build.BuildNumber)
- task: Docker@2
  inputs:
    command: push
    containerRegistry: sc-acr-myacr
    repository: api
    tags: $(Build.BuildId)
```

`docker buildx bake` has no task: log in with `Docker@2` `command: login` and run bake from `Bash@3`. Buildx is preinstalled on hosted Ubuntu images ([source](https://github.com/actions/runner-images/tree/main/images/ubuntu)).

```yaml
steps:
- task: Docker@2
  inputs:
    command: login
    containerRegistry: sc-acr-myacr
- task: Bash@3
  inputs:
    targetType: inline
    script: |
      set -euo pipefail
      docker buildx bake -f docker-bake.hcl all \
        --set "api.tags=myacr.azurecr.io/api:$(Build.BuildId)" \
        --set "migrator.tags=myacr.azurecr.io/migrator:$(Build.BuildId)" \
        --push
```
