# Changelog

All notable changes to `arc-kit` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-03

First release.

### Added

- `/arc-kit:arc`: session working rules (chat language, scope of a go-ahead, shared-worktree git, docs, comments, commits, migrations, UI), including no placeholders in code and names and strings findable by grep.
- Workflow: `brainstorming` (design dialogue, approval gate, design doc in `docs/plans/`), `plan-auditor` (stress-tests a plan before execution), `executor` (implements it with TDD, sub-agents, and continuous verification), `verifier` (completeness check against the plan, then parallel review for reuse, quality, efficiency, correctness and security, comments, and docs), `handoff` (session handoff file instead of `/compact`).
- `refactor`: pins behavior with characterization tests, maps the contract surface and its consumers, and moves in small verified steps; wide scopes stop for approval first.
- `fresh-air` blocks a project's own skills, commands, and `CLAUDE.md`, and restores them; the `comment-lint` hook flags wrapped, overlong, banner, and narrative comments.
