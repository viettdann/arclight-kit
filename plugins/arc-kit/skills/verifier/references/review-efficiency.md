# Efficiency review

Review the changes for efficiency. Category `efficiency` throughout.

1. **Unnecessary work**: redundant computation, repeated file reads, duplicate network or API calls, N+1 patterns
2. **Missed concurrency**: independent operations run sequentially when they could run in parallel
3. **Hot-path bloat**: new blocking work added to startup or to per-request and per-render hot paths
4. **Unnecessary existence checks**: pre-checking that a file or resource exists before operating on it (TOCTOU anti-pattern). Operate directly and handle the error.
5. **Memory**: unbounded data structures, missing cleanup, event listener leaks
6. **Overly broad operations**: reading whole files when a portion suffices, loading every item to filter for one
7. **React**: when the diff touches React components, hooks, or stores, also check it against `react-performance.md`, in the same directory as this checklist; skip the rules marked (correctness), which the correctness reviewer covers
