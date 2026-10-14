Performance rules for Azure Pipelines YAML on Microsoft-hosted Linux agents: measure first, then cut checkout, install, job and artifact cost.

## Contents

- [1. Measure a pipeline](#1-measure-a-pipeline)
- [2. Cache@2: measure before adding](#2-cache2-measure-before-adding)
- [3. Checkout](#3-checkout)
- [4. Skip work: path filters and Detect gating](#4-skip-work-path-filters-and-detect-gating)
- [5. Jobs: matrix, parallel slicing, fan-out, job cost](#5-jobs-matrix-parallel-slicing-fan-out-job-cost)
- [6. Artifacts](#6-artifacts)
- [7. Docker layer caching on hosted agents](#7-docker-layer-caching-on-hosted-agents)
- [8. Timeouts and workspace](#8-timeouts-and-workspace)
- [9. Optimize-mode checklist](#9-optimize-mode-checklist)

## 1. Measure a pipeline

Back every optimization claim with timeline numbers from the last N completed runs. The timeline has one record per stage, phase, job and task with `startTime`/`finishTime`, `result`, `parentId` (a task's parent is its job) and `log.id` ([source](https://learn.microsoft.com/en-us/rest/api/azure/devops/build/timeline/get?view=azure-devops-rest-7.1)). The run list comes from `GET _apis/build/builds?definitions={id}` ([source](https://learn.microsoft.com/en-us/rest/api/azure/devops/build/builds/list?view=azure-devops-rest-7.1)). Read-only, needs a PAT with Build (Read).

Use `scripts/step-durations.py`. It prints n/min/median/max seconds per job and step, slowest median first; `--raw` gives one JSON line per record with its `log` id; checkout names such as `Checkout repo@refs/pull/N/merge to s` are folded into one row.

```text
scripts/step-durations.py --org ORG --project P --pipeline-id ID --top 10 --reason pullRequest
scripts/step-durations.py --org ORG --project P --builds <before ids>
scripts/step-durations.py --org ORG --project P --builds <after ids>
```

Rules:

- Use at least 10 runs per variant and compare medians; single runs vary widely (observed: one cache restore ranged 4–40 s).
- Count every step the change adds, including `Post-job: Cache ...` (the save) and `Initialize job` of any added job.
- Queue wait is not in task records: compare the build's `queueTime` with the first job's `startTime` from `GET _apis/build/builds/{id}`.
- To tell a cache hit from a miss, read the Cache step log (`GET _apis/build/builds/{id}/logs/{logId}`, [source](https://learn.microsoft.com/en-us/rest/api/azure/devops/build/builds/get-build-log?view=azure-devops-rest-7.1)): it prints `There is a cache miss.` or `There is a cache hit: <key>` followed by `Used scope: <pipeline>;<project>;<ref>;<repo>` and `Missed on the following scopes: ...`, which shows which branch scope served the hit; the restore also prints `Expected size to be downloaded`. The post-job step prints `Uploaded N out of M bytes` on a save and `Cache with fingerprint ... already exists.` after a hit.
- A checkout log shows the exact `git fetch` flags (`--depth=1`, `--tags`/`--no-tags`) and `Receiving objects: ... MiB`: use it to confirm what the checkout really did.

## 2. Cache@2: measure before adding

Add `Cache@2` only with a before/after measurement that shows a gain. Docs: "Caching is most effective when the time required to restore and save the cache is less than the time it takes to regenerate the files ... could even negatively impact build time" ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/caching?view=azure-devops)).

How to measure:

1. Baseline: N runs without the cache. Record the install step (`npm ci`, `pip install`, `playwright install`) median.
2. With the cache: N runs, split into hits and misses using the Cache step log. Cost of a hit = restore + (install step if it still runs) + post-job step. Cost of a miss = restore + install + post-job save.
3. Expected cost = hit rate × hit cost + (1 − hit rate) × miss cost. Keep the cache only if that beats the baseline. Hit rate depends on scope (below), so measure it on the real trigger mix, not on reruns of one branch.

Verdict for `node_modules` (observed): a cache loses to plain `npm ci` on hosted agents; a hit costs about what `npm ci` costs and a miss doubles it.

Scope rules decide the hit rate ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/caching?view=azure-devops#cache-isolation-and-security)):

| Run | Reads | Writes |
|---|---|---|
| CI, manual, scheduled | source branch, `main`, `master` | source branch |
| Pull request | source branch, target branch, `refs/pull/N/merge`, `main`, `master` | `refs/pull/N/merge` only |
| Fork PR | target branch, `refs/pull/N/merge`, `main`, `master` | `refs/pull/N/merge` only |

- A PR-only pipeline (build validation, `trigger: none`) writes only to each PR's merge scope, so every new PR's first run misses unless a CI/manual run on the target branch (or `main`/`master`) seeded the cache.
- Caches are per pipeline; one pipeline cannot read another's.
- Caches are immutable per key and scope and expire after 7 days without use; there is no size limit and no way to clear one except changing the key ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/caching?view=azure-devops#q-can-i-clear-a-cache)).
- The save runs as `Post-job: Cache` only when every step succeeded ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/caching?view=azure-devops#cache-task-how-it-works)).

Key design ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/cache-v2?view=azure-pipelines)):

- Segments separated by `|`: strings, file paths (content is hashed), or comma-separated globs. Quote strings that contain a dot, or they are treated as file paths: `"node24.x"`.
- Put the lockfile in the key; do not add project, pipeline or branch, the scope already covers them.
- Include anything that changes the cached content's validity: OS, and for `node_modules` with native addons the Node major.
- `restoreKeys`: newline-separated prefixes tried when the exact key misses; the newest match wins, and `cacheHitVar` becomes `inexact`. Useful for package-manager caches (a partial cache still saves downloads); useless for `node_modules` + `npm ci`, because `npm ci` deletes `node_modules` first.
- `cacheHitVar`: set to `true`, `inexact` or `false` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/caching?view=azure-devops#use-restore-condition)).

Preferred npm shape, per docs (cache npm's download cache, always run `npm ci`); "avoid caching `node_modules` when using `npm ci`" ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/caching?view=azure-devops#examples)):

```yaml
variables:
  npm_config_cache: $(Pipeline.Workspace)/.npm

steps:
- task: UseNode@1
  inputs:
    version: '24.x'

# Keep only while a measurement shows a lower median than npm ci alone.
- task: Cache@2
  displayName: Cache npm download cache
  inputs:
    key: 'npm | "$(Agent.OS)" | package-lock.json'
    restoreKeys: |
      npm | "$(Agent.OS)"
    path: $(npm_config_cache)

- task: Bash@3
  displayName: npm ci
  inputs:
    targetType: inline
    script: |
      set -euo pipefail
      npm ci --prefer-offline --no-audit --fund=false
```

Trap: `node_modules` cached without a measurement and without the Node major in the key, so a Node upgrade restores modules built for the old ABI.

```text
# Before
key: 'npm | "$(Agent.OS)" | $(FE_DIR)/package-lock.json'
path: $(FE_DIR)/node_modules
# After (only if a measurement justifies node_modules at all; otherwise delete the cache and keep npm ci)
key: 'node_modules | "$(Agent.OS)" | "node24" | $(FE_DIR)/package-lock.json'
path: $(FE_DIR)/node_modules
cacheHitVar: NODE_CACHE_HIT     # install step: condition: ne(variables.NODE_CACHE_HIT, 'true')
```

## 3. Checkout

Checkout is often the largest fixed cost (observed on a large monorepo: full fetch ~270 MiB and 18–34 s per job, `--depth=1` 67 MiB and 5 s).

| Setting | Effect | Source |
|---|---|---|
| `fetchDepth: 1` | Shallow fetch of one commit. `0` means full history and overrides the pipeline setting. | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps-checkout?view=azure-pipelines#shallow-fetch) |
| `fetchFilter: tree:0` / `blob:none` | Partial clone: treeless or blobless. Default is no filter. Combine with `fetchDepth: 0` when history is needed (merge-base, `git log`, version derivation) but files of old commits are not. | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps-checkout?view=azure-pipelines#properties) |
| `fetchTags: false` | Adds `--no-tags`. | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops#sync-tags) |
| `sparseCheckoutDirectories: a b` | Cone-mode sparse checkout, space-separated. Wins over `sparseCheckoutPatterns` when both are set. Agent 3.253.0/4.253.0+, Git 2.25+. Only limits the working tree; the fetch still downloads the objects unless combined with `fetchFilter`. | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps-checkout?view=azure-pipelines#properties) |
| `sparseCheckoutPatterns: /* !/img` | Non-cone patterns, space-separated. | same |
| `checkout: none` | No fetch at all, and the agent skips its clean commands. Use in jobs that only consume artifacts, call APIs or deploy. | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops#dont-sync-sources) |
| `clean: true` | `git clean -ffdx` + `git reset --hard HEAD` before fetch. No effect on hosted agents, each job gets a new VM. | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops#clean-build) |
| `lfs: true` / `submodules:` | Off by default; turn on only when the job reads those files. | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/steps-checkout?view=azure-pipelines#properties) |

Defaults are not reliable; set `fetchDepth` and `fetchTags` explicitly:

- Docs: "In some organizations, new pipelines created after the September 2022 Azure DevOps sprint 209 update have Shallow fetch enabled by default and configured with a depth of 1"; new pipelines default to not syncing tags ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops#shallow-fetch)).
- Observed: the shallow setting lives on the definition (`repository.properties.fetchDepth` from `GET _apis/build/definitions/{id}`), and recently created definitions exist both with `fetchDepth=1` and with none (full history).
- Observed: with `fetchTags` unset, checkouts passed `--tags`, new pipelines included, contrary to the docs' "new pipelines default to false". `fetchTags: false` produces `--no-tags`.
- YAML beats the pipeline setting in both cases.

```yaml
steps:
- checkout: self
  fetchDepth: 1
  fetchTags: false
```

Large monorepo, one app, history not needed (not run-verified):

```yaml
steps:
- checkout: self
  fetchDepth: 1
  fetchTags: false
  fetchFilter: blob:none
  sparseCheckoutDirectories: apps/web packages/shared
```

Branch race: a very small depth can fail if the branch moves between queue and fetch ("increase the shallow fetch depth") ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops#shallow-fetch)). PR merge refs and CI runs fetch by commit SHA, so this matters mostly for manual runs on busy branches.

## 4. Skip work: path filters and Detect gating

Cheapest job is one that never starts.

- CI: `trigger.paths.include/exclude` works for Azure Repos Git ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops#paths)).
- PR on Azure Repos Git: the YAML `pr:` block (including its `paths`) is ignored. PR builds come from the branch policy's build validation, and its path filter is the one that counts ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/repos/azure-repos-git?view=azure-devops#pr-triggers), [source](https://learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies?view=azure-devops#path-filters)).
- Inside a run: a Detect job writes output variables, and downstream jobs gate on them with `condition: eq(dependencies.Detect.outputs['detect.BE'], 'true')` ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops#set-a-multi-job-output-variable)).

Fixes, largest first:

- The YAML has `pr.paths`, but the build validation policy has no path filter (`filenamePatterns: null` in `GET _apis/policy/configurations`), so every PR runs and pays at least Detect's checkout. Fix: set the policy path filter (e.g. `/apps/api/*`); drop the `pr:` block.
- Detect needs a merge base, not files: `fetchFilter: tree:0` with `fetchDepth: 0` fetches commits only, and `git diff` fetches the trees it touches on demand (unmeasured), or `fetchDepth: 2` as below.
- Gated jobs that inherit a full-clone definition default: `fetchDepth: 1`.

A PR build checks out `refs/pull/N/merge`, whose first parent is the target branch tip, so `git diff --name-only HEAD^1 HEAD` lists the PR's changes with `fetchDepth: 2`. This relies on the merge commit layout (unverified); fall back to linting everything when `HEAD^2` is missing.

```yaml
jobs:
- job: Detect
  timeoutInMinutes: 5
  steps:
  - checkout: self
    # Two levels reach both parents of the PR merge commit; that is all the diff needs.
    fetchDepth: 2
    fetchTags: false
  - task: Bash@3
    name: detect
    inputs:
      targetType: inline
      script: |
        set -euo pipefail
        if ! git rev-parse --verify --quiet HEAD^2 >/dev/null; then
          echo "##vso[task.setvariable variable=BE;isOutput=true]true"
          exit 0
        fi
        be=false
        if git -c core.quotePath=false diff --name-only HEAD^1 HEAD | grep -q '^apps/api/'; then be=true; fi
        echo "##vso[task.setvariable variable=BE;isOutput=true]$be"

- job: LintBackend
  dependsOn: Detect
  condition: eq(dependencies.Detect.outputs['detect.BE'], 'true')
  steps:
  - checkout: self
    fetchDepth: 1
    fetchTags: false
  - task: Bash@3
    inputs:
      targetType: inline
      script: |
        set -euo pipefail
        npm ci
        npm run lint
```

The gate costs one extra job (agent + checkout). With a policy path filter in place, keep Detect only when it chooses between several jobs.

## 5. Jobs: matrix, parallel slicing, fan-out, job cost

Each job gets a new VM and pays its own startup, checkout, tool install and dependency install (observed: `Initialize job` 1–6 s, checkout 1–34 s by repo and depth, `npm ci` 5–17 s). Splitting a 60 s job into three parallel jobs that each repeat `npm ci` rarely helps.

Parallel limits: each concurrently running job uses one parallel job. The free tier for private projects is one job, up to 60 minutes per run and 1,800 minutes per month; the paid tier allows 360 minutes per job; new organizations are capped at 25 Microsoft-hosted parallel jobs ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/licensing/concurrent-jobs?view=azure-devops)). With one parallel job, fan-out only adds queue time. Check Organization settings > Parallel jobs before recommending more jobs.

| Construct | Use | Rule | Source |
|---|---|---|---|
| `strategy.matrix` + `maxParallel` | Same job, different variable sets | Leg names: letters, digits, `_`, start with a letter, ≤100 chars. `maxParallel` caps concurrency (matrix only). A runtime expression can supply the matrix as JSON: `matrix: $[ dependencies.Gen.outputs['m.legs'] ]`. | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/phases?view=azure-devops#multi-job-configuration) |
| `strategy.parallel: N` | Same job N times, work split by the script | Sets `System.JobPositionInPhase` (1..N) and `System.TotalJobsInPhase`. Mutually exclusive with `matrix`. | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/phases?view=azure-devops#slicing) |
| `dependsOn` list | Fan-out from one job, fan-in to one | Jobs without `dependsOn` run in parallel; a job with `dependsOn: [A, B]` waits for both. | [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/phases?view=azure-devops#dependencies) |

```yaml
jobs:
- job: Build
  steps:
  - task: Bash@3
    inputs:
      targetType: inline
      script: |
        set -euo pipefail
        echo build

- job: Test
  dependsOn: Build
  strategy:
    parallel: 4
  steps:
  - task: Bash@3
    inputs:
      targetType: inline
      script: |
        set -euo pipefail
        # Round-robin by sorted file list keeps slices stable between runs.
        find tests -name '*.spec.ts' | sort | awk -v n="$SYSTEM_TOTALJOBSINPHASE" -v i="$SYSTEM_JOBPOSITIONINPHASE" 'NR % n == i % n' > slice.txt
        xargs -a slice.txt npx playwright test

- job: Lint
  dependsOn: Build
  strategy:
    maxParallel: 2
    matrix:
      be:
        APP_DIR: apps/be
      fe:
        APP_DIR: apps/fe
  steps:
  - task: Bash@3
    inputs:
      targetType: inline
      script: |
        set -euo pipefail
        npm --prefix "$APP_DIR" ci
        npm --prefix "$APP_DIR" run lint

- job: Report
  dependsOn:
  - Test
  - Lint
  steps:
  - checkout: none
  - task: Bash@3
    inputs:
      targetType: inline
      script: |
        set -euo pipefail
        echo done
```

Playwright has its own `--shard=i/n`; prefer it over a file list when the tool supports sharding (`npx playwright test --shard="$SYSTEM_JOBPOSITIONINPHASE/$SYSTEM_TOTALJOBSINPHASE"`) ([source](https://playwright.dev/docs/test-sharding)).

## 6. Artifacts

- Use `PublishPipelineArtifact@1`/`DownloadPipelineArtifact@2`. Pipeline artifacts are "the next generation of build artifacts", "recommended for faster performance" and deduplicated ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/artifacts/pipeline-artifacts?view=azure-devops#migrate-from-build-artifacts), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/artifacts/artifacts-overview?view=azure-devops)). `PublishBuildArtifacts@1` is only for consumers that need build artifacts (classic release pipelines).
- Use artifacts to pass files a later job needs; use a cache for files that only speed things up ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/caching?view=azure-devops#when-to-use-pipeline-artifacts-versus-pipeline-caching)).
- Publish the minimal directory (the build output, not the repo). Upload and download time grow with size, and every consumer job downloads all of it unless it names the artifact and `patterns`.
- `.artifactignore` sits in the `targetPath` root and uses `.gitignore`-like syntax. Without one, `.git` is ignored automatically; an empty file disables that ([source](https://learn.microsoft.com/en-us/azure/devops/artifacts/reference/artifactignore?view=azure-devops)).

```text
# $(Build.ArtifactStagingDirectory)/.artifactignore: ship only the bundle
**/*
!dist/**
!package.json
```

- Deployment jobs auto-inject an artifact download into the `deploy` hook (all artifacts of the run). Add `- download: none` when the job needs none, or `- download: current` with `artifact:` to take one ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/deployment-jobs?view=azure-devops#descriptions-of-lifecycle-hooks)).

## 7. Docker layer caching on hosted agents

Hosted agents are new VMs per job, so the Docker layer cache is always empty ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/hosted?view=azure-devops#capabilities-and-limitations)). Options, cheapest first; measure each like a Cache@2 change:

| Option | How | Trade-off |
|---|---|---|
| Registry cache in ACR | `docker buildx build --cache-from type=registry,ref=<acr>/<img>:buildcache --cache-to type=registry,ref=<acr>/<img>:buildcache,mode=max` after `Docker@2 login` | No pipeline-cache scope rules, shared across branches and pipelines; pull and push of cache layers cost network time ([source](https://docs.docker.com/build/cache/backends/registry/)) |
| Inline cache | `--cache-to type=inline` and `--cache-from <acr>/<img>:latest` | Only final-stage layers (`mode=min`); cheap for single-stage images ([source](https://docs.docker.com/build/cache/backends/inline/)) |
| Cache@2 + buildx local cache | `--cache-from type=local,src=$(Pipeline.Workspace)/docker_cache --cache-to type=local,dest=...,mode=max` | Subject to branch scopes and the 10 GB disk; archive/restore of large caches is often slower than rebuilding ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/caching?view=azure-devops#examples), [source](https://docs.docker.com/build/cache/backends/local/)) |
| Cache@2 + `docker save`/`load` | Docs example | Saves the whole image, not layers; rarely a win |
| Persistent agents | Managed DevOps Pools or scale set agents with a warm disk | Real layer cache; infra cost ([source](https://learn.microsoft.com/en-us/azure/devops/managed-devops-pools/overview?view=azure-devops)) |

```yaml
steps:
- task: Docker@2
  inputs:
    command: login
    containerRegistry: acr-connection

- task: Bash@3
  displayName: buildx with registry cache
  inputs:
    targetType: inline
    script: |
      # Bash instead of Docker@2 build: the task has no buildx cache-from/cache-to inputs.
      set -euo pipefail
      img=myacr.azurecr.io/api
      docker buildx create --use --driver docker-container
      docker buildx build \
        --cache-from "type=registry,ref=$img:buildcache" \
        --cache-to "type=registry,ref=$img:buildcache,mode=max" \
        --tag "$img:$(Build.BuildId)" --push .
```

## 8. Timeouts and workspace

- `timeoutInMinutes`: default 60 on the job; `0` means the maximum, which is 60 minutes for private projects on the free tier and 360 minutes on the paid tier; a value above the hosted limit has no effect ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/phases?view=azure-devops#timeouts), [source](https://learn.microsoft.com/en-us/azure/devops/pipelines/licensing/concurrent-jobs?view=azure-devops)). Set a tight timeout on every job (for example 5 for a Detect job) so a hung step fails fast instead of holding the only parallel job for an hour.
- `cancelTimeoutInMinutes`: default 5; time `always()` steps get after cancel ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/phases?view=azure-devops#timeouts)).
- `workspace: clean: outputs | resources | all` and `checkout clean` only matter on self-hosted agents; on hosted agents they are no-ops, drop them ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/phases?view=azure-devops#workspace)).
- Hosted Linux VM: 2 cores, 7 GB RAM, 14 GB SSD with at least 10 GB free ([source](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/hosted?view=azure-devops#hardware)). CPU-bound steps (`tsc`, bundling) do not speed up with more threads than that.

## 9. Optimize-mode checklist

1. Run `scripts/step-durations.py` for the last 10–30 runs. Rank steps by median × run count.
2. Checkout: `fetchDepth` and `fetchTags` explicit in YAML; `fetchDepth: 0` only with a stated reason, then try `fetchFilter: tree:0`; `checkout: none` in jobs that do not read the repo.
3. Triggers: for Azure Repos PRs, path filters go on the branch policy; YAML `pr:` does nothing.
4. Caches: each `Cache@2` has a recorded measurement (hit rate, hit cost, miss cost, baseline). Delete ones without it or with a loss.
5. Jobs: each job's fixed cost (init + checkout + install) is worth what it parallelizes; the parallel job count allows it.
6. Artifacts: pipeline artifacts, minimal `targetPath`, `.artifactignore`, `download: none` where nothing is consumed.
7. Every job has a `timeoutInMinutes`.
8. Re-measure after the change with the same N and report both medians.
