# Avatars

An avatar identifies a person at a glance, so the same person must look the same on every screen and in every failure mode.

## Degrade, don't break

- Fallback chain: the image, then initials from the name, then a generic person icon as the last resort. Never a broken-image square or an empty circle.
- Render the initials underneath and the image on top; on the image's `error` event, remove the image. The box has a fixed size, so nothing shifts when the image loads or fails.
- `alt=""` when the name is shown next to the avatar; otherwise `alt` is the name.

## Initials

- Two letters by default (first letter of the first and last word), which reads as a person; one letter only at the smallest size.
- Split by grapheme (`Intl.Segmenter`), not by string index, so accented and non-Latin names keep whole characters ("Đặng Lê" → "ĐL"). An email falls back to its local part; a single-word name gives one or two letters of that word.
- Initials are uppercase, weight 600, about 40% of the avatar size.

## One person, one color

- The fallback color comes from a hash of a stable key (user id; the name only if there is no id) mapped onto a fixed palette, via one shared function. Never random, and never the index in the current list, or the same person changes color between the chat header, a comment, and the member list.
- The palette has 6–8 hues at the same OKLCH lightness and chroma, so no one stands out, and every hue passes 4.5:1 with its initials. Leave out the accent and the status hues.
- In the tool profile the palette is quiet: a low-chroma tint of the hue with initials in a darker step of the same hue, not saturated fills.

## Sizes

- Three size tokens and nothing between, for example 24px in lists and rows, 32px in headers and comments, 40px on profile and detail views. A marketing page may add one display size for testimonials.
- People are round (`full` in `radius.md`); organizations, workspaces, and bots are rounded squares (`md`), so a person and a thing never look alike.

## Groups

- Overlap by about a quarter of the size (`-space-x-2` at 32px), each avatar with a 2px ring in the surface color so the edges stay readable.
- Show 3–5 and cap the rest as a "+N" chip of the same size and shape, which opens or tooltips the full list. The group has one accessible label ("7 collaborators: Sarah Chen, …").
- Order by relevance (owner, currently active), not alphabetically.

## Presence

- Presence lives on the avatar's ring (online, away), separated from the avatar by a gap in the surface color. One signal: never a ring plus a dot plus an "Online" pill.
- Offline shows no ring: the absence is the signal, and a grey ring reads as a border.
- Color isn't the only carrier: the status is in the avatar's accessible label and tooltip ("Sarah Chen, away").

## Checks

- [ ] A failed image falls back to initials, then an icon; no broken square, no layout shift.
- [ ] Fallback colors come from one hash of a stable id; the same person has the same color everywhere.
- [ ] Three avatar sizes; people round, organizations square.
- [ ] Groups overlap with a surface ring and cap with "+N".
- [ ] Presence is one ring with a text alternative; offline has none.
