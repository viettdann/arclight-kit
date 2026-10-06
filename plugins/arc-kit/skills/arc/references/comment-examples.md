# Comment examples

```
// BAD - narrates data flow + usage, wrapped to look tidy:
//   Shared transcript renderer: Block[] -> bundled subagents -> rail segments ->
//   components. Used by live session and read-only Task transcript.
// GOOD - only if a real invariant exists:
//   A thread with a parentThreadId never becomes a session.
// GOOD - a shortcut's ceiling:
//   Global lock; per-account locks if throughput matters.
// GOOD - usually no comment at all.
```
