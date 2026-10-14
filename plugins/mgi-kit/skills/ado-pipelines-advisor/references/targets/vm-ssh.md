# Azure VM over SSH

Every example below is the `steps:` of a `runOnce.deploy` hook unless it says otherwise. Service connections are Azure Resource Manager connections with workload identity federation. Deployment jobs, environments, approvals and output variables are in [deployment.md](../deployment.md).

Use an SSH service connection (host, port, user, private key) with `CopyFilesOverSSH@0` and `SSH@0` in a deployment job on a resource-less environment ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/service-endpoints?view=azure-devops), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/copy-files-over-ssh-v0?view=azure-pipelines), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/ssh-v0?view=azure-pipelines)). Make the remote script idempotent: one release directory per build, an atomic symlink switch, restart, health check, prune. `SSH@0` has `failOnStdErr: true` by default, so any stderr line fails the step; turn it off and rely on `set -euo pipefail`. Learn lists only RSA and DSA keys; whether ed25519 works is unverified.

```yaml
steps:
- task: CopyFilesOverSSH@0
  inputs:
    sshEndpoint: ssh-app-vm-prod
    sourceFolder: $(Pipeline.Workspace)/app
    contents: '**'
    targetFolder: /opt/app/releases/$(Build.BuildId)
    readyTimeout: '20000'
- task: SSH@0
  inputs:
    sshEndpoint: ssh-app-vm-prod
    runOptions: inline
    readyTimeout: '20000'
    failOnStdErr: false
    inline: |
      set -euo pipefail
      ln -sfn /opt/app/releases/$(Build.BuildId) /opt/app/current
      sudo systemctl restart app.service
      curl -fsS --retry 20 --retry-delay 3 --retry-all-errors http://127.0.0.1:8080/health
      # keep the last 5 releases so a rollback is a symlink switch
      ls -1dt /opt/app/releases/* | tail -n +6 | xargs -r rm -rf
```

A VM environment resource (an agent on the VM) is the alternative when you need `rolling` or per-VM history; steps then run on the VM without SSH ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops)).
