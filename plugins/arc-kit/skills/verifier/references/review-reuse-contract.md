# Reuse and contracts review

Review each change for code that already exists and for consumers it breaks. Category `reuse` for items 1-4, `contract` for items 5-6.

1. **Search for existing utilities and helpers** that could replace newly written code. Start with the repo's shared locations (utils, lib, shared, and helpers directories, shared workspace packages) and the directory of each changed file, then widen to the whole repo.
2. **Flag any new function that duplicates existing functionality.** Put the existing function's path and name in `suggested_fix`.
3. **Flag inline logic that an existing utility already covers**: hand-rolled string manipulation, manual path handling, custom environment checks, ad-hoc type guards, and similar patterns.
4. **Flag new code that the platform already covers**: the standard library, a native platform feature (CSS over JS, a DB constraint over app code, a framework built-in), or a dependency already in the manifest. Flag a dependency the diff adds for what a few lines do. In UI, the project's own components outrank native elements. Put the replacement in `suggested_fix`.
5. **Contract breaks**: a changed exported signature, HTTP route, DTO or serialized field name, string enum value, ORM mapping, event name, or config key whose consumers the diff does not update. Search the whole repo for consumers, string-based lookups included; the build stays green when a serialized name changes. Fix: update the consumers, or restore the old name when the change was not planned.
6. **API contract skill**: when the diff touches ASP.NET controllers or DTOs with TypeScript or JavaScript consumers, also use the installed `mgi-kit:api-contract` skill when it is available (explicit invocation: `$api-contract`); otherwise list this check under `not_verified`.
