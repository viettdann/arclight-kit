---
name: dotnet-upgrade
description: "Upgrade a .NET solution to a newer target framework (for example net8.0 to net10.0) with its runtime-tied packages, SDK pin, Docker images, CI, and tools. Inventories every project and where its TFM is set, reads Microsoft's breaking-change pages for each version crossed, records a build and test baseline, upgrades in an order that keeps the solution building, and reports new warnings and what lives outside the repo. Use when moving to a new .NET version or off one that is losing support (\"upgrade .NET\", \"nâng .NET\", \"lên .NET 10\", \"net8 hết support\", \"migrate to net10\"). Not for porting .NET Framework apps (it inventories them and stops), or for bumping a single package."
---

# .NET upgrade

Move the solution to the target framework with the build and tests green at every step, changing only what the upgrade requires. Facts about versions, support dates, and breaking changes are fetched, not recalled.

Follow applicable AGENTS.md instructions. Use Vietnamese in chat and English in files unless the user requests otherwise. Fetch pages with the session's available web tools; if none is available, list the pages that weren't read in the report and treat their content as unverified.

## 1. Target and baseline

- Target: the one the user named; otherwise the latest GA LTS, checked on `https://dotnet.microsoft.com/platform/support/policy/dotnet-core`. STS or preview only when asked.
- `dotnet --list-sdks`: if no SDK for the target is installed, stop and tell the user; don't install one.
- Build and test the whole solution before any edit. Record failing tests and the warning count; that is the baseline every later step is compared to.

## 2. Inventory

Read, don't edit:

- Projects: `git ls-files '*.csproj' '*.fsproj' '*.vbproj'`. For each: `TargetFramework` or `TargetFrameworks`, `Sdk`, `LangVersion`. The TFM may be set in `Directory.Build.props` instead of the project; grep both.
- Classify each TFM:
  - `netX.0` or `netcoreapp*`: in scope.
  - `netstandard2.x`: leave as is unless asked; it exists to be shared with older consumers.
  - `net4x` (.NET Framework): out of scope. Name its project type (ASP.NET MVC 5, Web Forms, WCF service, WinForms, WPF, class library) and stop for a separate plan; Web Forms and WCF server have no in-place path.
- Central files: `global.json` (SDK version and `rollForward`), `Directory.Build.props` and `.targets`, `Directory.Packages.props`, `NuGet.config`.
- Packages: `dotnet list package --outdated`, `--vulnerable --include-transitive`, `--deprecated`. Runtime-tied packages (`Microsoft.AspNetCore.*`, `Microsoft.EntityFrameworkCore.*`, `Microsoft.Extensions.*`, `System.*` packages that ship with the runtime) move with the TFM major; third-party packages move only when the new TFM requires it.
- Outside the projects: Dockerfiles (`mcr.microsoft.com/dotnet/sdk`, `aspnet`, `runtime` tags), CI (`actions/setup-dotnet` `dotnet-version`, Azure DevOps `UseDotNet@2`), `.config/dotnet-tools.json` (`dotnet-ef`), and hosting config kept in the repo (Bicep, Terraform, pipeline YAML runtime stacks).
- More than about ten projects in scope: show the inventory and the step order (section 4), then continue within the existing upgrade authorization. Ask only about a material scope decision (a project to leave behind, a third-party major the user may not want).

## 3. Read the breaking changes

- For each major version crossed (net8.0 to net10.0 crosses 9 and 10), fetch "Breaking changes in .NET N" under `https://learn.microsoft.com/dotnet/core/compatibility/`, and the EF Core breaking-changes page for each EF Core major crossed.
- Keep only the entries for areas the inventory shows in use: ASP.NET Core, EF Core, SDK and MSBuild, containers, serialization, networking, cryptography. List each with the projects or files it hits before editing.
- A third-party package that needs a new major: read its release notes for that major the same way.

## 4. Upgrade

Order:

- TFM set centrally, or a solution of a few projects: change it once and fix the build in one step.
- Otherwise project by project, consumers first: host projects (API, web, workers, functions) and their test projects, then down the `ProjectReference` graph to the leaves. A project on the new TFM can reference one on the old TFM, never the reverse, so upgrading a leaf first breaks every consumer still on the old TFM.

Each step:

1. Change the TFM where it is actually set. Leave `LangVersion`, `Nullable`, `ImplicitUsings`, and other properties alone unless the build requires a change.
2. Bump the runtime-tied packages to the matching major, in `Directory.Packages.props` when central package management is on. Bump a third-party package only when restore or build fails without it, one package at a time.
3. Restore, build, and run the tests of the projects changed in this step. Compare with the baseline.
4. Fix errors with the smallest change that matches the breaking-change entry. A behavioral change from section 3 that hits this code gets a test, or a line in the report when no test can observe it.

Never add `<NoWarn>` or `#pragma warning disable` to clear a new warning, and never pin a package to an older version to dodge a break without saying so. New obsolete warnings (`SYSLIB*`, `CS0618`, `ASPDEPR*`) go in the report; fix them only when trivial or asked.

## 5. Outside the code

- `global.json`: the SDK version for the target; keep the `rollForward` policy.
- Dockerfiles: image tags to the target major, keeping the distro variant (`-alpine`, `-noble`, `-chiseled`).
- CI: the SDK version in `setup-dotnet` or `UseDotNet@2`, and cache keys that embed it.
- `dotnet-tools.json`: `dotnet-ef` to the EF Core major in use.
- After an EF Core major bump: `dotnet ef migrations has-pending-model-changes`. Pending changes from the upgrade alone mean a convention changed; report them, don't generate a migration silently.
- Hosting configured outside the repo (App Service runtime stack, Functions version, the build agent image): list it for the user.

## 6. Report

```markdown
**Target**: net8.0 → net10.0 (SDK 10.0.x)
**Projects**: upgraded, in order; skipped (netstandard, .NET Framework) with the reason
**Packages**: from → to; left on the old version and why
**Breaking changes hit**: entry → fix (file)
**Outside the code**: global.json, Dockerfiles, CI, tools; for the user outside the repo: ...
**Build and tests**: result vs baseline; new warnings by id and count
**Not done**: ...
```

Branches and commits follow the user's rules; this skill creates neither.
