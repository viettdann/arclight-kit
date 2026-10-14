# API Contract

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.

Cross-reference the C# API's actual contract (routes, DTOs, status codes) against its TypeScript/JavaScript consumers and report contract drift in both directions before it reaches production. This skill does not modify code.

## Scope

- **After a change** (default when the working tree or branch has changes): audit only the endpoints and DTOs the diff touches, plus every endpoint that uses a touched DTO. Get the diff with `git diff HEAD` for uncommitted work or `git diff <base>...HEAD` for a branch.
- **Whole surface**: when the user asks for a full audit or names no change.

## Process

1. **Find the JSON serialization rules.** Check `Program.cs` or `Startup.cs`:
   - Controllers and Minimal APIs have separate option sets: `AddControllers().AddJsonOptions(...)` for controllers, `ConfigureHttpJsonOptions(...)` for Minimal APIs. A setting in one doesn't apply to the other, so resolve the rules per endpoint kind.
   - ASP.NET Core with System.Text.Json uses camelCase property names by default. Names stay PascalCase only when `PropertyNamingPolicy = null` is set; Newtonsoft (`AddNewtonsoftJson`) follows its contract resolver.
   - An explicit `[JsonPropertyName("...")]` or `[JsonProperty("...")]` wins over the policy. Skip properties with `[JsonIgnore]`; `[JsonIgnore(Condition = WhenWritingNull)]` makes only that property optional in the response.
   - Request binding is case-insensitive by default, so casing alone rarely breaks a request. `PropertyNameCaseInsensitive = false` makes it case-sensitive: then a casing difference in a request body is a break, and the field arrives as its default.
   - `DefaultIgnoreCondition = WhenWritingNull` (or `NullValueHandling.Ignore` in Newtonsoft) drops null properties from responses: the key is absent and the TypeScript value is `undefined`, not `null`. A client that checks `=== null` takes the wrong branch.
   - `RespectNullableAnnotations = true` (.NET 9+) rejects an explicit `null` for a non-nullable property with a 400, where it used to bind `null` silently.
   - `NumberHandling` without `AllowReadingFromString` rejects a number sent as a string (`"42"`), which form-style clients do.
   - With `JsonStringEnumConverter` (global or on the type), enum member names are part of the contract; without it, numeric values are.

2. **Map the C# contract surface.** For each endpoint in scope:
   - **Route and method**: controller `[Route]` plus action `[HttpGet("...")]` etc., or Minimal API `app.MapGet("...")` including `MapGroup` prefixes. Normalize parameters (`{id:int}`, `{id:guid}` → `{id}`). Keep the HTTP method with the route.
   - **Auth**: `[Authorize]` and `[AllowAnonymous]` on the action and controller, `RequireAuthorization()` and `AllowAnonymous()` on the endpoint or group, and a global fallback policy. With cookie auth, from ASP.NET Core 10 an unauthenticated call to an API endpoint (`[ApiController]`, a Minimal API that reads or writes JSON, `TypedResults`) gets 401 or 403 instead of a 302 to the login page.
   - **Inputs**: `[FromBody]` DTO, `[FromQuery]` and `[FromRoute]` parameters with their names.
   - **Required request fields**: `[Required]`, `[BindRequired]`, the C# 11 `required` modifier, or a non-nullable value type (`int`, `Guid`, `bool`) with no default. Optional: nullable (`string?`, `int?`) or has a default initializer.
   - **Nullable reference types change what is required.** With `<Nullable>enable</Nullable>` (project or `Directory.Build.props`) or `#nullable enable` in the file:
     - MVC treats every non-nullable reference property (`string Name`) as `[Required]` and returns 400 when it's missing or null, unless `SuppressImplicitRequiredAttributeForNonNullableReferenceTypes = true`.
     - Minimal API parameters follow the annotation: `string name` is required, `string? name` is optional.
     - `#nullable disable warnings` keeps the annotations, so the rules above still apply; only `#nullable disable` turns them off.
     - Enabling nullable on a project, or removing a `?` from a request property, is a new required field for every client that omits it.
   - **Minimal API validation**: from .NET 10, `builder.Services.AddValidation()` runs data annotations on Minimal API parameters. Adding it turns existing `[Required]`, `[Range]`, `[MaxLength]` attributes, which were ignored before, into new 400 responses.
   - **Response DTO**: property names after step 1, types, nullability.
   - **Status codes**: `[ProducesResponseType]`, `TypedResults`/`Results` return types, and explicit `StatusCode(...)`, `NotFound()`, `Conflict()` paths.
   - **Error shape**: ProblemDetails (`AddProblemDetails`, `Problem()`, `ValidationProblem()`, the automatic 400 from `[ApiController]`) or a custom error DTO, per endpoint.
   - **Pagination**: offset (`page`/`skip`/`take`) or cursor (`cursor`/`after`), and the response envelope fields.

3. **Find the consumer.** Label every finding with the method used:
   - **Generated client** (high confidence): NSwag or OpenAPI Generator output, matched by generated method or interface name. A generated client that disagrees with the backend means the client is stale: say "regenerate", not "edit by hand".
   - **Hand-written client** (medium confidence): `fetch`, `axios`, Angular `HttpClient`, `ky`, etc. Normalize URLs before matching: strip query strings, turn `${this.apiUrl}/users/${id}`, `baseUrl + '/users/' + userId`, and `:id` into `/users/{id}`, then match against the C# route regardless of variable names.
   - **No consumer located**: report it as such. Never pair by loosely similar class names, and never conclude an endpoint is unused from a failed static search.

4. **Backend → client breaks** (the client breaks):
   - A response property renamed or removed that a TS interface or client code still reads
   - A new required request field or parameter the client never sends
   - A string enum value renamed or removed that the client sends or switches on
   - A status code the client doesn't handle (the endpoint now returns 409, the error handler covers only 400 and 500)
   - A type or nullability change the client type assumes differently (`long` → `string`, non-nullable → nullable)
   - An HTTP method change (`GET` → `POST`, `PUT` → `PATCH`) the client still calls with the old method
   - A route moved from anonymous to authenticated that the client calls without a token (a public page, a pre-login call)
   - An error shape change (ProblemDetails ↔ custom DTO, `errors` dictionary ↔ list) the client's error handler parses the old way
   - Pagination switched from offset to cursor while the client still sends `page`/`skip` or reads a total count
   - A committed OpenAPI or NSwag file (`swagger.json`, `openapi.yaml`, `nswag.json` output) not regenerated after the change, so the next generated client bakes in the old contract
   - A changed document generator with no endpoint change: Swashbuckle → `AddOpenApi`, a `Microsoft.AspNetCore.OpenApi` major (OpenAPI 3.1 writes `type: ["string", "null"]` instead of `nullable: true`), or new schema or operation transformers. Operation ids, schema names, and nullability can all change, and the regenerated client's method names and types with them. Diff the old and new documents instead of reading the code
   - A cookie-authenticated frontend that detects an expired session by following the login redirect, now getting 401 from API endpoints (ASP.NET Core 10)
   - A null property now omitted (`WhenWritingNull` added) that the client compares with `null`, or a request now rejected because `RespectNullableAnnotations`, `PropertyNameCaseInsensitive = false`, strict `NumberHandling`, nullable reference types, or `AddValidation()` was turned on

5. **Client → backend drift**:
   - **Harmless dead field**: the client sends a property the backend ignores.
   - **Silent runtime bug** (high severity): the client reads a response property the backend no longer returns, so it becomes `undefined` at runtime while TypeScript still compiles.

## Report

1. **Scope audited**: controllers, endpoints, DTOs, and TS/JS files, plus the serialization rules found in step 1 and where they are set, per endpoint kind, and whether nullable reference types are on.
2. **Backend → client breaks**: grouped by endpoint. What changed, match method, impact on the client, severity (compile error vs. silent runtime failure).
3. **Client → backend drift**: dead fields separated from silent runtime bugs.
4. **No consumer found**: endpoints and DTOs that need manual confirmation.
5. **Match confidence**: counts of findings from generated clients, hand-written route matches, and unmatched endpoints.

Every finding names the C# file:line and the client file:line it rests on. When nothing breaks, say so in one line after the scope; don't fill the report with general API advice.