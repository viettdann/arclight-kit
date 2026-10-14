# Changelog

All notable changes to `mgi-kit` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [1.3.0] - 2026-10-14

- Sync main through `5fe23ac`; preserve Codex packaging, runtime adaptation, and patch hooks.
- Add EF Core review, Azure Pipelines advice/diagnostics, work-item briefs, and live Azure diagnostics.
- Extend .NET upgrade/API contract guidance and port dotnet-guard to completed Codex patches.

## [0.7.0] - 2026-10-14

### Added

- `efcore-review`: reviews EF Core data access for N+1 and lazy loading, filtering after materialization, repeated enumeration, `SaveChanges` hidden in loops, Include row explosion, predicates that defeat an index, deep offset paging and unstable ordering, tracking decided on the result graph, `ExecuteUpdate`/`ExecuteDelete` skipping concurrency tokens and interceptors, overlapping `DbContext` calls, concatenated raw SQL, dynamic expression churn, `.Contains()` on local lists under EF Core 10, and non-deterministic `HasData`. Each finding is labeled proven by source or needing runtime evidence; a missing index needs the model, configurations, migrations, and FK convention checked first, and a clean review says so in one line. Fixes only when asked, with SQL before and after; a new index becomes a migration that the skill never applies. Fix patterns and SQL Server and PostgreSQL differences in `references/fixes.md`.
- `dotnet-guard` hook (`PostToolUse` on `Edit|Write`, on by default, `dotnet_guard_enabled` turns it off): flags a newly added skipped test, `#pragma warning disable`, `[SuppressMessage]`, `#nullable disable`, empty `catch`, sleep in a test project, `NoWarn`, `WarningsNotAsErrors`, warnings-as-errors or nullable or analyzers turned off, `VersionOverride` or central package management turned off, and a lowered `.editorconfig` severity, and exits 2 so Claude fixes the cause or keeps the line with a stated reason. Only a rise in an identical line's count is new; each line is flagged once per session. Tested by `dotnet_guard_test.py`.
- `dotnet-upgrade`: `references/known-traps.md`, read for each major crossed, with a grep table that decides which entries apply: `Microsoft.OpenApi` 2.x and 3.x (missing from the ASP.NET Core breaking-change page), EF Core changes that generate migrations (`json` columns on Azure SQL, complex type column names), `HasData` with `DateTime.Now` and migrations in a user transaction, HttpClientFactory handler type, keyed service fallback, forwarded headers, DI validation in Development, `BackgroundService` startup and exceptions, configuration `null` binding, cookie redirects becoming 401 on API endpoints, C# 14 and 15 keywords and span overloads, SqlClient 7 Entra ID package, and a smoke and security checklist for the report.

### Changed

- `dotnet-upgrade`: the `global.json` SDK pin moves before the first build on the new TFM instead of after the code is fixed. The baseline is a clean build with warnings by id, plus a resolved package snapshot diffed in the report. Restore warnings are read before building: `NU1510` removes the package, transitive audit findings are fixed or pinned with the advisory named, a version-less `PackageReference` gets a version. Under `TreatWarningsAsErrors`, one-line obsoletion fixes are made and the rest go to `WarningsNotAsErrors` only with approval. Multi-targeted libraries add the new TFM, apps replace it. `BinaryFormatter` stops the upgrade for a decision. Debian image tags map to Ubuntu from .NET 10, zlib is gone from .NET 9 images, CI output parsers need `--tl:off`, and `dotnet ef` needs `--framework` on multi-targeted projects. Every build, test, and image result is reported as it ran.
- `api-contract`: controllers and Minimal APIs are checked against their own JSON option sets; `WhenWritingNull` (absent keys read as `undefined`), `PropertyNameCaseInsensitive = false`, `RespectNullableAnnotations`, and strict `NumberHandling` are contract changes; nullable reference types make non-nullable request properties and Minimal API parameters required (`#nullable disable warnings` doesn't turn that off); `AddValidation()` in .NET 10 turns existing annotations into new 400s; a changed OpenAPI generator or OpenAPI 3.1 nullability is diffed as a document; cookie-authenticated API calls get 401 instead of a login redirect from ASP.NET Core 10. Findings cite both files, and a clean audit says so in one line.
- Descriptions: `azure-diagnose` gains a "Use when" and excludes failed pipeline runs and locally reproducible bugs; `ado-pipelines-advisor` excludes a deployed app failing at runtime; `ado-work-item` excludes pipeline runs; `api-contract` excludes query performance; `dotnet-upgrade` is shorter.

## [0.6.0] - 2026-10-14

### Added

- `dotnet-upgrade`: Azure Functions in-process to isolated worker migration (`references/functions-isolated.md`). It detects in-process projects (support ends 2026-11-10) and migrates the model on the current TFM before the TFM change: project SDK, extensions, startup, bindings, logging, HTTP, System.Text.Json fixtures, `FUNCTIONS_WORKER_RUNTIME`, Linux Consumption and Flex limits. Workspace checks run on every Functions project: `host.json`, host version, deprecated and identity-based settings, Durable task hub, `local.settings.json` in git, retry, blocking calls, cancellation, per-call clients. Adapted from Azure/azure-functions-skills (MIT, Microsoft).
- `azure-diagnose` Audit:
  - Active Azure service issues printed first.
  - Resource Health `Unavailable` and `Degraded`.
  - In-process .NET Functions, Functions hosts older than 4.x, and Linux Consumption apps.
  - Key Vault secrets, keys and certificates expired or expiring within 30 days, read through ARM with Reader, never values.
  - Standard load balancers with no backend pool as idle candidates.
- `azure-diagnose` Diagnose:
  - Resource Health and the App Service and Functions deployment history in the timeline.
  - Disabled Functions triggers and Flex Consumption metrics.
  - Service Bus failure reasons, lock loss, client lifetime, AMQP ports and data roles.
  - A telemetry coverage query, Resource Graph queries, and the Cost Management query limits.
  - Reports mark the cause confirmed or suspected.
  - Facts taken from microsoft/azure-skills and Azure/azure-functions-skills (MIT, Microsoft).
- `ado-pipelines-advisor`: data-plane role check for app identities in deployed Bicep and Terraform (review rule S13), and .NET Functions packaging: publish the project not the solution, `local.settings.json` kept out of the artifact and git, `FUNCTIONS_WORKER_RUNTIME` matching the build.

## [0.5.0] - 2026-10-14

### Added

- `ado-work-item`: reads one work item by ID or URL (fields, rich text, test steps, ancestors, links, pull requests, attachments, comments) and turns it into a brief: the current ask after later comments, done conditions marked stated or inferred, repro, what is already merged, and open questions. Read-only.
- `azure-diagnose`: read-only investigation of live App Service, Functions, Container Apps and jobs, Container Instances, PostgreSQL flexible server, and Service Bus problems. Audit mode (`audit.py`) surveys a tenant and lists what is failing now, what is at risk (runtime support dates from endoflife.date, shared Basic plans, sustained load, warnings), and what has no logs, plus 30-day spend against the 30 days before, resources whose cost rose, idle candidates with their cost, and open Advisor cost recommendations (Cost Management and Resource Graph, no MCP). `find.py` locates a resource across every tenant `az login` knows and reports where its logs go; the skill builds a timeline from the activity log and works through KQL queries and metrics, all run against real workspaces.
- `ado-pipelines-advisor`: Diagnose mode and `run-failure.py`, which print a run's validation errors and each failed step with its issues and log tail.

### Fixed

- `ado-pipelines-advisor` scripts asked az for a token in the default subscription's tenant, so an organization in another tenant answered 401. They now read the organization's tenant from the `X-VSS-ResourceTenant` header (`ADO_TENANT` overrides).

## [0.4.0] - 2026-10-14

### Added

- `ado-pipelines-advisor`, from 4mgi-devops-claude-skills: writes, optimizes, reviews, and previews Azure Pipelines YAML against verified rules (compile time versus runtime expressions, output variables, conditions, triggers, deployment jobs, secrets, task versions), with per-target deploy patterns and read-only scripts for repo detection, task-version checks, server-side preview, and step durations.

## [1.2.0] - 2026-10-05

### Changed

- Sync the Codex package with main through `f2bb39d` using a recorded Git merge; adapt new instructions and checks to Codex.

## [1.1.0] - 2026-10-04

Brings the Codex package up to the Claude line's 0.2.0.

## [0.3.0] - 2026-10-05

### Added

- `api-contract`: HTTP method changes, routes moved from anonymous to authenticated, error-shape drift (ProblemDetails versus a custom DTO), offset-to-cursor pagination, and a committed OpenAPI or NSwag file left stale.

## [0.2.0] - 2026-10-03

### Added

- `dotnet-upgrade`: inventories projects, where each TFM is set, central package files, Docker images, CI, and tools; fetches Microsoft's breaking-change pages for each version crossed; records a build and test baseline; upgrades consumers before dependencies so the solution builds at every step; bumps runtime-tied packages with the TFM; checks EF Core model drift after an EF major bump; stops at .NET Framework projects.

## [1.0.0] - 2026-10-03

### Changed

- Package the API contract audit for Codex with portable and compatibility manifests and skill UI metadata.
- Retain the API audit procedure and upstream MIT attribution.

## [0.1.0] - 2026-10-03

First release.

### Added

- `api-contract`, adapted from github/awesome-copilot (MIT): audits ASP.NET controllers, Minimal API endpoints, and DTOs against their TypeScript/JavaScript consumers in both directions; diff-scoped by default. `refactor` and `verifier` run it when it is installed.
