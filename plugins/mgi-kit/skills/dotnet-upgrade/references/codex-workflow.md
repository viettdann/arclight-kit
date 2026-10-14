# .NET upgrade

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.

Move the solution to the target framework with the build and tests green at every step, changing only what the upgrade requires. Facts about versions, support dates, and breaking changes are fetched, not recalled.

## 1. Target and baseline

- Target: the one the user named; otherwise the latest GA LTS, checked on `https://dotnet.microsoft.com/platform/support/policy/dotnet-core`. STS or preview only when asked.
- `dotnet --list-sdks`: if no SDK for the target is installed, stop and tell the user; don't install one.
- Clean build (`dotnet build --no-incremental`) and test the whole solution before any edit. Record failing tests and warnings by id and count; that is the baseline every later step is compared to. An incremental build hides warnings from projects it skips.
- Snapshot resolved packages: `dotnet list package --include-transitive --format json > packages-before.json` (SDK 10: `dotnet package list`), outside the repo or untracked. The report diffs it against the same command after the upgrade.

## 2. Inventory

Read, don't edit:

- Projects: `git ls-files '*.csproj' '*.fsproj' '*.vbproj'`. For each: `TargetFramework` or `TargetFrameworks`, `Sdk`, `LangVersion`. The TFM may be set in `Directory.Build.props` instead of the project; grep both.
- Classify each TFM:
  - `netX.0` or `netcoreapp*`: in scope.
  - `netstandard2.x`: leave as is unless asked; it exists to be shared with older consumers.
  - `net4x` (.NET Framework): out of scope. Name its project type (ASP.NET MVC 5, Web Forms, WCF service, WinForms, WPF, class library) and stop for a separate plan; Web Forms and WCF server have no in-place path.
- Multi-targeted projects (`TargetFrameworks`): an app or test project replaces the old TFM; a library consumed by projects or packages still on the old TFM adds the new one beside it. When the consumers aren't all in this repo, ask.
- Central files: `global.json` (SDK version and `rollForward`), `Directory.Build.props` and `.targets`, `Directory.Packages.props`, `NuGet.config`. Note `TreatWarningsAsErrors` and `WarningsAsErrors` wherever they are set; they turn new obsolete warnings into build errors (section 4).
- Packages: `dotnet list package --outdated`, `--vulnerable --include-transitive`, `--deprecated`. Runtime-tied packages (`Microsoft.AspNetCore.*`, `Microsoft.EntityFrameworkCore.*`, `Microsoft.Extensions.*`, `System.*` packages that ship with the runtime) move with the TFM major; third-party packages move only when the new TFM requires it.
- Azure Functions projects: in-process when they reference `Microsoft.NET.Sdk.Functions` or use `[FunctionName]`. In-process ends support on 2026-11-10 and runs only .NET 8, so it blocks any TFM change past net8.0. Migrate the model first, on the current TFM, with [functions-isolated.md](references/functions-isolated.md), then return to section 3 for the TFM. Run its workspace checks on every Functions project, isolated ones included.
- Outside the projects: Dockerfiles (`mcr.microsoft.com/dotnet/sdk`, `aspnet`, `runtime` tags), CI (`actions/setup-dotnet` `dotnet-version`, Azure DevOps `UseDotNet@2`), `.config/dotnet-tools.json` (`dotnet-ef`), and hosting config kept in the repo (Bicep, Terraform, pipeline YAML runtime stacks).
- More than about ten projects in scope: show the inventory and the step order (section 4), and wait for approval before editing.

## 3. Read the breaking changes

- For each major version crossed (net8.0 to net10.0 crosses 9 and 10), fetch "Breaking changes in .NET N" under `https://learn.microsoft.com/dotnet/core/compatibility/`, and the EF Core breaking-changes page for each EF Core major crossed.
- Then read [known-traps.md](references/known-traps.md) for each major crossed and run its grep table over the repo. It holds what the pages miss or bury: `Microsoft.OpenApi` 2.x and 3.x, EF Core changes that generate migrations, Debian images, NuGet pruning and audit, the security checks. A fetched page wins over it on any disagreement.
- Keep only the entries for areas the inventory shows in use: ASP.NET Core, EF Core, SDK and MSBuild, containers, serialization, networking, cryptography. List each with the projects or files it hits before editing.
- `BinaryFormatter` in use and net9.0 or later crossed: stop and ask. It always throws from .NET 9, and replacing it changes a stored or wire format.
- A third-party package that needs a new major: read its release notes for that major the same way.

## 4. Upgrade

Order:

- TFM set centrally, or a solution of a few projects: change it once and fix the build in one step.
- Otherwise project by project, consumers first: host projects (API, web, workers, functions) and their test projects, then down the `ProjectReference` graph to the leaves. A project on the new TFM can reference one on the old TFM, never the reverse, so upgrading a leaf first breaks every consumer still on the old TFM.

Before the first build on the new TFM, move the SDK pin: `global.json` `sdk.version` to the target's SDK, keeping `rollForward` and any other keys. A pin left on the old major fails every build with an error about the target framework, not about `global.json`. `rollForward: disable` or `latestPatch` needs the exact installed feature band; say so when it doesn't match `dotnet --list-sdks`.

Each step:

1. Change the TFM where it is actually set. Leave `LangVersion`, `Nullable`, `ImplicitUsings`, and other properties alone unless the build requires a change.
2. Bump the runtime-tied packages to the matching major, in `Directory.Packages.props` when central package management is on. Bump a third-party package only when restore or build fails without it, one package at a time.
3. Restore, and read its warnings before building:
   - `NU1510` (from SDK 10): the shared framework now provides that package. Remove the `PackageReference`; don't bump it.
   - `NU1901`–`NU1904` from the transitive audit: upgrade the package that brings the vulnerable one in, or pin the transitive version in CPM with the advisory named. Report it either way.
   - A `PackageReference` with no version is an error from SDK 10; give it one.
4. Clean build and run the tests of the projects changed in this step. Compare with the baseline.
5. Fix errors with the smallest change that matches the breaking-change entry. A behavioral change from section 3 that hits this code gets a test, or a line in the report when no test can observe it.

Never add `<NoWarn>` or `#pragma warning disable` to clear a new warning, and never pin a package to an older version to dodge a break without saying so. New obsolete warnings (`SYSLIB*`, `CS0618`, `ASPDEPR*`) go in the report; fix them only when trivial or asked. Under `TreatWarningsAsErrors` they fail the build instead: fix the ones with a one-line replacement named in the obsoletion message, and ask before adding the remaining ids to `WarningsNotAsErrors`, listing each with its count.

## 5. Outside the code

- Dockerfiles: image tags to the target major. Keep `-alpine`, `-noble`, and `-chiseled` variants. From .NET 10 there are no Debian images: map `-bookworm-slim` and other Debian tags to the default (Ubuntu 24.04) or `-noble`, and check each `apt-get install` package exists there. From .NET 9 the images don't ship zlib. Build the image when Docker is available; otherwise list it as not checked.
- CI: the SDK version in `setup-dotnet` or `UseDotNet@2`, and cache keys that embed it. Steps that parse `dotnet build` output need `--tl:off` (Terminal Logger is the default from .NET 9 in an interactive terminal).
- `dotnet-tools.json`: `dotnet-ef` to the EF Core major in use. A multi-targeted project needs `--framework` on every `dotnet ef` call from EF Core 10, scripts and pipeline steps included.
- After an EF Core major bump: `dotnet ef migrations has-pending-model-changes`. Pending changes from the upgrade alone mean a convention changed (known-traps.md lists the EF Core 10 ones that do this); report them, don't generate a migration silently.
- Hosting configured outside the repo (App Service runtime stack, Functions version, `FUNCTIONS_WORKER_RUNTIME`, the build agent image): list it for the user. A Functions app on Linux Consumption can't run .NET 10; say so before targeting it.

## 6. Report

```markdown
**Target**: net8.0 → net10.0 (SDK 10.0.x)
**Projects**: upgraded, in order; skipped (netstandard, .NET Framework) with the reason
**Functions model**: in-process → isolated per project, with the `func start` and JSON fixture results
**Packages**: from → to; removed as pruned (NU1510); left on the old version and why; transitive changes from the before and after snapshots; audit findings and what was done
**Breaking changes hit**: entry → fix (file)
**Outside the code**: global.json, Dockerfiles, CI, tools; for the user outside the repo: ...
**Build and tests**: clean build result vs baseline; new warnings by id and count; ids moved to `WarningsNotAsErrors` with approval
**Smoke checks**: each applicable check from known-traps.md with its result, or "not checked"
**Not done**: ...
```

Report each build, test, and image result as it ran. A step not run is "not run", never "passed".

Branches and commits follow the user's rules; this skill creates neither.