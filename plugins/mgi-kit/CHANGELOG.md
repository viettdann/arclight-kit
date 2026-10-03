# Changelog

All notable changes to `mgi-kit` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-10-04

Brings the Codex package up to the Claude line's 0.2.0.

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
