# Triggers

What starts a run, which YAML version and which commit it uses, and the variables it sets: CI, PR (branch policies and `pr:`), schedules, pipeline completion, repository resources, and cross-repo build validation.

- [Resolution table: which YAML, which commit](#resolution-table-which-yaml-which-commit)
- [CI triggers](#ci-triggers)
- [PR triggers](#pr-triggers)
- [Build validation branch policy](#build-validation-branch-policy)
- [Scheduled triggers](#scheduled-triggers)
- [Pipeline completion triggers](#pipeline-completion-triggers)
- [Repository resource triggers](#repository-resource-triggers)
- [Cross-repo build validation ("cross run")](#cross-repo-build-validation-cross-run)
- [Review checklist](#review-checklist)

## Resolution table: which YAML, which commit

| Run started by | YAML version used | Code checked out for `self` | `Build.Reason` | `Build.SourceBranch` |
|---|---|---|---|---|
| Push (CI) | YAML in the pushed branch ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops)) | pushed commit | `IndividualCI`, `BatchedCI` with `batch: true` | `refs/heads/<branch>` or `refs/tags/<tag>` |
| PR, same repo (Azure Repos policy or GitHub `pr:`) | YAML of the PR merge commit, so a PR can change its own pipeline ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops)) | merge commit of `refs/pull/<id>/merge` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops)) | `PullRequest` | `refs/pull/<id>/merge` |
| PR on a repo declared as a repository resource (cross run) | latest YAML on the default branch of `self` (observed) | `self` stays at its default branch; the triggering repo is at the merge commit (see [cross run](#cross-repo-build-validation-cross-run)) | `PullRequest` | the target's `refs/pull/<id>/merge` (observed) |
| Manual run | the branch picked in the Run dialog, else **Default branch for manual and scheduled builds** ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/pipeline-default-branch?view=azure-devops)) | head of that branch | `Manual` | that branch |
| Schedule | YAML in each branch; a branch is scheduled only if that branch's own YAML includes it ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/scheduled-triggers?view=azure-devops)) | head of that branch | `Schedule` | that branch |
| Pipeline completion, same repo | triggered pipeline's YAML in the triggering run's branch ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/pipeline-triggers?view=azure-devops)) | same commit as the triggering run (observed) | `ResourceTrigger` | triggering run's branch |
| Pipeline completion, different repo | triggered pipeline's **Default branch for manual and scheduled builds** ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/pipeline-triggers?view=azure-devops)) | head of that branch | `ResourceTrigger` | that branch |
| Push to a repository resource with `trigger:` | latest YAML on the default branch of `self` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/multi-repo-checkout?view=azure-devops)) | `self` at default branch; triggering repo at the pushed commit; other resources at their `ref` | `ResourceTrigger` (unverified) | triggering repo's branch |

Branch filters of pipeline completion triggers are always read from the triggered pipeline's **Default branch for manual and scheduled builds**, even when the run itself uses another branch's YAML ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/pipeline-triggers?view=azure-devops)).

## CI triggers

Rules ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops) unless noted):

- No `trigger:` means CI on every branch, unless **Disable implied YAML CI trigger** is on at org or project level (`disableImpliedYAMLCiTrigger` in `GET {project}/_apis/build/generalsettings`). Write `trigger: none` explicitly on PR-only, scheduled and completion-triggered pipelines.
- Triggers live in the root YAML only; `trigger`, `pr`, `schedules` and pipeline-resource triggers inside templates are ignored ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/pipeline-triggers?view=azure-devops)).
- No variables in branches, tags or paths: triggers are evaluated before any variable exists.
- UI trigger overrides (**Triggers** > **Override the YAML ... trigger from here**) silently replace YAML triggers; check them when a trigger "does not work".
- Includes are applied first, then excludes. `exclude` without `include` means include `*`. A pattern starting with `*` must be quoted.
- Wildcards: `*` and `?` anywhere in branch, tag and path patterns on Azure DevOps Services; `**` for paths.
- Paths are relative to the repo root and case-sensitive. An excluded folder can be re-included only with a deeper path (`exclude: tools`, `include: tools/trigger-runs-on-these`).
- Tags never trigger unless listed. Branch and tag filters are OR'ed: a tag push that matches `branches` runs even when `tags.exclude` matches it.
- `batch: true` queues one run for all pushes that arrived while a run was in progress; the in-progress run must finish every stage (approvals included) first, so split CI and CD before batching a multi-stage pipeline. Not supported on repository resource triggers.
- A new branch triggers only if it changes files matching the path filter (when one exists); with no path filter it triggers even with no changes.
- `[skip ci]`, `[ci skip]`, `skip-checks: true`, `[skip azp]`, `***NO_CI***` in any pushed commit skip CI for that push, but never skip build validation of a PR.

```yaml
trigger:
  batch: true
  branches:
    include:
      - main
      - releases/*
    exclude:
      - releases/old*
  paths:
    include:
      - src
    exclude:
      - src/**/*.md
```

Trap, tag release pipeline that also builds every branch push:

```text
# wrong: a tag push on a commit of main runs twice, and tags.exclude does not stop it
trigger:
  branches: { include: [main] }
  tags: { include: ['v*'], exclude: ['v0.*'] }
# fix: one pipeline for branches, one for tags with trigger.branches.include: [refs/tags/v*]
```

## PR triggers

- Azure Repos Git: YAML `pr:` is ignored; PR runs come only from a **Build validation** branch policy on the target branch ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/pr?view=azure-pipelines)). A `pr:` branch list there says nothing about when policy runs happen; on Azure Repos write `pr: none` or nothing, and put the real filter in the policy. `pr: none` compiles to `pr: enabled: false`.
- GitHub and Bitbucket Cloud: `pr:` is the PR trigger. No `pr:` means every target branch. Full syntax has `branches`, `paths`, `autoCancel` (default `true`: a new push cancels the running validation) and `drafts` (default `true`) ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/pr?view=azure-pipelines)). GitHub builds `refs/pull/<id>/merge`, so the PR's version of the YAML runs ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/github?view=azure-devops)).
- Draft PRs on Azure Repos never trigger build validation ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops)).
- A push to a PR's source branch can start both the policy run (on the merge commit) and a CI run (on the source branch) when the CI trigger includes that branch. Gate PR-only or CI-only work on `Build.Reason`.

```yaml
pr:
  autoCancel: true
  drafts: false
  branches:
    include:
      - main
  paths:
    exclude:
      - docs
```

## Build validation branch policy

Configured on the target branch, per pipeline ([source](https://learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies?view=azure-devops)):

| UI field | REST / `az repos policy build` | Meaning |
|---|---|---|
| Trigger: Automatic / Manual | `manualQueueOnly` | Manual means someone queues it from the PR |
| Policy requirement: Required / Optional | `isBlocking` | Optional reports status but never blocks completion |
| Build expiration: Immediately when branch is updated | `queueOnSourceUpdateOnly: false`, `validDuration: 0` | Status expires and the build requeues on every target-branch update |
| After n hours if branch has been updated | `queueOnSourceUpdateOnly: true`, `validDuration: n*60` (minutes) | Compromise for busy branches |
| Never | `queueOnSourceUpdateOnly: true`, `validDuration: 0` | Target updates do not expire the result |
| Path filter | `filenamePatterns` | Policy applies only when the PR touches matching files |

The CLI doc states `valid-duration` must be 0 when `queue-on-source-update-only` is false; the other expiration rows are inferred from existing policies (`GET {project}/_apis/policy/configurations`).

Path filter syntax ([source](https://learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies?view=azure-devops)): each path starts with `/` or a wildcard (a path starting with anything else has no effect), `;` separates entries, `!` excludes something already included, order matters (left to right), `*` matches across `/`. `!/docs/*` alone matches nothing. The FAQ says branch policies aren't case-sensitive, unlike YAML trigger paths.

Interaction with YAML:

- The policy path filter and the YAML `trigger.paths` are independent; keep them in sync by hand.
- A policy run uses the merge commit's YAML: `trigger` is irrelevant to it, but job conditions, templates and variables come from the PR.
- The policy queues the pipeline even if the YAML says `trigger: none` and `pr: none`.

## Scheduled triggers

Rules ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/scheduled-triggers?view=azure-devops)):

- Cron has 5 fields `mm HH DD MM DW` in UTC; day of week 0-6 from Sunday; ranges, lists, `*/n`. Converting a local time can shift the weekday.
- Schedules are read from the YAML **in each branch**: add `release` to the branch filter in `release`'s own YAML, not only in `main`'s. Schedules re-sync on push to the YAML, on pipeline creation, and on branch creation; a trivial push to the YAML fixes a stale schedule.
- Default `always: false`: the run is skipped when nothing changed since the last *successful* scheduled run. A partially succeeded run doesn't count, so a pipeline that only partially succeeds runs every time.
- `batch: true` skips a tick while the previous scheduled run is still in progress, but only when `always: false`; with `always: true` the schedule fires regardless.
- Any schedule defined in the UI disables all YAML schedules of that pipeline.
- Limits are on runs, not on cron entries: about 1000 scheduled runs per pipeline per week and 10 per 15 minutes. No documented maximum on the number of `cron` entries.
- A disabled pipeline doesn't refresh its schedules when its YAML changes.
- `Build.CronSchedule.DisplayName` holds the firing schedule's `displayName`; use it in conditions when one pipeline has several schedules.
- For a schedule-only pipeline also write `trigger: none` (and `pr: none` on GitHub).

```yaml
trigger: none
pr: none
schedules:
  # 08:00 Monday in UTC+7.
  - cron: '0 1 * * 1'
    displayName: Weekly scan
    branches:
      include:
        - main
    # The scan checks external data, so run without new commits too.
    always: true
```

## Pipeline completion triggers

```yaml
resources:
  pipelines:
    - pipeline: ci
      # Pipeline in a folder: folder path with a leading backslash.
      source: '\Team\app-ci'
      # project: OtherProject   # only for a source pipeline in another project
      trigger:
        branches:
          include:
            - main
        stages:
          - Build
        tags:
          - release
```

Rules ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/pipeline-triggers?view=azure-devops), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/resources?view=azure-devops)):

- Fires when the source run completes successfully and matches every filter: `branches` (include/exclude, wildcards; try `refs/heads/` prefixes if a filter doesn't match), `tags` (AND), `stages` (all listed stages completed). `trigger: true` means any successful run.
- There is no path filter. Every matching source run triggers; put path logic in the source pipeline or in a job condition.
- Not configurable in templates; the `resources.pipelines` block itself can be in a template.
- `version`, `branch`, `tags` on the resource (outside `trigger`) only choose the artifact version for manual and scheduled runs; they are ignored for completion-triggered runs. `branch` takes no wildcards.
- A pipeline with its own CI trigger and a completion trigger on a pipeline in the same repo runs twice per push. Set `trigger: none` on the downstream one.
- Cross-project completion triggers fail silently when the triggered pipeline's default branch is stored without `refs/heads/`; re-select the default branch to fix it.
- Doc inconsistency: the resources page says a different-repo trigger runs "on the default branch of the `pipeline` resource repository"; the pipeline-triggers page and the schema say the triggered pipeline's **Default branch for manual and scheduled builds**. Follow the latter ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/resources-pipelines-pipeline?view=azure-pipelines)).

Runtime variables, not usable in `${{ }}` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/resources-pipelines-pipeline?view=azure-pipelines)): `resources.pipeline.<alias>.projectName` (only when `project` is set), `.projectID`, `.pipelineName`, `.pipelineID`, `.runName`, `.runID`, `.runURI`, `.sourceBranch`, `.sourceCommit`, `.sourceProvider`, `.requestedFor`, `.requestedForID`; env form `RESOURCES_PIPELINE_<ALIAS>_RUNID`. On a completion run also `Resources.TriggeringAlias` and `Resources.TriggeringCategory = pipeline`.

Observed: the run's `triggerInfo.pipelineTriggerType` is `PipelineCompletion`, and the Runs API's `resources.pipelines.<alias>.pipeline.id` holds the source *run* id, not the definition id.

## Repository resource triggers

```yaml
resources:
  repositories:
    - repository: tools
      type: git
      name: OtherProject/tools
      # Pinned so a default-branch rename cannot move it.
      ref: refs/heads/main
      trigger:
        branches:
          include:
            - main
        paths:
          include:
            - scripts
```

Rules ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/multi-repo-checkout?view=azure-devops), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/resources-repositories-repository?view=azure-pipelines)):

- Azure Repos Git only, same organization, and `self` must be Azure Repos Git. No `batch`. No `trigger` on the resource means pushes to it never trigger.
- The YAML comes from `self`'s default branch; the triggering repo is checked out at the pushed commit; other resources at their `ref`.
- `Build.Repository.ID/Name/Provider/Uri`, `Build.SourceBranch`, `Build.SourceBranchName`, `Build.SourceVersion`, `Build.SourceVersionMessage` describe the triggering repo, not `self`.
- `ref` accepts `${{ }}` but not `$( )`; `name` accepts neither. Inline `checkout: git://P/R@$(branch)` looks for a ref literally named `$(branch)`.
- Runtime metadata: `resources.repositories.<alias>.name/ref/type/id/url/version`; in `$[ ]` write `resources.repositories['alias'].ref`.

## Cross-repo build validation ("cross run")

Shape: pipeline definition in project P, its YAML in repo R (any project), validating PRs of repo T.

Requirements:

1. Declare T as a repository resource in the root YAML. The docs make this the condition for PR triggers from another repo: "declare the repository resources ... and configure a branch policy in the repository (Azure Repos only)" ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/multi-repo-checkout?view=azure-devops)).
2. Add the Build validation policy on T's target branch, pointing at the pipeline.
3. Token scope. With **Limit job authorization scope to current project** on, the job token is `<P> Build Service (<org>)`. It must have Read on every repo the job fetches outside P, plus "View project-level information" on that project ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/access-tokens?view=azure-devops)). Keep P = T's project so fetching T and posting PR comments need no cross-project grant; if R is in another project, `checkout: self` then needs Read for `<P> Build Service` on R, and `checkout: none` avoids that.
4. **Protect access to repositories in YAML pipelines** scopes the token to repos the job references; docs disagree whether that means "a `checkout` step or a `uses` statement" ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/access-tokens?view=azure-devops)) or "repositories explicitly listed in the pipeline's `resources` section" ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/resources?view=azure-devops)). Observed: with `enforceReferencedRepoScopedToken: true`, T declared, `checkout: none` and no `uses`, the job cloned T with `System.AccessToken`; a non-triggering resource is unverified. `uses: repositories: [target]` on the job satisfies both readings. The first run may wait for a **Permit** on the repo resource.

What the run sees (observed through `_apis/pipelines/{id}/runs/{runId}` and `_apis/build/builds/{id}`):

| Item | Value |
|---|---|
| `resources.repositories.self` | R, `refName: refs/heads/main`, `version` = R's main head |
| `resources.repositories.target` | T, `refName: refs/pull/<id>/merge`, `version` = PR merge commit |
| `Build.Reason` | `PullRequest` |
| `Build.SourceBranch` | `refs/pull/<id>/merge` of T |
| `Build.SourceVersion` | T's merge commit, a commit that doesn't exist in R |
| Build record `repository` | R, not T |
| `System.PullRequest.PullRequestId`, `.SourceBranch`, `.TargetBranch`, `.TargetBranchName`, `.SourceCommitId`, `.SourceRepositoryUri`, `.PullRequestIteration` | populated from T's PR |
| `triggerInfo` | `pr.number`, `pr.isFork: False`, `pr.triggerRepository` = T's id |
| `requestedFor` | PR author; `requestedBy` = `Microsoft.VisualStudio.Services.TFS` |

`Build.Repository.*`: the multi-repo doc says it describes the triggering repo, but the build record shows R and a task input default `$(Build.Repository.Name)` reportedly resolved to R (unverified). Pass T's project and repo name explicitly.

Checkout of T:

- `checkout: target` is expected to check out the merge commit: "for the triggering repository, the commit that triggered the pipeline determines the version of the code that is checked out" ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/multi-repo-checkout?view=azure-devops)), and the run pins `target` to `refs/pull/<id>/merge` (unverified in a run). "A repository resource always checks out its default branch" holds only for non-triggering resources.
- Manual fetch of `refs/pull/<id>/merge` (observed working):

```yaml
trigger: none
resources:
  repositories:
    - repository: target
      type: git
      name: Apps/app
jobs:
  - job: review
    pool:
      vmImage: ubuntu-26.04
    uses:
      repositories:
        - target
    steps:
      - checkout: none
      - task: Bash@3
        displayName: Fetch the PR merge commit
        inputs:
          targetType: inline
          script: |
            set -euo pipefail
            # Unset macros stay literal, so test for digits rather than for empty.
            case "$PR_ID" in ''|*[!0-9]*) echo "##vso[task.logissue type=error]Not a PR build: '$PR_ID'"; exit 1 ;; esac
            auth="AUTHORIZATION: bearer $ACCESS_TOKEN"
            git init -q "$PR_DIR"
            # Depth 2 keeps both merge parents, enough for git diff HEAD^1 HEAD.
            git -C "$PR_DIR" -c http.extraheader="$auth" fetch --no-tags --depth=2 "$REPO_URL" "refs/pull/${PR_ID}/merge"
            git -C "$PR_DIR" checkout -q --detach FETCH_HEAD
        env:
          PR_ID: $(System.PullRequest.PullRequestId)
          ACCESS_TOKEN: $(System.AccessToken)
          REPO_URL: $(System.CollectionUri)Apps/_git/app
          PR_DIR: $(Build.SourcesDirectory)/pr
```

The `--depth=2` variant is unverified (observed: full `git clone --no-checkout` plus fetch). Build T's URL from the project and repo name, not from `System.PullRequest.SourceRepositoryUri`, which points at the fork for fork PRs while `refs/pull/<id>/merge` lives in T. The header goes on the command line with `-c`, so the token is never written to `.git/config`.

## Review checklist

| Detect | Fix |
|---|---|
| `pr:` block in a pipeline on Azure Repos Git | Replace with `pr: none` or remove it; move branch and path filters into the Build validation policy |
| No `trigger:` on a PR-only, scheduled or completion-triggered pipeline | `trigger: none` |
| `trigger`/`schedules`/`resources.pipelines[].trigger` inside a template | Move to the root YAML |
| `$(var)` in trigger branches, paths or `checkout: git://...@$(ref)` | Literal values, or `${{ parameters.x }}` on the repository resource `ref` |
| Policy path filter and YAML `trigger.paths` differ | Align them, or note why they differ |
| Path filter entry not starting with `/` or `*` | Prefix `/`; it is ignored otherwise |
| Schedule without `always: true` on a pipeline whose output depends on external state | Add `always: true` |
| Branch added to `schedules.branches` only on the default branch | Add it in that branch's YAML too |
| Cron written in local time | Convert to UTC and state the local time in a comment |
| Completion-triggered pipeline also has a CI trigger in the same repo | `trigger: none` downstream |
| Completion trigger expected to filter on paths | Filter in the source pipeline or a job condition |
| Cross-run pipeline without T as a repository resource | Declare it; add `uses: repositories: [alias]` to the job |
| Cross-run reads `Build.Repository.Name` or `System.TeamProject` to find T | Pass T's project and repo explicitly |
| Cross-run fetches `System.PullRequest.SourceRepositoryUri` | Fetch from T's URL |
