# Azure Functions: in-process to isolated worker

Facts checked on 2026-10-14 against the [migration guide](https://learn.microsoft.com/azure/azure-functions/migrate-dotnet-to-isolated-model) (page dated 2026-09-14) and the [isolated worker guide](https://learn.microsoft.com/azure/azure-functions/dotnet-isolated-process-guide). Re-fetch them when the target differs or a step fails.

## Detect

A project is in-process when any of these hold: it references `Microsoft.NET.Sdk.Functions`, uses `[FunctionName]`, has a `FunctionsStartup` class, or its app setting `FUNCTIONS_WORKER_RUNTIME` is `dotnet` (in `local.settings.json`, IaC, or the pipeline's app settings). `dotnet-isolated` and `Microsoft.Azure.Functions.Worker` mean it is already isolated.

The in-process model ends support on **2026-11-10** and supports only .NET 8 on host 4.x. Isolated supports .NET 8, 9, 10 and .NET Framework 4.8. Host 1.x to 3.x: upgrade the host first ([v3 to v4](https://learn.microsoft.com/azure/azure-functions/migrate-version-3-version-4)) as its own step. C# script (`.csx`) apps convert to a project first.

## Order

The model migration and the TFM change are separate stages. Migrate the model on the current TFM, get it building, tested and starting under `func start`, then change the TFM with the main skill. When the current TFM has no isolated path, change the TFM first and say why.

## Steps

1. Project SDK: `<Project Sdk="Azure.Functions.Sdk/1.0.0">` (or the version in `global.json` `msbuild-sdks`). Remove `Microsoft.NET.Sdk.Functions`, `Microsoft.Azure.Functions.Worker.Sdk`, `FunctionsEnableWorkerIndexing`, and `Microsoft.Azure.Functions.Extensions`. Keep `Microsoft.Azure.Functions.Worker` as an explicit reference. Minimum Worker versions listed by the guide: 2.50.0 for .NET 10, 2.0.0 for .NET 9, 1.16.0 for .NET 8 and Framework; take the latest stable.
2. Restore the Functions project directly, not only the solution: solution restore can skip the step that generates the host extensions project. Never edit `obj/azure_functions.g.csproj`.
3. Extensions: replace each `Microsoft.Azure.WebJobs.Extensions.*` with its `Microsoft.Azure.Functions.Worker.Extensions.*` (Timer, Storage.Blobs/Queues, Tables, ServiceBus, EventHubs, EventGrid, CosmosDB, DurableTask, SignalRService). Add only the extensions the app uses. A WebJobs package that is transitive or in the generated host project is not a defect. Moving the Service Bus extension from 4.x to 5.x changes the `host.json` schema of its section.
4. Startup: move every `FunctionsStartup.Configure` registration to `Program.cs`, keeping each service lifetime, options binding and initialization. Delete the old class and its assembly attribute.
5. Functions: `[FunctionName("X")]` becomes `[Function("X")]` with the exact same name, route and authorization level. Rewrite trigger, input and output bindings from each extension's isolated docs. `out` parameters, `IAsyncCollector<T>` and `IBinder` become return values or a multi-output type. Use `FunctionContext` where the code read invocation context.
6. Logging: `ILogger` method parameters become constructor-injected `ILogger<T>` or `context.GetLogger(...)`. Log filters in `host.json` apply to the host only; worker filters go in `Program.cs`. Set up one telemetry pipeline (`Microsoft.Azure.Functions.Worker.ApplicationInsights` or OpenTelemetry), not both.
7. HTTP: with ASP.NET Core integration, `ConfigureFunctionsWebApplication()`, `Microsoft.Azure.Functions.Worker.Extensions.Http.AspNetCore` and `<FrameworkReference Include="Microsoft.AspNetCore.App" />`; otherwise the built-in `HttpRequestData`/`HttpResponseData`. Don't add the HTTP extension to an app with no HTTP triggers.
8. Serialization: the default moves from Newtonsoft.Json to System.Text.Json, which ignores `[JsonProperty]` and Newtonsoft converters without an error. Compare JSON output (names, nulls, enums, dates) against fixtures from before the change; switch the attributes or configure the serializer. Never edit the expected fixtures to match.
9. Settings: `FUNCTIONS_WORKER_RUNTIME=dotnet-isolated` in `local.settings.json` `Values` and in every app settings source the repo holds (Bicep, Terraform, pipeline `appSettings`). Keep connection setting names and `host.json` unchanged. `local.settings.json` stays git-ignored and `<CopyToPublishDirectory>Never</CopyToPublishDirectory>`; `host.json` is copied to output.
10. After the later TFM change to a modern .NET: add `<Using Include="System.Threading.ExecutionContext" Alias="ExecutionContext" />`.

## Workspace checks

Run on every Functions project the inventory finds, migrated or not, and report each hit in the final report's **Functions model** line. Fix only what the upgrade touches or the user asks for.

| Check | Finding |
|---|---|
| `host.json` | Missing, invalid JSON, or `"version"` not `"2.0"` (the schema version, not the runtime) |
| `FUNCTIONS_EXTENSION_VERSION` in IaC or pipeline settings | `~2` or `~3` is unsupported; a pinned minor (`~4.x.y`) stops platform updates |
| `AzureWebJobsDashboard` | Deprecated since v2; remove |
| Identity-based connections (`<Name>__serviceUri`, `__accountName`, `__fullyQualifiedNamespace`) | A group missing its required keys, or the same connection set both as a secret string and as identity keys |
| `AzureWebJobsStorage` | Missing on a non-Flex plan, or `UseDevelopmentStorage=true` in production config |
| Durable Functions | Orchestration triggers with no `extensions.durableTask.hubName` in `host.json`: two apps on one storage account share the default task hub |
| `local.settings.json` | Tracked by git (secrets leak), or not excluded from publish |
| Retry | Event Hubs, Timer, Cosmos DB or Kafka triggers without `[FixedDelayRetry]`/`[ExponentialBackoffRetry]` drop a failed event; Service Bus and queue triggers retry through `maxDeliveryCount`/`maxDequeueCount` instead, so their handlers must be idempotent |
| `.Result` / `.Wait()` / `.GetAwaiter().GetResult()` in functions | Blocks a worker thread under load |
| `CancellationToken` | Long-running functions without one ignore host shutdown and scale-in |
| `new HttpClient()`, `new ServiceBusClient()`, `new BlobServiceClient()` inside a function body | Socket exhaustion; register once in `Program.cs` (`AddHttpClient`, `AddAzureClients`) |
| Worker and extension packages | Below the minimums in step 1, or a `Microsoft.Azure.WebJobs.*` package next to `Microsoft.Azure.Functions.Worker` |

## Done when

- Restore, build and the existing tests pass against the baseline.
- `func start` lists the same function names as before and logs no binding or listener error.
- JSON output matches the pre-migration fixtures.
- No app-level `Microsoft.Azure.WebJobs.*` or `Microsoft.Azure.Functions.Extensions` reference remains.
- Durable apps: an orchestration started before the change resumes after it (a new one doesn't prove that).

## For the user, outside the repo

- `FUNCTIONS_WORKER_RUNTIME=dotnet-isolated` on the live app. Switch through a staging slot where the plan has slots; changing it on a live app restarts it on the new model, and the old package fails to start.
- Linux Consumption (`Y1` on Linux) can't run .NET 10, and its hosting retires on 2028-09-30. The move is `az functionapp flex-migration list` / `start` to Flex Consumption ([guide](https://learn.microsoft.com/azure/azure-functions/migration/migrate-plan-consumption-to-flex)), after the app is isolated. Flex has no deployment slots, and its blob trigger works only through Event Grid.

Adapted from [Azure/azure-functions-skills](https://github.com/Azure/azure-functions-skills) (MIT, Copyright (c) Microsoft Corporation).
