# Baseline (always applies)

## Semantics

- Interactive elements are real elements: `<button>` for actions, `<a href>` for navigation, native inputs for input. No `div` or `span` with a click handler acting as a button.
- Prefer native primitives when they fit: `<dialog>` with `showModal()`, `<details>`/`<summary>`, `popover` attribute, `<input type="date">` on mobile.
- An `aria-label` contains the visible text (WCAG 2.5.3), best at the start: a button showing "Send" is named "Send" or "Send message", never "Submit form", or a voice-control user who says "click Send" gets nothing.
- Each ARIA state has one job: `aria-pressed` for a toggle button (Bold, Mute), `aria-selected` for the chosen tab, option, or grid cell, `aria-current` for the current page, step, or date within a set, `aria-checked` for checkboxes, radios, and switches. Swapping them makes a screen reader announce a tab as "pressed" or a nav link as "selected", and the user can't tell what the control does.
- Never put `aria-hidden="true"` on an element that is or contains something focusable: the keyboard still lands on it and the screen reader announces nothing. Hide the subtree with `inert` instead, or keep it exposed.

## Keyboard and focus

- Never remove the outline without a replacement. Focus ring: 2px thick, 2px offset, at least 3:1 against the adjacent colors, visible in every theme. Use `:focus-visible` so mouse clicks don't show it.
- The focus ring color differs from the selected or active color, otherwise keyboard users can't tell "where I am" from "what is chosen".
- When several states apply at once, one wins the visual: loading over selected, selected over focus, focus over hover, so a hover tint never hides a selection and a busy row doesn't look clickable. The focus ring is the exception that always stays visible on top of the winner: an effect wrapper (glow, animated border, gradient frame) draws around the child without clipping or resetting its `outline`, and `overflow: hidden` on the wrapper doesn't cut the ring off.
- DOM order matches visual order. Don't reorder focusable content with CSS `order` or grid placement.
- Dialogs trap focus, close on Escape, and return focus to the element that opened them.
- Pages with navigation start with a skip link that is visible on focus.

## Pointer and touch

- Under `@media (pointer: coarse)`, primary controls have a 44×44px target; with a fine pointer every target is at least 24×24px (a dense tool's 28–36px controls meet this). Pad the hit area and keep the glyph at 16–20px.
- Hover styles live under `@media (hover: hover)`; enlarge controls under `@media (pointer: coarse)`. Never branch on user agent.
- Hover may reveal extras only. Every primary action is reachable by tap and keyboard without hover.

## Unavailable actions: explain, don't disable

*Disabled* means the native `disabled` attribute; *unavailable* means focusable with `aria-disabled="true"` and a stated reason.

A grey button that does nothing and says nothing is a dead end. `disabled` removes the control from the tab order, blocks the pointer events a tooltip needs, and gives no reason.

- Keep `disabled` for controls whose reason is obvious in context (Next on the last page, Bold with no text selected).
- Invalid input: keep submit enabled, validate on click, mark the fields, focus the first one (`forms.md`).
- Missing permission, a plan limit, or the wrong state: keep the control focusable with `aria-disabled="true"`, styled as unavailable, and on click, hover, or focus say why and what unlocks it ("Only admins can delete projects", "Export is on Pro"). `aria-disabled` blocks nothing by itself: the handler checks the state and shows the reason instead of acting, and a submit button stops the form too. If the user can never get the action, hide it.
- A tooltip that explains never sits on a `disabled` element, which fires no pointer events; put it on an `aria-disabled` control or a focusable wrapper.
- Busy is not disabled: an async button keeps focus and stays in the tab order with `aria-busy="true"`, ignores repeat clicks through state, names the progress ("Creating…"), then the result ("Project created"). Setting `disabled` mid-request drops focus to the body.
- Disabled controls are exempt from WCAG contrast, but one shown in order to explain must stay readable: its label at least 3:1.

## Color and text

- Contrast: 4.5:1 for body text, 3:1 for large text (24px, or 18.66px at weight 700; 600 doesn't count) and for UI boundaries, icons, and focus rings.
- Never carry meaning by color alone: pair it with an icon, text, or shape.
- Text survives 200% zoom or a larger root font size without clipping or overlap: containers that hold text size to their content (`min-height`, padding), never a fixed `height`, and type and spacing use `rem` rather than `px` where the project allows.
- Breakpoints are written in `em` or `rem` (`@media (min-width: 48em)`; Tailwind v4's defaults already are, v3's are px, so override `screens` in rem): an `em` media query follows the browser's default text size, so a user who sets 24px text gets the narrow layout that fits it, while a `px` breakpoint keeps the wide layout and squeezes the larger text into it.

## Announcements, images, and decoration

- A polite live region (`aria-live="polite"` or `role="status"`) is in the DOM, empty, from the first render, and the message is written into it later. A region inserted with its text already inside is often not announced at all, so a toast or "Saved" that mounts with its message stays silent.
- Alt text follows the image's job: informative, the information it carries ("Revenue up 12% in Q3", not "chart"); functional, inside a link or button, the action or destination ("Home", "Download invoice"); decorative, `alt=""` so it is skipped; complex (a chart, a diagram), a short alt plus the full data or description in nearby text or a table.
- Decorative layers (a glow, a gradient overlay, a canvas or video behind content) get `pointer-events: none` and `aria-hidden="true"`: without the first they swallow clicks meant for the controls beneath, without the second a canvas or video is announced as an unnamed element.
- Anything that moves, blinks, scrolls, or auto-updates for more than 5 seconds alongside other content (carousel, ticker, marquee, live feed, background video) has a visible pause or stop control (WCAG 2.2.2), or the user can't read the content before it changes.

## Layout stability

- Every `<img>`, `<video>`, and `<iframe>` reserves its box before it loads: `width` and `height` attributes, or `aspect-ratio` on the element or its wrapper. Content that arrives later (ads, embeds, banners) gets reserved space or appears below the viewport, never pushing visible content down.

## Mobile web and locale

- `touch-action: manipulation` on controls, so fast repeated taps don't zoom. Set `-webkit-tap-highlight-color` deliberately (usually `transparent`, with the control's own pressed state).
- Modals, drawers, sheets, and scrollable panels get `overscroll-behavior: contain`, so scrolling past their end doesn't scroll the page behind.
- `user-select: none` and `-webkit-touch-callout: none` go only on controls a long press shouldn't select (buttons, tabs, drag handles), never on `body` or content: there they stop users from copying text and break selection for assistive tools.
- Full-bleed layouts and fixed bars: `viewport-fit=cover` in the viewport meta, with padding from `env(safe-area-inset-*)` so content clears the notch and the home indicator.
- When the on-screen keyboard should shrink the layout rather than slide over it (a chat composer, a form with a fixed footer), add `interactive-widget=resizes-content` to the viewport meta (Chromium; iOS Safari ignores it), so `100dvh` and bottom-fixed bars sit above the keyboard instead of under it.
- `translate="no"` on brand names, code, identifiers, and usernames, so browser translation doesn't rewrite them.
- Dates, times, numbers, and currency go through `Intl.DateTimeFormat` and `Intl.NumberFormat` with the user's locale, never hand-built strings. Take the language from the user's setting or `navigator.languages`, never from IP.
- Text is translatable whole: plurals through `Intl.PluralRules` or the i18n library, never `item${n !== 1 ? 's' : ''}`; one message with placeholders, never a sentence glued from pieces (word order changes per language). Buttons and labels size to their text (`min-width` plus padding, never a fixed width): translations run about 40% longer.
- Never `transition: all`: list the properties, or a theme switch and every layout change animate too.
- Never block paste (`onPaste` with `preventDefault`), in password and confirmation fields included.

## Server side

Client-side checks exist for speed, not trust: the server re-runs validation and re-checks authorization for every action.

## Motion

- Honor `prefers-reduced-motion: reduce` for every animation and every transition that moves or scales (`transform`, `translate`, `scale`, position): replace the movement with an opacity change or nothing. Color and opacity transitions may stay.
- Press/tap feedback appears within 100ms, regardless of the network.
- Exits are faster than entrances, roughly 60–70% of the entrance duration.
- Animate `transform` and `opacity`, not `top`/`left`/`width`/`height`.
- Loops (spinners aside) pause when offscreen or when the tab is hidden. An animation interrupted midway (a second click, a reversed hover) continues from where it is, never jumps to the start; use View Transitions or FLIP when an element must visibly move between two layouts.
- No `scroll` event listeners and no scroll position, pointer position, or animation frames stored in React (or other framework) state: each frame re-renders the tree. Use `IntersectionObserver`, CSS scroll-driven animations, or the animation library's motion values (`useScroll`, `useMotionValue`, GSAP `ScrollTrigger`), and clean them up on unmount.
- Adding or changing an animation: whether it should move at all, durations per element, origins, and enter/exit mechanics are in `motion.md`.

## Platform CSS worth using

- `:has()` for state that already lives in the DOM (checked, open, invalid, child count) instead of mirroring it into JS state, e.g. `.plan:has(:checked)`, `form:has(:user-invalid)`, `.grid:has(> :nth-child(n + 5))`.
- `:user-invalid` instead of `:invalid`, so errors don't show on first render.
- `body:has(dialog[open]) { overflow: hidden; }` for scroll lock without cleanup code.
- Animate to `height: auto` with `grid-template-rows: 0fr → 1fr` (or `interpolate-size: allow-keywords` where supported).
- `z-index` only works on positioned elements or flex/grid children, and only ranks siblings inside one stacking context. Put `isolation: isolate` on components with internal layers; never escalate to 9999, find the stacking context instead.
- `animation-timeline: scroll()` / `view()` for scroll-linked effects, wrapped in `@supports` with a static fallback.

## Checks

- [ ] Every interactive element is focusable in a logical order and has a visible `:focus-visible` style.
- [ ] No clickable `div`/`span`.
- [ ] Every `aria-label` starts with the visible text, each ARIA state matches its role, and no `aria-hidden` subtree holds a focusable element.
- [ ] Focus rings survive effect wrappers; decorative layers are `pointer-events: none` and `aria-hidden`.
- [ ] Live regions exist empty before their first message; every image's alt matches its job; anything moving or updating past 5 seconds can be paused.
- [ ] No action depends on hover, right-click, or swipe alone.
- [ ] Every moving animation or transition has a `prefers-reduced-motion: reduce` override.
- [ ] No scroll listener or per-frame value held in component state.
- [ ] No state is conveyed by color alone.
- [ ] No fixed `height` on a container that holds text, breakpoints in `em`/`rem`; images, videos, and iframes reserve their size.
- [ ] Overlays contain overscroll, fixed bars clear the safe areas, dates and numbers go through `Intl`, no `transition: all`, and paste works in every field.
- [ ] No control is disabled without an obvious reason: unavailable actions explain themselves, busy buttons keep focus.
