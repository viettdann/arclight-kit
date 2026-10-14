# Changelog

All notable changes to `mgi-kit` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

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

## [0.3.0] - 2026-10-05

### Added

- `api-contract`: HTTP method changes, routes moved from anonymous to authenticated, error-shape drift (ProblemDetails versus a custom DTO), offset-to-cursor pagination, and a committed OpenAPI or NSwag file left stale.

## [0.2.0] - 2026-10-03

### Added

- `dotnet-upgrade`: inventories projects, where each TFM is set, central package files, Docker images, CI, and tools; fetches Microsoft's breaking-change pages for each version crossed; records a build and test baseline; upgrades consumers before dependencies so the solution builds at every step; bumps runtime-tied packages with the TFM; checks EF Core model drift after an EF major bump; stops at .NET Framework projects.

## [0.1.0] - 2026-10-03

First release.

### Added

- `api-contract`, adapted from github/awesome-copilot (MIT): audits ASP.NET controllers, Minimal API endpoints, and DTOs against their TypeScript/JavaScript consumers in both directions; diff-scoped by default. `refactor` and `verifier` run it when it is installed.
