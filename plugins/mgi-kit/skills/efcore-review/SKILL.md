---
name: efcore-review
description: "Review EF Core data access for slow or wrong queries: N+1, filtering after ToList, SaveChanges in loops, Include row explosion, predicates that defeat an index, deep Skip/Take paging, unstable ordering, wrong tracking, ExecuteUpdate skipping concurrency, overlapping DbContext calls, concatenated raw SQL, missing indexes. Separates what the code proves from what needs a query plan; reports first. Use when an endpoint or job on EF Core is slow or runs too many queries, or a query or model change is about to merge (\"query chậm\", \"N+1\", \"review EF\", \"tối ưu query\"). Not for Dapper or raw ADO.NET, or a live database's metrics (see mgi-kit:azure-diagnose)."
argument-hint: "[file, folder, or endpoint; default: the current diff]"
---

# EF Core review

Find the data-access defects that cost round-trips, rows, scans, or correctness, and say how sure each one is. Source alone proves what the code does; it doesn't prove what the database does. Every finding is labeled with which of the two it rests on.

## Scope

- **After a change** (default when the working tree or branch has changes): the queries, repositories, and model configuration the diff touches, plus the callers of a touched repository method. Diff with `git diff HEAD` or `git diff <base>...HEAD`.
- **A named target**: the file, folder, endpoint, or job the user named, followed down to the `DbContext`.
- **Whole data layer**: only when asked.

Find the EF boundary yourself: the `DbContext`, `DbSet` properties, repository implementations, `IEntityTypeConfiguration` classes, `OnModelCreating`, and the migrations folder. Don't ask for paths that are in the repo. Read the provider (`UseSqlServer`, `UseAzureSql`, `UseNpgsql`, `UseSqlite`) and the EF Core version from the package reference; several rules below depend on both.

## Process

1. **Trace each query to where it executes.** Follow repository and helper methods into their implementation, not their interface name. Note the static type at each step: operators on `IQueryable<T>` run in SQL; once a value is a `List<T>`, array, or `IEnumerable<T>` produced by `AsEnumerable()` or a materializing call, every later `Where`, `Select`, `Count`, `OrderBy` runs in memory on rows already loaded. An `IEnumerable<T>` that still wraps a query runs it again on every enumeration.
2. **Count round-trips and writes along the call path.** Queries inside a loop, a navigation read inside a loop with lazy loading on, `SaveChanges` hidden in a repository `Add`, an audit hook, or a progress update. Note which calls share one `DbContext` instance.
3. **Check each query** against the table below.
4. **Hold the contract.** A fix must keep result membership and order, page-number access where the UI uses it, generated keys, transaction and partial-failure behavior, concurrency checks, and interceptor or domain-event side effects. A fix that changes one of these is a behavior change; say so.
5. **Gate on evidence** (next section) before writing anything up.

| Look for | Defect | Fix direction |
|---|---|---|
| A navigation or a query inside `foreach`, `Select(async ...)`, or per-row helper | N+1 | Project with `Select`, or `Include`, in one query; never turn on lazy loading in a server app |
| `ToList()`/`ToArray()`/`AsEnumerable()` then `Where`, `Count`, `Any`, `Sum`, `OrderBy` | Filtering or aggregating in memory | Keep composing on `IQueryable` and execute once; `AnyAsync` for existence, `CountAsync` only when the number is needed |
| Two or more sibling collection `Include`s on one query | Cartesian row explosion | Narrow projection first; otherwise `AsSplitQuery()` with a unique, stable order |
| One collection `Include` under a parent with large text or binary columns | The wide parent row repeated per child | Project only the needed columns |
| `.Year`, `.Date`, `ToLower()`, `ToUpper()`, `ToString()`, arithmetic on a column in `Where` or `OrderBy` | A predicate an ordinary index can't seek | Compare the bare column: half-open ranges for dates, a normalized or computed indexed column, a case-insensitive collation (SQL Server) or `citext` / `EF.Functions.ILike` (PostgreSQL) |
| `Contains(term)` on a text column in a search | A scan on every call | Keep it when the table is small; otherwise prefix search, full-text, or a trigram index on PostgreSQL. Each changes what matches; say which |
| `Skip(page * size)` on a large or growing table | Deep pages scan and discard | Keyset paging when the UI only goes next/previous; keep offset when it jumps to page N |
| `Skip`/`Take` without `OrderBy` on a unique key, or a second `OrderBy` where `ThenBy` was meant | Nondeterministic or wrongly ordered pages | Order by the sort key then a unique key, all with `ThenBy` |
| A query returning an unbounded list to an API or UI | Memory and payload grow with the table | Page or cap it; an export streams with `AsAsyncEnumerable()` instead of buffering |
| `SaveChanges` per item in a loop, through any layer | One transaction and round-trip per row | Save per batch when the contract allows; keep per-item saves where a partial failure must keep earlier rows |
| `ChangeTracker.Entries()`, `HasChanges()`, or `SaveChanges` per row in a long import on one context | Change detection over a growing graph | Count progress yourself; save and clear, or use a fresh context, per batch the import owns |
| Read-only entity results without `AsNoTracking` | Tracking cost and memory | Only when the result is proven read-only and is an entity or contains one; see the tracking table |
| `ExecuteUpdateAsync` / `ExecuteDeleteAsync` | Skips tracked state, concurrency tokens, `SaveChanges` interceptors, and client-side cascades | Keep when none of those matter; otherwise add the token predicate and check affected rows, or stay tracked |
| `Task.WhenAll` over calls that share one `DbContext`, or a context in a singleton or static field | Overlapping operations: `InvalidOperationException` or corrupted state | Await in sequence, or `IDbContextFactory` with one context per concurrent call |
| `FromSqlRaw`/`ExecuteSqlRaw` with `+` or `$"..."` built outside the call, `string.Format` into SQL | SQL injection | `FromSql`/`ExecuteSql` with an interpolated string at the call, or explicit parameters |
| `Expression.Constant(requestValue)` in a dynamic filter builder | A new SQL text and EF cache entry per value | Close over a variable so the value becomes a parameter |
| `.Contains()` on a local list inside a query, EF Core 10 or later | `IN (@p1, @p2, ...)`: many parameters and plan variants for long lists | Leave it for short lists; `EF.Parameter(list)` or `UseParameterizedCollectionMode` when lists run to hundreds |
| `HasData` with `DateTime.Now`, `DateTime.UtcNow`, or `Guid.NewGuid()` | A model that changes every build: pending model changes, migrations that throw from EF Core 9 | Constants |
| `Where`/`OrderBy` columns with no index in the model, configurations, or migrations | Possible scan | Report only with the evidence named in the next section |

Tracking, decided on the result graph rather than the return type:

| Result | Decision |
|---|---|
| Scalars or a DTO of scalars from `Select` | Nothing is tracked; `AsNoTracking` adds nothing, so don't report it |
| An entity, or a DTO holding an entity, that is edited and saved later | Keep tracking |
| A read-only entity graph | `AsNoTracking`, or better, a narrower projection |
| A read-only graph where the same entity appears many times and the consumer compares references | `AsNoTrackingWithIdentityResolution` |

Fix patterns, provider differences, and the edge cases for each row: [fixes.md](references/fixes.md). Read the section for a row before writing its finding or its fix.

## Gate findings on evidence

- **Proven by source**: the code path does it regardless of data: a query per row, a filter after `ToList()`, a `SaveChanges` per item, overlapping calls on one context, concatenated SQL, a predicate wrapped in a function. Report as a defect.
- **Needs runtime evidence**: anything whose cost depends on data volume, the deployed indexes, or the plan: a missing index, split vs single query, `AsNoTracking` on a small result, `EF.Constant` vs a parameter, compiling a query. Report it only when the code shows the query is hot (a list endpoint, a loop, a job over a table) and say what would confirm it: the SQL from `LogTo` or `Microsoft.EntityFrameworkCore.Database.Command` at `Information`, the plan, Query Store or `pg_stat_statements`.
- No `HasIndex` in one file doesn't mean no index. Check `OnModelCreating`, every `IEntityTypeConfiguration`, the migrations, and the FK convention (EF creates an index on each dependent foreign key unless a key or index already covers it) before saying an index is missing. When EF doesn't own the schema (no migrations, `ExcludeFromMigrations`, a database-first scaffold), say the database may still have it.
- A load, mutate, then one `SaveChanges` after the loop is a single save, not a per-row round-trip. Don't report it unless the batch is unbounded.
- When every reviewed path is sound, say "no actionable findings" with what was reviewed. Don't fill the report with general EF advice.

## Fixing

Only when the user asks, and one finding at a time:

- Show the SQL before and after when the app can run: `LogTo(Console.WriteLine, LogLevel.Information)` or the `Microsoft.EntityFrameworkCore.Database.Command` category, with `.TagWith("...")` on the query to find it. Report the statement count and rows before and after. Without a run, say the fix is unmeasured.
- Run the tests that cover the changed path. A behavior change listed in Process step 4 needs the user's agreement first.
- A new index goes in the model, then `dotnet ef migrations add <Name>` (with `--framework` on a multi-targeted project). Never apply a migration to a database: no `dotnet ef database update`, no `Migrate()` call, no script run. Show the migration and leave applying it to the user's pipeline.

## Report

```markdown
**Scope**: files, endpoints, and jobs reviewed; provider and EF Core version; whether EF owns the schema
**Defects (proven by source)**:
1. `path:line` (call path: Endpoint → Service.Method → Repo.Method) | what happens | cost: N+1 rows, full load, per-item commit, ... | fix
**Needs runtime evidence**:
1. `path:line` | the suspicion | what confirms it (SQL log, plan, Query Store / pg_stat_statements)
**Sound**: patterns checked and found fine, in one line
**Not checked**: what source can't show here (deployed indexes, data volume, plans)
```

Severity order inside each list: wrong results or data loss (overlapping context, unstable paging, a bulk write overwritten by tracked state, SQL injection), then cost that grows with rows (N+1, in-memory filtering, unbounded results, per-item saves), then constant-factor cost.
