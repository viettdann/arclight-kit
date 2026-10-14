---
name: efcore-review
description: "Review EF Core data access for slow or wrong queries: N+1, filtering after ToList, SaveChanges in loops, Include row explosion, predicates that defeat an index, deep Skip/Take paging, unstable ordering, wrong tracking, ExecuteUpdate skipping concurrency, overlapping DbContext calls, concatenated raw SQL, missing indexes. Separates what the code proves from what needs a query plan; reports first. Use when an endpoint or job on EF Core is slow or runs too many queries, or a query or model change is about to merge (\"query chậm\", \"N+1\", \"review EF\", \"tối ưu query\"). Not for Dapper or raw ADO.NET, or a live database's metrics (see mgi-kit:azure-diagnose)."
---

# EF Core review

Find the data-access defects that cost round-trips, rows, scans, or correctness, and say how sure each one is. Source alone proves what the code does; it doesn't prove what the database does. Every finding is labeled with which of the two it rests on.

Before starting, read `references/codex-workflow.md` for the complete workflow, checks, and report format. Load its other references only when the relevant step calls for them.

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.
