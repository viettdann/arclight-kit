# Style: Cinematic

Immersive, paced pages where imagery, scale, and scroll tell a story. Reads as directed and crafted; fails when motion becomes the content (preloaders, scroll hijacking, every element animating in) and the page turns slow, hard to read, or nauseating.

**Fits:** "immersive", "cinematic", "Awwwards", "storytelling", "launch", "campaign", portfolios and studios, product launches, film, music, games, fashion. Also "dark tech" launch pages (Vercel, Raycast) as its dark mode. **Profile:** marketing. Not for tool screens or long-form reading.

## Decisions

- **Canvas:** deep or bright, picked from the brand and its imagery. Dark is common here but the design rule still holds: dark only when the brief asks for it or names a dark reference, built per `dark-mode.md`. In dark tech, one luminous accent works as the single light source (`materials.md`, Gradient and glow); that element is exempt from the marketing profile's glow tell, and nothing else glows.
- **Type:** display at viewport scale, `clamp(3.5rem, 10vw, 11rem)`, tracking -0.03 to -0.05em, line-height 0.9–1.0. Display may use one extra weight (300 or 700, from a variable font); body stays 400/600 at 17–18px. A display line still fits in 2–3 lines at 390px, and the marketing profile's hero rules hold: the CTA is visible in the first viewport.
- **Imagery:** full-bleed photo or video carries the mood, one subject per section. Video is muted, `playsinline`, with a poster that loads first, and pauses under `prefers-reduced-motion: reduce`.
- **Pacing:** a section is one beat. Alternate dense and quiet beats; a full-height section (`min-height: 100dvh`) only where its content fills it.
- **Texture and glass:** optional film grain, and glass for floating navigation and controls over imagery, both per `materials.md`.
- **Motion:** each section gets at most one choreographed movement; the rest of the page is still. Entrances 400–800ms with a long ease-out. The movement must serve the story (reveal, transform, sequence); the marketing profile's one-sentence reason still applies.

## Motion rules

- **Content first.** The page shell and the hero headline render on first paint, never hidden behind a script or a preloader. A loader is only for an asset the first view can't show without (a 3D model, a WebGL scene), and then the shell is visible with a progress indicator, not a blank screen.
- **Native scroll.** No scroll hijacking that snaps between sections or changes wheel distance. A smooth-scroll library (Lenis) only when the brief asks for it, off under reduced motion.
- **Pinned sections and horizontal journeys:** one or two per page, never two in a row, each pinned for at most about two viewports. Keyboard and anchor links still reach everything; phones and reduced motion get a plain stacked layout.
- **Parallax** moves imagery and decoration only, never text.
- **Split text:** split by word or by grapheme (`Intl.Segmenter`), so diacritics and emoji stay whole. The split spans are `aria-hidden="true"` and the full string sits beside them in a visually hidden span, so screen readers read the sentence, not letters.
- **Cursor effects** (custom cursor, magnetic buttons) only under `@media (hover: hover) and (pointer: fine)`. The custom cursor tracks the real hotspot, and the native cursor returns over text, inputs, and selection.
- **Cost:** animate only `transform` and `opacity` (ui-interaction `baseline.md`). Set `will-change` just before a heavy animation and remove it after; never leave it on many elements in the stylesheet.
- **Tools:** CSS scroll-driven animations (`animation-timeline: view()`) where support allows, otherwise the project's existing library (Motion, GSAP ScrollTrigger). Don't add a library for one reveal.
- **Reduced motion** (`prefers-reduced-motion: reduce`): no pinning, parallax, scroll-linked movement, or smooth scrolling; content appears in place, opacity fades allowed.

## Signature moves (examples)

These show the style's spirit; they are not a menu. Derive the surface's distinctive move from the product first, and use one of these only when it fits better. Never more than two per page.

- A viewport-scale headline that the hero image sits behind or cuts through, passing contrast at every crop.
- One pinned section where the product or image transforms as the reader scrolls: the story beat of the page.
- A full-bleed video or image band carrying a single line of type.
- Section changes by color or image cross-fade instead of borders.
- Dark tech: one light source behind the product, the rest of the page unlit.

## Avoid

Preloaders and intro animations on every visit; scroll hijacking; text parallax; custom cursors that hide the real one; every element staggering in; autoplaying sound; hover-only reveals with no touch path; glow on more than the one light source; mega-menus with image previews for a nav of five links.
