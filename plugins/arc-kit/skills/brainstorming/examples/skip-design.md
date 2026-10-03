# Example: The user requests implementation immediately

> Fictional project: paths, symbols, and findings are illustrative.

User: “Add a rate limiter to the Hono API. Don't ask a bunch of questions, just do it.”

Inspect the actual project before choosing defaults: applicable AGENTS.md, middleware registration, deployment topology, installed packages, tests, and the trusted source of client identity. The request already authorizes implementation.

Assistant:

> Tôi sẽ dùng giới hạn 60 request/phút trên các route `/api/*`, trả `429` kèm `Retry-After`, và dùng nguồn client IP đã được middleware hiện tại xác thực. Tôi đang kiểm tra deployment để chọn nơi lưu counter.

If the repository confirms a single-process deployment, choose a bounded in-memory store and explain that scope. If topology is unverified, do not claim the absence of Redis proves single-node operation. Resolve it from deployment files, or ask the one missing consequential question while progressing independent work.

Present a concise file/change/check plan and implement without another approval gate. Run the project's relevant unit and integration checks. Do not install e2e tooling for this request.

## User steering

- “Go”: continue the plan already within scope; do not request another confirmation.
- “Use Postgres instead”: inspect the existing DB integration, update the storage and concurrency design, and continue within the revised scope. Clarify only unresolved operational choices.
- “Just write the code”: continue implementation using verified constraints and reasonable defaults.
- A question about design: answer it briefly, incorporate any correction, and continue unless the user asks to pause or switches to a design-only task.

Authorization persists across ordinary preference answers. A plan or user correction does not authorize unrelated earlier suggestions.
