# Example: The user changes a design constraint

> Fictional project: paths, symbols, and findings are illustrative.

A rate-limiter design currently assumes one API process and an in-memory store.

User: “Actually, we will deploy multiple nodes. Use Postgres, which is already in the stack.”

Identify the affected decisions and verify the new facts:

> Nhiều node cần dùng chung counter. Tôi sẽ đổi phần storage sang Postgres, kiểm tra cách bảo đảm cập nhật atomic và cập nhật test cho các request đồng thời.

Inspect the actual database driver, schema conventions, and transaction behavior. An insert/count sequence alone does not establish an atomic global limit; verify serialization or another suitable concurrency mechanism before relying on it.

Revise the middleware and storage design together. Include request cost, cleanup, migration compatibility, and database failure behavior. If the failure policy is unresolved and materially changes availability or enforcement, ask that question; continue independent work while waiting.

User: “Fail open and log at error level.”

Apply that decision within the existing authorization. The user decided it, so it moves into the design and out of the plan's assumptions. Update the plan's affected files, including schema or migration files discovered from the project, middleware, registration, and concurrency and failure tests. Run required checks after implementation.

For a design-only conversation, present the coherent revised design and finish there. For an implementation request, proceed without another plan approval gate. The latest clear correction supersedes stale assumptions while preserving the original objective.
