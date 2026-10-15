# Fix patterns and edge cases

One section per row of the review table. Each says when the finding holds, the fix, and what the fix must not break.

## Contents

- [Materialization and repeated enumeration](#materialization-and-repeated-enumeration)
- [N+1 and lazy loading](#n1-and-lazy-loading)
- [Include explosion and split queries](#include-explosion-and-split-queries)
- [Index-compatible predicates](#index-compatible-predicates)
- [Paging](#paging)
- [Persistence in loops](#persistence-in-loops)
- [Change detection in long imports](#change-detection-in-long-imports)
- [Bulk updates and deletes](#bulk-updates-and-deletes)
- [DbContext lifetime and concurrency](#dbcontext-lifetime-and-concurrency)
- [Raw SQL](#raw-sql)
- [Dynamic query shapes](#dynamic-query-shapes)
- [Parameters, constants, compiled queries](#parameters-constants-compiled-queries)
- [`.Contains()` on a local list](#contains-on-a-local-list)
- [Index coverage](#index-coverage)

## Materialization and repeated enumeration

A helper that returns `List<T>` has already run its query; everything the caller does afterwards is in memory. A helper that returns `IEnumerable<T>` over a query runs it again each time it is enumerated (`Count()` then `foreach` is two queries).

```csharp
// Loads every candidate, then filters in memory.
var candidates = await repo.GetCandidatesAsync(ct);   // returns List<Order>
return candidates.Where(o => o.CreatedAt < cutoff).ToList();

// Filters in SQL.
return await repo.QueryCandidates()                   // returns IQueryable<Order>
    .Where(o => o.CreatedAt < cutoff)
    .ToListAsync(ct);
```

When the repository pattern forbids exposing `IQueryable`, add a method that takes the filter, or a specification, rather than widening every caller. Several summaries of one set (`Count`, `Sum`, `Max`) can be one query with `GroupBy(_ => 1).Select(...)` or a projection, instead of loading the set once and reducing it several times.

## N+1 and lazy loading

Lazy loading is on when `UseLazyLoadingProxies()` is called, or `ILazyLoader` is injected into entities, and navigations are `virtual`. With it on, every navigation read in a loop is a query. Without it, the same read returns null or empty, which is a correctness bug, not a performance one; report it as such.

```csharp
var summaries = await db.Orders
    .Where(o => o.CustomerId == customerId)
    .Select(o => new OrderSummary(o.Id, o.Items.Count, o.Items.Sum(i => i.Price)))
    .ToListAsync(ct);
```

A loop of `await repo.GetByIdAsync(id)` over a list of ids becomes one `Where(x => ids.Contains(x.Id))`. Keep the input order when the caller relies on it: load into a dictionary and map the ids in order.

## Include explosion and split queries

Rows returned by a single query with sibling collection Includes are the product of the collection sizes per parent. A chain (`Include(a => a.Items).ThenInclude(i => i.Options)`) is not a product of siblings, and reference navigations add no rows.

- First choice: project only what the consumer reads.
- Then `AsSplitQuery()`: one statement per collection. It costs extra round-trips, and the statements run at different moments, so concurrent writes can make them disagree; when the data must be consistent, run them in a snapshot or serializable transaction, or keep a single query.
- Split queries with `Skip`/`Take` need an order by a unique key, or the pages of the parent and child statements can differ.
- A project-wide `UseQuerySplittingBehavior(SplitQuery)` changes every query; a single query that needs `AsSingleQuery()` keeps it.

## Index-compatible predicates

| Pattern | Rewrite |
|---|---|
| `o.CreatedAt.Year == year` | `o.CreatedAt >= start && o.CreatedAt < start.AddYears(1)` |
| `o.CreatedAt.Date == day` | `o.CreatedAt >= day && o.CreatedAt < day.AddDays(1)` |
| `u.Email.ToLower() == email.ToLower()` | SQL Server: the default collation is already case-insensitive, so compare directly. PostgreSQL: a `citext` column, a stored lowercase column with an index, or an expression index on `lower(email)` |
| `p.Price * 1.1m > x` | `p.Price > x / 1.1m` |
| `o.Total.ToString().StartsWith(s)` | A real comparison on the typed column |
| `EF.Functions.Like(name, "%term%")`, `name.Contains(term)` | Prefix `term%` can seek; arbitrary substrings need full-text search (SQL Server) or a `pg_trgm` GIN index (`HasMethod("gin").HasOperators("gin_trgm_ops")` in Npgsql). Both change what matches; state it |

Don't claim a scan from LINQ alone: computed columns, expression indexes, and the other predicates in the query change the plan. Say "likely cannot use an index on X" and what confirms it.

Comparing with `string.Equals(a, b, StringComparison.OrdinalIgnoreCase)` doesn't translate; EF throws instead of filtering in memory. On PostgreSQL `EF.Functions.ILike` is case-insensitive but cannot use a plain B-tree index.

## Paging

- Offset paging (`Skip`/`Take`) reads and discards every skipped row. It stays fine for small tables and shallow pages, and it is the only kind that supports jumping to page N and showing a total.
- Keyset paging seeks from the last row seen. For a descending `(CreatedAt, Id)` order the condition is `o.CreatedAt < lastDate || (o.CreatedAt == lastDate && o.Id < lastId)`, not two independent bounds. It needs an index matching the order.
- Switching from offset to keyset changes the API contract (`page` becomes a cursor). Check the frontend with `mgi-kit:api-contract` and agree it with the user before changing it.
- Any page needs `OrderBy` on the sort key plus a unique key (`ThenBy(o => o.Id)`). Ordered offset pages can still shift when rows are inserted between requests; ordering fixes nondeterminism, not that.

## Persistence in loops

- `SaveChanges` per item: one transaction and one round-trip per row. Batching (save every N, or once) is right for imports where all-or-nothing per batch is acceptable. Keep per-item saves where a failure must not roll back earlier items, and say why.
- Generated keys are available on the entity objects after `SaveChanges`; read them from the references, never assume ids are allocated in input order.
- An import that retries must not double-insert: a unique key on the source identity, or upsert, or a checkpoint. Chunking alone is not idempotency, and check-then-insert without a unique constraint races.

## Change detection in long imports

Every saved entity stays tracked on the context. `SaveChanges`, `HasChanges()`, and `ChangeTracker.Entries()` scan all of them, so cost per row grows with the rows already imported.

- Count progress in a local variable instead of querying the tracker.
- When the import owns the context: `ChangeTracker.Clear()` after each saved batch, or one context per batch from `IDbContextFactory`. Never clear a context that has other pending work.
- `AutoDetectChangesEnabled = false` only around a proven redundant scan, restored in `finally`, with an explicit `DetectChanges()` before saving if entities were mutated.

## Bulk updates and deletes

`ExecuteUpdateAsync` and `ExecuteDeleteAsync` (EF Core 7+) run immediately, without loading rows.

- They don't update entities already loaded on the context. A later `SaveChanges` of a tracked entity can write its stale value over the bulk change, even in one request.
- They don't check concurrency tokens. Put the token in the `Where`, set it in the update when it isn't database-generated, and check the returned row count.
- They don't run `SaveChanges` interceptors, domain events raised there, audit or outbox writes, or cascades EF would do on the client. They aren't atomic with a later `SaveChanges` unless both run in one explicit transaction.
- EF Core 10 takes a plain lambda for setters, so conditional updates are `if` blocks inside it.

## DbContext lifetime and concurrency

One context, one operation at a time. `Task.WhenAll(repoA.GetAsync(), repoB.GetAsync())` over repositories that share the scoped context throws or corrupts state. Parallel reads need `IDbContextFactory<T>` and a context per task, disposed after. A context held by a singleton, a static field, or a `BackgroundService` field outlives its scope; background services create a scope or a context per unit of work.

## Raw SQL

- `FromSql($"... {value}")` and `ExecuteSql($"...")` turn interpolated values into parameters.
- `FromSqlRaw` and `ExecuteSqlRaw` take the string as-is. A string built with `+`, `string.Format`, or an interpolated string assigned to a variable first is injectable. Pass `SqlParameter` / `NpgsqlParameter`, or switch to `FromSql`.
- Identifiers (table or column names) can't be parameters; validate them against a fixed list.

## Dynamic query shapes

Building `Expression.Constant(requestValue)` makes each value part of the expression tree, so each value gets its own SQL text and EF cache entry. Close over a variable instead:

```csharp
Expression<Func<string>> valueAccess = () => filterValue;
var comparison = Expression.Equal(property, valueAccess.Body);
```

Fixed structural constants (a status literal the code always uses) are fine. Report this as cache and plan churn, not a memory leak.

## Parameters, constants, compiled queries

- Captured variables become parameters; literals in the LINQ stay literals. Keep the defaults without workload evidence.
- `EF.Parameter(x)` (EF Core 9+) forces a parameter; `EF.Constant(x)` (8.0.2+) forces a literal. Both are plan-tuning choices that need a plan or Query Store data behind them.
- `EF.CompileAsyncQuery` saves the translation lookup on one very hot, simple query shape. It doesn't make the database faster and isn't worth reporting for ordinary endpoints.

## `.Contains()` on a local list

EF Core 8 and 9 send the list as one JSON parameter (`OPENJSON` on SQL Server, an array on PostgreSQL). EF Core 10 on SQL Server sends `IN (@p1, @p2, ...)` by default: better estimates for short lists, more plan variants and a parameter-count limit (2,100 on SQL Server) for long ones. For lists that run to hundreds, `EF.Parameter(ids).Contains(x.Id)` per query or `UseParameterizedCollectionMode(ParameterTranslationMode.Parameter)` globally.

## Index coverage

- Evidence for an existing index: `HasIndex` in `OnModelCreating` or an `IEntityTypeConfiguration`, `[Index]` on the entity, `CreateIndex` in a migration, or the FK convention: EF indexes each dependent foreign key unless an existing key or index already starts with those columns.
- A composite index serves equality columns first, then one range or sort column. An index on `(CustomerId)` covers the relationship but not `Where(CustomerId == x).OrderBy(CreatedAt)` on a large customer; `(CustomerId, CreatedAt)` does.
- Recommend an index only for a query the code shows is hot, with the column order and the write cost. Add it to the model and create the migration; applying it is the user's call.
- When EF doesn't own the schema, give the index as a recommendation for whoever manages the database.
