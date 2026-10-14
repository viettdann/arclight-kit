# Queries and metrics

Every query runs as `az monitor log-analytics query --subscription S -w <workspace ID> --timespan P1D --analytics-query "..." -o table`, with S and the workspace ID from `find.py`. Widen `--timespan` (PT6H, P3D, P7D) to the incident window. An empty result is data: the table exists and nothing matched. "Failed to resolve table" means that source is not sent to this workspace; go back to what `find.py` listed.

Column aliases must not be KQL keywords: `first`, `last`, `count`, `max`, `min`, `sum`, `avg`, `type`, `kind`, `range` fail with "Query could not be parsed" (SYN0002). Use `lastSeen`, `firstSeen`, `n`, `msg`.

## Contents

- [Which table](#which-table)
- [App Insights (workspace-based)](#app-insights-workspace-based)
- [App Service and Functions diagnostic settings](#app-service-and-functions-diagnostic-settings)
- [Container Apps](#container-apps)
- [PostgreSQL flexible server](#postgresql-flexible-server)
- [Metrics](#metrics)
- [Resource Graph](#resource-graph)

## Which table

| Source (from `find.py`) | Tables |
|---|---|
| App Insights component | `AppRequests`, `AppExceptions`, `AppDependencies`, `AppTraces` in the component's workspace. Classic names (`requests`, `exceptions`) and `az monitor app-insights query` fail when the default az tenant differs; use the workspace. |
| Diagnostic setting on App Service or Functions ("resource-specific") | `AppServiceConsoleLogs`, `AppServiceHTTPLogs`, `AppServicePlatformLogs`, `AppServiceAppLogs`, `FunctionAppLogs` |
| Diagnostic setting on PostgreSQL ("AzureDiagnostics") | `AzureDiagnostics` filtered by `Category`; columns carry type suffixes (`errorLevel_s`, `Calls_d`) |
| Container Apps environment | `ContainerAppConsoleLogs_CL`, `ContainerAppSystemLogs_CL` (columns `ContainerAppName_s`, `Log_s`, `Reason_s`), or `ContainerAppConsoleLogs` / `ContainerAppSystemLogs` without suffixes in newer environments; try the `_CL` table first |

## App Insights (workspace-based)

Failing and slow operations:

```kusto
AppRequests
| summarize total=count(), failed=countif(Success == false), p95=percentile(DurationMs, 95) by AppRoleName, Name
| top 15 by failed
```

Exceptions grouped (`last` is a KQL keyword; don't use it as a column name):

```kusto
AppExceptions
| summarize n=count(), lastSeen=max(TimeGenerated), msg=take_any(InnermostMessage), outer=take_any(OuterMessage), type=take_any(ExceptionType) by AppRoleName, ProblemId
| top 15 by n
```

`InnermostMessage` carries the real cause where the outer one is generic (EF Core's "An error occurred while saving the entity changes" hides a SQL error such as 2601/2627 duplicate key). Which operations throw: `AppExceptions | summarize n=count() by OperationName, ExceptionType | top 10 by n`.

One exception with its stack and the request it broke: `AppExceptions | where ProblemId == "<id>" | take 1 | project TimeGenerated, OperationId, Details`, then `AppRequests | where OperationId == "<OperationId>"`.

Failed or slow dependencies (SQL, HTTP, Service Bus):

```kusto
AppDependencies
| where Success == false or DurationMs > 1000
| summarize n=count(), p95=percentile(DurationMs, 95) by AppRoleName, Type, Target, ResultCode
| top 15 by n
```

Error logs written through `ILogger`: `AppTraces | where SeverityLevel >= 3 | project TimeGenerated, AppRoleName, Message | order by TimeGenerated desc | take 50`.

Which tables still receive data, to find telemetry that stopped (a broken connection string, a sampling change) before trusting an empty result:

```kusto
union withsource=TableName AppRequests, AppExceptions, AppTraces, AppDependencies
| where TimeGenerated > ago(7d)
| summarize n=count(), lastSeen=max(TimeGenerated) by TableName, AppRoleName
```

Request rate over time, to see when it started: `AppRequests | summarize total=count(), failed=countif(Success == false) by bin(TimeGenerated, 15m) | order by TimeGenerated asc`.

## App Service and Functions diagnostic settings

Container stdout (what the app logged), filtered:

```kusto
AppServiceConsoleLogs
| where ResultDescription has_any ("fail", "error", "exception", "unhandled", "fatal")
| project TimeGenerated, app=tostring(split(_ResourceId, "/")[-1]), ResultDescription
| order by TimeGenerated desc | take 100
```

5xx by path: `AppServiceHTTPLogs | where ScStatus >= 500 | summarize n=count() by app=tostring(split(_ResourceId, "/")[-1]), CsUriStem, ScStatus | top 20 by n`.

Container lifecycle (start, stop, pull, crash): `AppServicePlatformLogs | project TimeGenerated, Level, Message | order by TimeGenerated desc | take 50`.

Functions:

```kusto
FunctionAppLogs
| where Level in ("Error", "Warning")
| summarize n=count(), msg=take_any(Message) by AppName, FunctionName, Level, ExceptionType
| top 20 by n
```

## Container Apps

```kusto
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == "<app>"
| project TimeGenerated, RevisionName_s, Log_s
| order by TimeGenerated desc | take 100
```

```kusto
ContainerAppSystemLogs_CL
| where ContainerAppName_s == "<app>" and Type_s != "Normal"
| project TimeGenerated, RevisionName_s, Reason_s, Log_s
| order by TimeGenerated desc | take 50
```

Rollout timeline, to tell a deploy's churn from a failure (use the suffix-less table and columns in newer environments):

```kusto
ContainerAppSystemLogs_CL
| where ContainerAppName_s == "<app>"
| summarize n=count() by bin(TimeGenerated, 30m), Reason_s
| where Reason_s in ("RevisionCreation", "RevisionDeactivating", "RollingRevisionCompleted") or n > 0 and Reason_s !in ("SyncingSecretFromAzureKeyVaultForContainerAppSucceeded", "SyncingSecretFromAzureKeyVaultForContainerAppJobSucceeded")
| order by TimeGenerated asc
```

## PostgreSQL flexible server

Errors by SQLSTATE:

```kusto
AzureDiagnostics
| where Category == "PostgreSQLLogs" and errorLevel_s in ("ERROR", "FATAL", "PANIC")
| summarize n=count(), lastSeen=max(TimeGenerated), msg=take_any(Message) by LogicalServerName_s, errorLevel_s, sqlerrcode_s
| top 20 by n
```

Heaviest queries (Query Store must be on, `pg_qs.query_capture_mode` not `none`):

```kusto
AzureDiagnostics
| where Category == "PostgreSQLFlexQueryStoreRuntime" and Is_system_query_b == false
| summarize calls=sum(Calls_d), total_ms=sum(Total_time_d), max_ms=max(Max_time_d) by Queryid_str_s
| top 10 by total_ms
```

The log has no query text. With database access: `SELECT query_sql_text FROM query_store.qs_view WHERE query_id = <Queryid> LIMIT 1;` in the `azure_sys` database.

Sessions by state per hour (pool leaks show as `idle` growing, lock waits as `Lock` wait events):

```kusto
AzureDiagnostics
| where Category == "PostgreSQLFlexSessions"
| summarize sessions=dcount(Pid_d) by bin(TimeGenerated, 1h), State_s, Wait_event_type_s
| order by TimeGenerated asc
```

## Metrics

`az monitor metrics list --subscription S --resource <id> --metric NAME1 NAME2 --offset 1d --interval PT15M --aggregation Average Maximum -o table`. Names are separate arguments; one quoted string of several names is rejected. `--start-time`/`--end-time` (UTC ISO) for a past window.

| Resource | Metrics |
|---|---|
| App Service plan | `CpuPercentage MemoryPercentage HttpQueueLength` (the plan's, shared by every app on it) |
| App Service app / Function app | `Http5xx Requests HttpResponseTime MemoryWorkingSet HealthCheckStatus InstanceCount` |
| Function app on Flex Consumption | `OnDemandFunctionExecutionCount OnDemandFunctionExecutionUnits AlwaysReadyFunctionExecutionCount AlwaysReadyUnits InstanceCount` |
| Container app | `Requests RestartCount Replicas CpuPercentage MemoryPercentage ResponseTime` |
| PostgreSQL flexible | `cpu_percent memory_percent cpu_credits_remaining active_connections max_connections connections_failed storage_percent deadlocks longest_query_time_sec` |
| Service Bus namespace | `IncomingMessages CompleteMessage ServerErrors UserErrors ThrottledRequests` (counts: `Total`); `ActiveMessages DeadletteredMessages` are gauges: use `Maximum`, since `Total` adds one sample per minute (27 dead letters read as 38,880 a day) |

Failed or server-error counts in `AppRequests` include 4xx; split by `ResultCode` first: `AppRequests | where Success == false | summarize n=count() by ResultCode, Name | top 15 by n`.

Cost Management query limits (what `audit.py` COST works within): `Daily` granularity covers at most 31 days and silently truncates the start beyond that; `Monthly` and `None` 12 months; 37 months is a hard 400. Future dates are shifted without an error. At most 2 `grouping` dimensions; grouping by `ResourceId` works only at subscription or resource-group scope. Throttling allows a few queries a minute per scope.

Settings that explain a metric: `az postgres flexible-server parameter show --subscription S -g RG -s SERVER --name max_connections --query value`; Service Bus backlog: `az servicebus queue list --subscription S -g RG --namespace-name NS --query "[].{q:name,active:countDetails.activeMessageCount,dead:countDetails.deadLetterMessageCount}" -o table` (topics: `az servicebus topic subscription list ... --topic-name T`).

## Resource Graph

Run through `find.py`/`audit.py`, or `POST /providers/Microsoft.ResourceGraph/resources` with the tenant's token ([pitfalls.md](pitfalls.md)); `az graph query` uses only the default tenant.

Resources whose Resource Health isn't `Available` (the table holds only resources with a health signal; `Unknown` means no signal):

```kusto
healthresources
| where type =~ 'microsoft.resourcehealth/availabilitystatuses' and properties.availabilityState != 'Available'
| project id, state=tostring(properties.availabilityState), reason=tostring(properties.reasonType), summary=tostring(properties.summary), since=tostring(properties.occuredTime)
```

Active Azure incidents. `HealthAdvisory` and `PlannedMaintenance` events are usually active too and rarely explain a failure; filter to `ServiceIssue`:

```kusto
servicehealthresources
| where type =~ 'microsoft.resourcehealth/events' and properties.Status == 'Active' and properties.EventType == 'ServiceIssue'
| project trackingId=name, title=tostring(properties.Title), impact=properties.Impact
```

Resources stuck after a failed deploy: `resources | where tostring(properties.provisioningState) !in ('Succeeded', '') | project name, type, resourceGroup, state=tostring(properties.provisioningState)`.
