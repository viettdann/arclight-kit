# az CLI and access pitfalls

Each of these cost a wrong turn in a real investigation. Read the one that matches an error before retrying.

| Symptom | Cause | Do instead |
|---|---|---|
| `az graph query --subscriptions <ids>` fails with `NoValidSubscriptionsInQueryRequest ... Given: ''` | It takes the default tenant's token, so subscriptions in another tenant are dropped | `find.py` / `audit.py`, or `POST /providers/Microsoft.ResourceGraph/resources?api-version=2022-10-01` with `az account get-access-token --tenant T` |
| `SubscriptionsContainInvalidGuids ... Given: 'id1 id2 '`, or `= not found` from `[ a == b ]` | The shell is zsh: an unquoted `$VAR` holding a list arrives as one argument, and `==` inside `[ ]` is an error | Pass the IDs as separate words, or wrap the snippet in `bash -c '...'` |
| `AuthorizationFailed ... or the scope is invalid` on one resource | Usually the resource sits in another subscription than the one passed, not missing RBAC | Take the subscription from `find.py`, retry, and only then report a missing role |
| `az keyvault secret list` → `ForbiddenByRbac` (`secrets/readMetadata/action`) | Reader has no data-plane access; secret names aren't readable | Secret names and vault URLs from `az containerapp show --query properties.configuration.secrets` (no values), or the Container Apps system log, whose `Log_s` names vault, secret and identity |
| Key Vault reference failures in the system log all say "Ensure the managed identity has the correct access..." | The sentence is boilerplate | Read the end of the line: `context canceled` is a timeout (transient, often during a rollout), `403` is access |
| `Invalid jmespath query ... keys(): invalid type ... null` | A JMESPath function hit a field that is null on this resource (`identity.userAssignedIdentities` with no identity) | `-o json`, then parse with `python3 -I` |
| `az webapp show --query appServicePlanId` returns null | The field is `serverFarmId` | `--query serverFarmId` |
| `az monitor log-analytics query` says only `BadArgumentError: The request had some invalid properties` | The real reason (`SYN0002` parse error, `Failed to resolve table`) is in `Inner error` further down | Read the whole error; don't cut it with `tail` |
| A metric name is rejected | Names differ per resource type and SKU | `az monitor metrics list-definitions --subscription S --resource ID --query "[].name.value" -o tsv`; the rejection also lists the valid names |

## Signals that look like incidents but aren't

- **Container App `ScaledToZero`, 0 replicas, Healthy**: the app scales to zero when idle. Not down.
- **5xx in exact multiples of 3**: one client retrying each call twice; count distinct operations, not responses.
- **500s on one path and method from one or two clients**, such as `POST /index.html` against an ASP.NET SPA fallback that only serves GET: a scanner or a stale form. Group by `Name`, method, `UserId`, `SessionId` and `AppRoleInstance` before ranking it.
- **A `failed` count in App Insights**: `Success == false` includes 4xx (a logout endpoint answering 401 in a loop). Split by `ResultCode` before calling it a server error.
- **Exceptions outnumbering failed requests**: one request can log several exceptions, and handled ones behind a 401 count too. Join `AppExceptions` to `AppRequests` on `OperationId` before saying "N errors".
