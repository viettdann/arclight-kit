# Canvas effects

A canvas effect is a shader, particle field, or WebGL/3D scene running behind or around the content. It is the most expensive thing a page can draw: a GPU loop every frame, on every device, for as long as the tab is open. These rules keep it from costing the reader text, battery, or a working link. Styles decide whether a page gets one (cinematic, premium); the contract below holds whenever it does.

Contents: when · layer · capability gate · poster · resolution · frame loop · pausing · density · quality · contrast · teardown · checks.

## When to use one

- First try a static image, a video loop with a poster, or CSS (gradient, `animation-timeline`, a blurred blob). Reach for a canvas only when the motion reacts to something the reader does (pointer, scroll, time of day) and that reaction is the point of the section.
- At most one canvas effect per page. Two GPU loops halve the frame budget on a phone, and two moving backgrounds compete for the one focal point a section has.
- The effect is decoration: the section reads, and every action works, with the canvas removed. Meaningful 3D content (a product configurator) gets a text equivalent and DOM controls, which is outside this file.

## Layer contract

```text
section (position: relative; isolation: isolate; overflow: hidden)
├─ poster: static image or CSS background, always present
├─ canvas wrapper [aria-hidden="true"] (position: absolute; inset: 0; z-index: 0; pointer-events: none)
└─ content (position: relative; z-index: 1)
```

- `isolation: isolate` on the section keeps the canvas's `z-index` and any `mix-blend-mode` inside it, so the effect never blends into or stacks over the header or the next section.
- The canvas is `aria-hidden="true"` and `pointer-events: none`. A pointer-reactive effect reads the pointer from a listener on the section (`pointermove`), not from a layer that captures events: an overlay that captures the pointer above links makes them unclickable, and the bug only shows on the links.
- Content sits above the canvas in the stacking order; keyboard focus rings and text selection work as if the canvas weren't there.

## Capability gate

Mount the effect only when every check passes, in a small module that loads before the effect's own code, so ineligible devices never download the shader or the 3D library.

- `prefers-reduced-motion: reduce` doesn't match. A moving background is exactly what this setting asks to stop.
- `prefers-reduced-transparency: reduce` and `forced-colors: active` don't match; under both, the reader asked for a plain, high-contrast surface.
- No low-power signal: `navigator.connection?.saveData` is not true. A constrained device (`navigator.deviceMemory < 4` or `navigator.hardwareConcurrency <= 2`, where reported) gets the poster or the lowest tier.
- A WebGL (or WebGPU) context can be created. A failed `getContext` falls back to the poster, never to a blank box.
- Pointer-reactive effects also require `(hover: hover) and (pointer: fine)`; on touch they have nothing to react to.

Mirror the same queries in CSS, so a preference changed after load, or an effect that throws during init, still hides the layer:

```css
@media (prefers-reduced-motion: reduce), (prefers-reduced-transparency: reduce), (forced-colors: active) {
  .canvas-layer { display: none; }
}
```

Listen for `change` on each media query and unmount when one flips; don't wait for a reload.

## Poster first

- The poster (an image or CSS background matching the effect's first frame) is in the server-rendered HTML and stays visible until the effect reports its first rendered frame, then crossfades out over 300–500ms. Removing it on mount shows a blank or black flash while shaders compile and textures upload.
- Warm shaders before the reveal (`renderer.compileAsync` in Three.js, or one hidden frame), so the first visible frames don't stall.
- Handle context loss: on `webglcontextlost` call `event.preventDefault()`, stop the loop, and show the poster again; on `webglcontextrestored` rebuild GPU resources and resume. Mobile browsers drop contexts under memory pressure and on tab switching; without the handlers the section goes blank for the rest of the visit.

## Resolution

- Cap the device pixel ratio: `Math.min(devicePixelRatio, 1.5)` for a full-screen background, 2 for a single object that the eye inspects (a product model). A full-screen canvas at DPR 3 renders 9x the pixels of DPR 1 for a blur the eye can't resolve, and fill rate is what runs out first on phones.
- Size the canvas from a `ResizeObserver` on the section, not from `window` resize. On touch browsers, ignore height-only changes (the URL bar collapsing) when the width is unchanged; resizing on each one reallocates buffers mid-scroll and stutters.

## Frame loop

- Clamp the frame delta: `dt = Math.min(now - last, 1000 / 30) / 1000`. After a long frame (a GC pause, a background tab) an unclamped `dt` teleports particles and overshoots springs.
- Reset the time base on resume (`last = performance.now()` when the loop restarts), so a paused effect continues from where it stopped instead of jumping by the length of the pause.
- Scroll-linked effects read the scroll position each frame and derive state from it; they don't integrate scroll deltas (scroll-story rules in `styles/cinematic.md`).
- Animate with damping that is independent of frame rate (`1 - Math.exp(-k * dt)`), so a 120Hz display and a 60Hz one land on the same motion.

## Pausing

- Stop `requestAnimationFrame` when `document.hidden` is true, and when an `IntersectionObserver` reports the section offscreen. A loop drawing into an offscreen canvas still burns the GPU and the battery.
- Unmount heavy GPU work (dispose the renderer, release textures) when the section is far from the viewport, roughly more than one viewport away; remount from the poster when it returns. Pausing keeps memory allocated; a page with a 3D hero and a long body should give that memory back.
- On pause, the canvas keeps its last frame (or the poster), never clears to black.

## Density by area

Particle and instance counts scale with the area being covered, not a fixed number tuned on the designer's monitor:

```js
const scale = Math.min(1.3, Math.max(0.5, Math.sqrt((width * height) / (1440 * 900))));
const count = Math.round(BASE_COUNT * scale);
```

A count tuned at 1440×900 then reads at the same density on a 390px phone (half the particles, not the same 2,000 crammed into a small box) and doesn't explode on a 4K screen. Recompute on width changes, not on every resize.

## Quality step-down

- Start from a tier chosen by device signals (DPR cap, particle scale, post-processing on or off), then measure. Step down only after sustained misses, for example 120 frames in a rolling window averaging over 22ms, measured after shader warm-up.
- Step down in order of cost per visual change: DPR first, then post-processing passes, then particle count, then geometry detail.
- Hysteresis: never step back up in the same visit, or only after a long stable interval (tens of seconds). A governor that switches tiers every few seconds makes the effect visibly flicker between resolutions, worse than either tier alone.

## Contrast

- Text over an effect is checked against the brightest frame the effect can produce, not the first frame: capture the peak (a flare, a particle cluster, the end of a scroll sequence) and run `./scripts/contrast.mjs` against that color, with any scrim stacked as in `materials.md` (Glass, Contrast).
- When the effect can pass behind body text at full brightness, add a scrim or move the text; dimming the effect in code drifts the next time someone tunes it.

## Teardown

On unmount (route change, offscreen unmount, capability change), once, with ownership tracked so nothing is disposed twice:

- Cancel the `requestAnimationFrame` handle and any timers.
- Disconnect `ResizeObserver` and `IntersectionObserver`; remove `visibilitychange`, pointer, scroll, media-query, and context-loss listeners.
- Dispose geometries, materials, textures, render targets, and the renderer (`renderer.dispose()`, plus `forceContextLoss()` when the canvas is removed). Browsers cap live WebGL contexts at roughly 8–16; a single-page app that remounts without disposing loses the oldest context and the effect goes blank after a few navigations.
- Revoke object URLs, and restore the poster.

## Checks

- [ ] A static image or CSS was tried first; one canvas effect at most on the page; the section works with the canvas removed.
- [ ] Section has `isolation: isolate`; canvas is `aria-hidden` and `pointer-events: none`, behind content; every link and button over it is clickable and focusable.
- [ ] Gate checks reduced motion, reduced transparency, forced colors, Save-Data or low-end hardware, and WebGL support in JS, mirrored in CSS, and reacts to preference changes; ineligible devices load no effect code.
- [ ] Poster in the HTML, kept until the first rendered frame; context loss shows the poster and restore resumes.
- [ ] DPR capped at 1.5 (full-screen) or 2 (single object); canvas sized from the section.
- [ ] `dt` clamped to 1/30s; time base reset on resume, no jump after a hidden tab.
- [ ] Loop stops when hidden or offscreen; GPU resources released when far away.
- [ ] Particle count scales with area, clamped 0.5–1.3 of the base.
- [ ] Quality steps down only after sustained misses, with hysteresis; no tier flicker.
- [ ] Text contrast passes against the brightest frame.
- [ ] Teardown cancels rAF, disconnects observers, removes listeners, and disposes every GPU resource once.
