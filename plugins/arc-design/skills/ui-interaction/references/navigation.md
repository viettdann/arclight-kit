# Tabs, Navigation, Scroll

## Tabs

- `tablist`/`tab`/`tabpanel` roles; arrows move between tabs, Home/End jump, Tab moves into the panel.
- The active indicator slides rather than jumping; panel switches don't shift the layout.
- Overflow scrolls horizontally with edge fades (plus chevrons on desktop), never wraps to a second row.
- On mobile use a segmented control for up to 4–5 options; beyond that, a scrolling row or a select/sheet.
- When tabs are views, the active tab is in the URL.

## Accordion

- The header is a `<button>` with `aria-expanded` and `aria-controls`, or use `<details>`/`<summary>`.
- One-open-at-a-time for sequential content, many-open for FAQs.
- Chevron rotation and panel height share one duration and easing.
- The tapped header stays anchored when a lower item expands.

## Navigation

- Mobile: bottom tabs for 3–5 primary destinations. Desktop: a persistent sidebar for 5+ sections, a top bar for fewer.
- A hamburger holds secondary items on mobile only, never desktop primary navigation.
- Breadcrumbs only for hierarchies deeper than two levels.
- The current location is marked with `aria-current="page"`.

## Scroll position in client-side routing

The browser restores scroll on Back for real page loads; a client-side router has to do it itself.

- A new navigation (link, push) starts at the top and moves focus to the new page's heading. Back and Forward restore the exact position the entry was left at.
- Prefer the router's built-in restoration (React Router `<ScrollRestoration>`, Vue Router `scrollBehavior`, the Next.js and SvelteKit defaults). Hand-rolled: `history.scrollRestoration = "manual"`, save the position on leave (the router's before-navigate hook, plus `pagehide`), and restore on return. Never on a scroll listener (`baseline.md`).
- Key saved positions by history entry (`history.state` key or `location.key`), not by path: the same URL can sit in history twice at different positions.
- Restore after the content has height: keep the list's data cached so it renders immediately on Back, or restore once it has rendered. Restoring before the data arrives lands at zero.
- An app shell that scrolls an inner pane instead of the window saves and restores that pane; the browser never does it for you.
- A route effect that calls `scrollTo(0, 0)` on every path change breaks Back; scroll to top only for new navigations.

## Sticky headers and anchors

- Offset every scroll target by the sticky header's height with CSS, not a number in code: `scroll-padding-top: var(--header-height)` on the scroller covers jump links, `scrollIntoView`, and keyboard focus (a focused control never hides under the header), and `scroll-margin-top` handles single targets.
- A hash link in a client-side route scrolls to the target after it renders and moves focus to it (`tabindex="-1"` on non-focusable targets). Smooth scroll only without `prefers-reduced-motion`.
- A feed with infinite scroll has no footer to reach; its footer links move to the sidebar or an about/settings page.

## Checks

- [ ] Back restores the exact scroll position (window or inner pane); new routes start at the top.
- [ ] Jump links and focused controls land below the sticky header.
- [ ] Trunk test: with only the navigation visible, a user can tell the site, the current page, the main sections, where they are among them, and how to search.
