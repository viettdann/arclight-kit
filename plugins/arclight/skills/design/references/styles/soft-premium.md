# Style: Soft Premium

Calm, expensive-feeling surfaces: large soft radii, diffused light, slow confident motion, lots of air. Reads as considered and physical; fails when every element gets the same treatment and the page becomes a template of rounded cards.

**Fits:** "premium", "luxury", "wellness", "Apple-like", "expensive", "soft", consumer hardware, beauty, hospitality, high-end consumer apps. **Profile:** marketing (and consumer-app onboarding). Not for dense tool screens.

## Decisions

- **Palette:** either airy (near-white or pale tinted canvas, soft grey text) or deep (near-black canvas, off-white text), picked from the brand, not from habit. One accent. Avoid the default premium clichés (cream + brass + espresso, black + purple orbs) unless the brand really is that; see the design rules on habitual choices.
- **Type:** a display sans with presence (or a refined serif if the brand is heritage), large and tightly tracked; body 17–18px with relaxed leading.
- **Radius:** large and concentric: 20–32px on outer containers, inner radius = outer − padding; CTAs as full pills.
- **Depth:** very diffused shadows tinted toward the background hue (large blur, low opacity, small offset), plus a 1px highlight on the top edge for lifted objects. Depth marks what is important, so most surfaces stay flat.
- **Space:** section padding 96–160px on desktop; one idea per section.
- **Motion:** slow and weighted: entrances 400–700ms with a long ease-out (`cubic-bezier(0.32, 0.72, 0, 1)`), a single 16px fade-up per block, run once; press feedback `scale(0.98)`. Every animation still needs a reason (see the marketing profile).

## Signature moves (pick one or two)

- **Double bezel** for the hero media or one feature: an outer shell (subtle tinted background, hairline ring, 6–8px padding, large radius) holding an inner core (own background, inset top highlight, radius = outer − padding). Use it on one or two objects, not on every card.
- **Pill CTA with a nested icon:** the trailing arrow sits in its own small circle flush with the button's inner padding and shifts slightly on hover.
- **Floating pill navigation** detached from the top edge, blurred background (blur only on fixed or sticky elements).
- A macro product crop filling a section, with type set small beside it.

## Avoid

Blur on scrolling content (repaints kill mobile performance); animating every element on entry; glow orbs and mesh blobs behind text; the same double-bezel card repeated down the page; shadows on everything, which flattens the hierarchy the shadows were meant to create.
