# Known upgrade traps

Changes that the fetched breaking-change pages miss, bury, or describe without the fix. Read the section for each major version crossed and each area the inventory shows in use. The fetched pages stay the source of truth: when an entry here disagrees with them, the page wins. The net11.0 entries were collected from previews; confirm each against the GA page.

## Grep first

Run these over the repo after the inventory. A hit names the entry to read; no hit means the entry is skipped and not mentioned.

| Grep | Crossing | Entry |
|---|---|---|
| `BinaryFormatter` | 9 | Stop: always throws |
| `HasData(` near `DateTime.Now`, `DateTime.UtcNow`, `Guid.NewGuid()` | 9 | EF pending model changes |
| `BeginTransaction` in the same method as `Migrate(` or `MigrateAsync(` | 9 | EF migrations in a user transaction |
| `as HttpClientHandler`, `(HttpClientHandler)` near `ConfigurePrimaryHttpMessageHandler` | 9 | HttpClientFactory handler type |
| `FromKeyedServices` | 9 | Keyed fallback removed |
| `KnownProxies`, `KnownNetworks`, `UseForwardedHeaders` | 9, 10 | Forwarded headers |
| `System.Linq.Async` | 10 | AsyncEnumerable is built in |
| `WebHostBuilder`, `IWebHost`, `AddRazorRuntimeCompilation`, `IActionContextAccessor`, `WithOpenApi(` | 10 | ASP.NET Core obsoletions |
| `Microsoft.OpenApi.Models`, `Microsoft.OpenApi.Any`, `OpenApiString`, `.Nullable =` in schema transformers | 10, 11 | Microsoft.OpenApi v2 and v3 |
| `BackgroundService` | 10, 11 | Startup thread, unhandled exceptions |
| `UseAzureSql`, `UseCompatibilityLevel`, `ToJson()`, primitive collections | 10 | EF `json` column type |
| `ComplexProperty` | 10 | EF complex type column names |
| `Application Name` in connection strings | 10 | EF injected application name |
| `.Contains(` on a local collection inside a query | 10 | EF parameterized collections |
| `IExceptionHandler` | 10 | Diagnostics suppressed on handled exceptions |
| `Rfc2898DeriveBytes(`, `SslStream` cipher properties | 10 | SYSLIB0058, SYSLIB0060 |
| `XmlSerializer` | 10 | `[Obsolete]` properties now serialized |
| a local or member named `field` or `extension` | 10 | C# 14 keywords |
| `apt-get`, `:8.0-bookworm`, `-bookworm-slim`, `zlib` in Dockerfiles | 9, 10 | Container images |
| `Authentication=Active Directory` in SQL connection strings | 11 | SqlClient 7 Entra ID package |

## net8.0 → net9.0

- **`BinaryFormatter` always throws.** Stop and ask; replacing it changes a wire or storage format, and the choice (System.Text.Json, MessagePack, protobuf, the compatibility package) is the user's.
- **EF Core 9 throws on pending model changes** in `Migrate()`, `MigrateAsync()`, and `dotnet ef database update`. The usual cause after an upgrade is non-deterministic seed data: `HasData` with `DateTime.Now`, `DateTime.UtcNow`, or `Guid.NewGuid()` produces a new model on every build. Replace those with constants (`new DateTime(2024, 1, 1, 0, 0, 0, DateTimeKind.Utc)`, a fixed `Guid`). Ignoring `PendingModelChangesWarning` hides schema drift; only with the user's say-so.
- **EF Core 9 throws when `Migrate()` runs inside a user transaction.** Remove the outer transaction; migrations manage their own.
- **EF tools can't load `Microsoft.EntityFrameworkCore.Design`** from SDK 9.0.200: add `<Publish>true</Publish>` to that `PackageReference`.
- **HttpClientFactory's primary handler is `SocketsHttpHandler`.** A cast to `HttpClientHandler` throws `InvalidCastException`; configure `SocketsHttpHandler` instead.
- **`[FromKeyedServices]` no longer falls back to the unkeyed registration**; it throws. Register the keyed service.
- **Forwarded headers from proxies outside `KnownProxies` and `KnownNetworks` are ignored.** Behind App Service, Container Apps, or Front Door the client IP and scheme change. Add the real proxy ranges; never clear the lists to accept every source.
- **`ValidateOnBuild` and `ValidateScopes` are on in Development.** A DI registration that was silently wrong now throws at startup; fix the registration, don't turn validation off.
- **Environment variables override `runtimeconfig.json`.**
- **Floating-point to integer conversions saturate** on x86 and x64.
- **Containers: images no longer install zlib.** Add the package only when a native dependency needs it.
- **Terminal Logger is the default in interactive terminals.** Scripts that parse `dotnet build` output need `--tl:off` or `MSBUILDTERMINALLOGGER=off`.
- **Visual Studio 17.12 or later** is needed to target net9.0; tell the user when the team's VS is older.

## net9.0 → net10.0

### SDK and NuGet

- **NU1510**: a direct `PackageReference` that the shared framework now provides is pruned. Remove the reference (often `System.Text.Json`, `System.Net.Http`, `Microsoft.Extensions.*` in an ASP.NET Core project) instead of silencing the warning.
- **A `PackageReference` without a version is an error.** Add the version or move it to `Directory.Packages.props`.
- **Restore audits transitive packages.** New `NU1901`–`NU1904` warnings are real findings: upgrade the package that pulls the vulnerable one in, or pin the transitive package in CPM with a comment naming the advisory. Never add them to `NoWarn`.
- **`dotnet new sln` writes `.slnx`.** Scripts that create or glob `*.sln` need `--format sln` or an update.
- CLI diagnostics go to stderr, `--interactive` defaults to true for a user (pass `--interactive false` in scripts), HTTP package sources error in `dotnet package list` and `search`.

### C# 14

- `field` is a keyword inside property accessors: a local named `field` is error CS9272, a member read without `this.` is warning CS9258. Rename or write `@field`.
- `extension` can't name a type, alias, or type parameter.
- Span overloads win: `array.Contains(x)` inside an expression tree can bind to `MemoryExtensions.Contains` and fail EF translation; `array.Reverse()` can bind to the in-place span version. Cast to `IEnumerable<T>` or call `Enumerable.Contains` explicitly.

### ASP.NET Core

- Obsolete: `WebHostBuilder`, `IWebHost`, `WebHost` (move to `WebApplication.CreateBuilder`), `IActionContextAccessor`, `AddRazorRuntimeCompilation`, `WithOpenApi()`, `<IncludeOpenAPIAnalyzers>`, the old `IPNetwork` and `ForwardedHeadersOptions.KnownNetworks` (use `System.Net.IPNetwork` and `KnownIpNetworks`), the `Microsoft.Extensions.ApiDescription.Client` package.
- **`Microsoft.AspNetCore.OpenApi` 10 brings `Microsoft.OpenApi` 2.x, and this is not on the ASP.NET Core breaking-changes page.** `Microsoft.OpenApi.Models` and `Microsoft.OpenApi.Any` are gone (all types live in `Microsoft.OpenApi`); `OpenApiString` and `OpenApiAny` become `JsonNode`; `OpenApiSecurityScheme.Reference` becomes `OpenApiSecuritySchemeReference`; `operation.Parameters`, `Responses`, and `document.Components` collections can be null; `OpenApiSchema.Nullable` is removed because OpenAPI 3.1 writes `type: ["string", "null"]`. Every document and operation transformer needs a pass. A generated TypeScript client built from the new document can change nullability and names; run `mgi-kit:api-contract` on it.
- **API endpoints return 401 or 403 instead of a cookie login redirect.** It applies to `[ApiController]`, Minimal APIs that read or write JSON, SignalR hubs, and `TypedResults` endpoints. A frontend that followed the redirect to detect an expired session now gets a 401.
- **`IExceptionHandler.TryHandleAsync` returning `true` suppresses the diagnostics event.** Log security-relevant failures (auth, authorization, validation of untrusted input) before returning `true`.

### Hosting and configuration

- **`BackgroundService.ExecuteAsync` runs entirely on a background thread.** Synchronous code before the first `await` no longer delays the start of the other hosted services. When something depended on that order, move it to `StartAsync` or `IHostedLifecycleService.StartingAsync`.
- **Configuration binds JSON `null` as `null`** (it was `""`) and `[]` as an empty array (it was ignored). A property with a non-null default is overwritten by a `null` in `appsettings.*.json` or an App Service setting.

### EF Core 10

- **`json` column type on Azure SQL** (`UseAzureSql`) or compatibility level 170 and above: JSON and primitive-collection columns move from `nvarchar(max)` to `json`, and the next migration alters them. `DISTINCT` over JSON arrays fails. Keep the old type with `UseCompatibilityLevel(160)` or `HasColumnType("nvarchar(max)")` unless the user wants the change.
- **Complex type column names**: duplicate property names across complex types get a numeric suffix, and nested complex properties use the full path (`Complex_Nested_Property`). Both generate rename migrations; pin the old names with `HasColumnName`.
- **`.Contains()` on a local collection becomes `IN (@p1, @p2, ...)`** instead of `OPENJSON`. Better plans for small lists, plan-cache churn and parameter limits for large ones. `UseParameterizedCollectionMode(ParameterTranslationMode.Parameter)` restores the old mode globally, `EF.Parameter(list)` per query.
- **`Application Name` is injected** into connection strings without one. EF and non-EF access (Dapper, ADO.NET) on the same string end up in different pools, `TransactionScope` can escalate to a distributed transaction, and the version string shows in `sys.dm_exec_sessions`. Set an explicit `Application Name`.
- **`ExecuteUpdateAsync` takes a plain lambda.** Hand-built expression trees for setters no longer compile; rewrite as a lambda with `if` blocks.
- **EF tools need `--framework`** on a multi-targeted project.
- Microsoft.Data.Sqlite reads and writes `DateTimeOffset` as UTC. Integration tests on SQLite can change results; `Microsoft.Data.Sqlite.Pre10TimeZoneHandling` is the temporary switch.

### Libraries, security, containers

- SYSLIB0058 (`SslStream` cipher properties → `NegotiatedCipherSuite`; keep any weak-cipher rejection), SYSLIB0060 (`Rfc2898DeriveBytes` constructors → `Rfc2898DeriveBytes.Pbkdf2`), SYSLIB0061, SYSLIB0062.
- `System.Linq.Async` clashes with the built-in `System.Linq.AsyncEnumerable`: remove the package, or set `ExcludeAssets="compile"` when it arrives transitively; `SelectAwait` becomes `Select`.
- `Uri` no longer rejects long strings. Code that relied on it as a length limit needs an explicit check.
- `XmlSerializer` serializes `[Obsolete]` properties. Add `[XmlIgnore]` to any that hold data that shouldn't leave.
- The runtime no longer handles SIGTERM for apps without the Generic Host (console apps in containers): register `PosixSignalRegistration` for graceful shutdown.
- **No Debian images.** `sdk:10.0`, `aspnet:10.0`, and `runtime:10.0` are Ubuntu 24.04 (`-noble`). Map `-bookworm-slim` and other Debian tags to the default or `-noble`, keep `-alpine` and `-chiseled` as they are, and check every `apt-get install` package name exists on Ubuntu 24.04. Chiseled images have no shell or package manager, so a `RUN` in the final stage fails.
- Renamed variables: `DOTNET_OPENSSL_VERSION_OVERRIDE`, `DOTNET_ICU_VERSION_OVERRIDE`; `NUGET_ENABLE_ENHANCED_HTTP_RETRY` is gone. OpenSSL 1.1.1 or later on Linux.

## net10.0 → net11.0

Collected from previews; confirm each on the GA page before acting on it.

- **An unhandled exception in `BackgroundService.ExecuteAsync` stops the host.** A worker that used to die quietly now takes the app down. Decide per service: catch, log, and keep looping, or let it stop the host on purpose.
- **`Microsoft.AspNetCore.OpenApi` moves to `Microsoft.OpenApi` 3.x.** Transformers break again; follow the library's v3 upgrade guide.
- **Microsoft.Data.SqlClient 7 moves Entra ID authentication** into `Microsoft.Data.SqlClient.Extensions.Azure`. A connection string with `Authentication=Active Directory ...` (managed identity on Azure SQL) fails at runtime until that package is added.
- `Microsoft.EntityFrameworkCore.Tools` no longer brings `.Design`: add it explicitly where migrations are created. `EFOptimizeContext` is replaced by `EFScaffoldModelStage` and `EFPrecompileQueriesStage`.
- SYSLIB0063 (`NamedPipeClientStream` constructor with `isConnected`).
- C# 15: span collection expressions get a narrower safe context; `with(...)` inside a collection expression is constructor arguments; `nameof(this.P)` in attributes is an error; `(X.Y) when` in a switch arm parses as a pattern.
- ZIP reads validate CRC32 and TAR reads validate checksums, so corrupt archives that used to read now throw.
- Server-side client-certificate validation stops downloading intermediates through AIA: install the full chain or have clients send it.
- Minimum hardware: x86-64-v2 on x64, LSE on Windows Arm64.

## Smoke checks for the report

List the ones that apply, with the result or "not checked":

- Startup: DI validation, hosted service order, config values that may now be `null`.
- Auth: API calls without a session get 401 and the frontend handles it; forwarded client IP and scheme behind the proxy.
- EF: `has-pending-model-changes` clean; queries with `.Contains()` on large lists; migrations apply in the deploy pipeline.
- OpenAPI: the document still generates and the generated client still compiles.
- Containers: the image builds and starts; graceful shutdown on SIGTERM.
- Security: weak-cipher checks kept after SYSLIB0058, obsolete sensitive properties excluded from serialization, explicit length checks where `Uri` was the limit, exception handlers still emit security telemetry, restore audit findings fixed rather than suppressed, forwarded-header lists not cleared.
