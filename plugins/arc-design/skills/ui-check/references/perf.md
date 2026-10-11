# Performance numbers

Read before reporting a timing, a Core Web Vital, or the effect of a fix, whether from `--perf`, `--compare`, `--click`, a DevTools trace, or field data.

## Thresholds

| Metric | Good | Poor |
| --- | --- | --- |
| LCP | ≤ 2.5s | > 4s |
| INP | ≤ 200ms | > 500ms |
| CLS | ≤ 0.1 | > 0.25 |

- Ratings apply to the 75th percentile of real visits (CrUX, Search Console, the project's RUM), per page, or per origin when that fallback is named. Anything between the two columns is "needs improvement".
- One lab run rates nothing. Report it as a lab value next to the threshold, never as "passes Core Web Vitals".

## Reporting a number

- Label every number lab or field. Lab means this machine, headless, with the number of loads. Field means p75, the source, and its period. Never set one lab value against a field p75 as if they were the same kind of sample.
- Every number carries its conditions: URL or build, width and device emulation, CPU and network throttling (ui-check applies none), cache state, and the interaction measured. A reload is not a cold cache (ui-check disables the cache for its timed loads). Keep phone and desktop numbers apart.
- With only source code and no runtime evidence, name the likely causes but don't claim a metric fails.
- After a fix, re-measure under the same conditions. A difference inside the run-to-run spread is noise (`--compare` takes the median of 3). Field numbers move only after new visits, and CrUX covers a rolling 28 days.
- Don't add up the savings of overlapping findings: render-blocking CSS and a late-discovered LCP image claim the same LCP milliseconds. Fix the larger one, re-measure, then estimate the next.
- Zero estimated savings doesn't prove a resource is harmless, and one load doesn't prove it unused. Check later interactions and routes before removing a script.

## INP

- TBT and long tasks come from the load. They predict input delay for clicks during load, but they are not INP. INP needs a real interaction: `--click`, or a trace recorded while clicking. `--eval` clicks (`el.click()`) are synthetic and produce no event timing.
- `--click --perf` reports a click of 200 to 500ms to the next paint as `inp` and one over 500ms as `inp-slow`. Both are lab values without CPU throttling: a phone is slower, so a pass here doesn't clear the field.
- An interaction's time splits into three phases. Fix the one that dominates; don't start with the handler by default:
  - Input delay, from the event to the handler start: the main thread was busy (hydration, a third-party script, a timer). Split, defer, or lazy-start that work.
  - Processing, the handler's run time: remove work, paint the pending state and then yield (`${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/baseline.md`, Motion), and move CPU-bound work to a Worker.
  - Presentation, from the handler's end to the next frame: style, layout, and paint of what changed. Update fewer nodes, batch DOM reads before writes (a read after a write forces layout), and put `content-visibility: auto` on long offscreen lists.
- Memoize only when a profile shows the repeated work it removes.
- A third-party widget started on the first interaction makes that interaction pay its startup cost. Paint feedback first, or start it on intent (hover, focus).

## Layout shift after an interaction

- Chrome treats shifts within 500ms of an input as expected and leaves them out of CLS. Later shifts count like a load shift. The usual cause is an async result, banner, or validation summary inserted above the viewport (`layout-shift-input`); fix it per `${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/baseline.md`, Layout stability.
