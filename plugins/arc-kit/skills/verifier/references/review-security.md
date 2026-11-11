# Security review

Read the changed code as an attacker who controls every input that crosses a trust boundary. Category `security` throughout. Report only a path from an input the attacker controls to the harm, and name both in `issue`.

## Guards are run, not read

An authentication, authorization, injection, or secrets guard the diff adds is verified by making it fire, the way `review-logic.md` in this directory describes: copy what it guards into a `mktemp -d` directory, break the copy the way the guard exists to catch, run the guard. A guard that passes its own violation is a high finding; put the command in `issue`. Never write inside the repository.

## Checks

1. **Injection**: untrusted input reaching SQL, shell commands, HTML, file paths, or outbound URLs without parameterization, encoding, or validation
2. **Access control**: a new endpoint or action without an authentication or authorization check, including access to another user's records; an unguessable ID (UUID) treated as authorization
3. **Secrets**: secrets in code, logs, or error messages; a secret, token, or signature compared with `==` instead of a constant-time compare; tokens, IDs, or nonces from `Math.random`, `System.Random`, or another non-CSPRNG source
4. **Webhooks**: an inbound webhook without signature verification, timestamp check against replay, or idempotency on the event ID
5. **Deserialization**: untrusted data passed to `pickle`, `yaml.load`, `BinaryFormatter`, Newtonsoft `TypeNameHandling` other than `None`, or similar type-resolving deserializers
6. **CI workflows**: `pull_request_target` or `workflow_run` that checks out or runs the untrusted head; `${{ }}` expressions holding event data (titles, branch names, bodies) interpolated into a `run:` script instead of passed through `env:`
7. **LLM output**: model output written to the database, rendered as HTML, used as a URL to fetch, or run as code or a query without validation
8. **Dependencies**: a dependency the diff adds whose exact package name does not exist in the registry, or that the ecosystem audit (`npm audit`, `dotnet list package --vulnerable`, `pip-audit`) reports as high or critical; a version ceiling or pin the diff writes that excludes the registry's current release with no reason stated in the diff or plan (check with `npm view <pkg> version`, `dotnet package search <pkg> --exact-match`, or `pip index versions <pkg>`; bounds written from memory go stale)
9. **Frontend sinks**: `dangerouslySetInnerHTML`, `innerHTML`, `v-html`, or Markdown rendered with raw HTML (`rehype-raw`) on data that isn't sanitized; an `href` or `src` built from user data without a scheme check (`javascript:`); auth tokens kept in `localStorage`; a `message` event handler that doesn't check `event.origin`; a redirect to a `returnTo` or `redirect` parameter without an allowlist
10. **React server code**: when the diff touches React server code, check the rule in `react-performance.md` that says to report under security
