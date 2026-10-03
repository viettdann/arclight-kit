---
name: api-contract
description: "Audit ASP.NET controllers, Minimal API endpoints, and DTOs against their TypeScript/JavaScript consumers (hand-written fetch/axios/HttpClient services or NSwag/OpenAPI clients) for contract drift in both directions: renamed or removed JSON keys, enum values, new required fields, status codes, type changes. Reads source, reports only. Use when checking for breaking API changes, FE/BE contract sync, or a DTO or controller change before merging, including after a refactor (\"check breaking change\", \"API có vỡ không\", \"FE BE còn khớp không\")."
license: "MIT (adapted from github/awesome-copilot, see LICENSE.txt)"
---

# API Contract

Cross-reference the C# API's actual contract (routes, DTOs, status codes) against its TypeScript/JavaScript consumers and report contract drift in both directions before it reaches production. This skill does not modify code.

## Scope

- **After a change** (default when the working tree or branch has changes): audit only the endpoints and DTOs the diff touches, plus every endpoint that uses a touched DTO. Get the diff with `git diff HEAD` for uncommitted work or `git diff <base>...HEAD` for a branch.
- **Whole surface**: when the user asks for a full audit or names no change.

## Process

1. **Find the JSON serialization rules.** Check `Program.cs` or `Startup.cs`:
   - ASP.NET Core with System.Text.Json uses camelCase property names by default. Names stay PascalCase only when `PropertyNamingPolicy = null` is set; Newtonsoft (`AddNewtonsoftJson`) follows its contract resolver.
   - An explicit `[JsonPropertyName("...")]` or `[JsonProperty("...")]` wins over the policy. Skip properties with `[JsonIgnore]`.
   - Request binding is case-insensitive by default, so casing alone rarely breaks a request; response casing always matters to a TypeScript client.
   - With `JsonStringEnumConverter` (global or on the type), enum member names are part of the contract; without it, numeric values are.

2. **Map the C# contract surface.** For each endpoint in scope:
   - **Route**: controller `[Route]` plus action `[HttpGet("...")]` etc., or Minimal API `app.MapGet("...")` including `MapGroup` prefixes. Normalize parameters (`{id:int}`, `{id:guid}` → `{id}`).
   - **Inputs**: `[FromBody]` DTO, `[FromQuery]` and `[FromRoute]` parameters with their names.
   - **Required request fields**: `[Required]`, `[BindRequired]`, the C# 11 `required` modifier, or a non-nullable value type (`int`, `Guid`, `bool`) with no default. Optional: nullable (`string?`, `int?`) or has a default initializer. Respect `#nullable enable`.
   - **Response DTO**: property names after step 1, types, nullability.
   - **Status codes**: `[ProducesResponseType]`, `TypedResults`/`Results` return types, and explicit `StatusCode(...)`, `NotFound()`, `Conflict()` paths.

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

5. **Client → backend drift**:
   - **Harmless dead field**: the client sends a property the backend ignores.
   - **Silent runtime bug** (high severity): the client reads a response property the backend no longer returns, so it becomes `undefined` at runtime while TypeScript still compiles.

## Report

1. **Scope audited**: controllers, endpoints, DTOs, and TS/JS files, plus the serialization rules found in step 1 and where they are set.
2. **Backend → client breaks**: grouped by endpoint. What changed, match method, impact on the client, severity (compile error vs. silent runtime failure).
3. **Client → backend drift**: dead fields separated from silent runtime bugs.
4. **No consumer found**: endpoints and DTOs that need manual confirmation.
5. **Match confidence**: counts of findings from generated clients, hand-written route matches, and unmatched endpoints.
