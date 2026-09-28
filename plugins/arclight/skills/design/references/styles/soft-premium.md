# Style: Soft Premium

Calm, expensive-feeling surfaces: soft radii, diffused light, slow confident motion, lots of air. Reads as considered and physical; fails when every element gets the same treatment and the page becomes a template of rounded cards.

**Fits:** "premium", "luxury", "wellness", "Apple-like", "expensive", "soft", consumer hardware, beauty, hospitality, high-end consumer apps. **Profile:** marketing (and consumer-app onboarding). Not for dense tool screens.

## Decisions

- **Palette:** either airy (near-white or pale tinted canvas, soft grey text) or deep (near-black canvas, off-white text), picked from the brand, not from habit. One accent. Avoid the default premium clichés (cream + brass + espresso, black + purple orbs) unless the brand really is that; see the design rules on habitual choices.
- **Type:** a display sans with presence (or a refined serif if the brand is heritage), large and tightly tracked; body 17–18px with relaxed leading.
- **Radius:** soft, not large. The premium feel comes from light, space, and motion; radius only keeps edges from feeling sharp. Use the marketing profile's radius table with these overrides; every other row stays as the profile sets it:

  | Element | Override |
  |---|---|
  | Double-bezel shell (one or two per page) | 20–24px; core = shell − padding |
  | Full-width band or large panel | 20px |
  | Card, demo window, pricing tier, modal | 16px when the short side is over ~320px, otherwise the profile's 12px |
  | Primary CTA, floating nav | full pill |

  Secondary buttons, chips, tags, and badges keep the profile's radius; making them pills is a mistake, not a variant.
- **Depth:** very diffused shadows tinted toward the background hue (large blur, low opacity, small offset), plus a 1px highlight on the top edge for lifted objects. Depth marks what is important, so most surfaces stay flat.
- **Space:** section padding 96–160px on desktop; one idea per section.
- **Motion:** slow and weighted: entrances 400–700ms with a long ease-out (`cubic-bezier(0.32, 0.72, 0, 1)`), a single 16px fade-up per block, run once; press feedback `scale(0.98)`. Every animation still needs a reason (see the marketing profile).

## Signature moves (pick one or two)

- **Double bezel** for the hero media or one feature: an outer shell (subtle tinted background, hairline ring, 6–8px padding, shell radius from the table) holding an inner core (own background, inset top highlight, radius = outer − padding). Use it on one or two objects, not on every card.
- **Pill CTA with a nested icon:** the trailing arrow sits in its own small circle flush with the button's inner padding and shifts slightly on hover.
- **Floating pill navigation** detached from the top edge, blurred background (blur only on fixed or sticky elements).
- A macro product crop filling a section, with type set small beside it.

## Avoid

Blur on scrolling content (repaints kill mobile performance); animating every element on entry; glow orbs and mesh blobs behind text; the same double-bezel card repeated down the page; every button, chip, and tag as a pill, or every card at the outer-container radius, which reads as bubbly rather than premium; shadows on everything, which flattens the hierarchy the shadows were meant to create.
