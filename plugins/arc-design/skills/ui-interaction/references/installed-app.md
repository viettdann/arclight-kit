# Installed Web App (Home Screen, PWA)

Applies when the product ships a web app manifest or `apple-mobile-web-app-*` tags, or users add it to the Home Screen. Current iOS Safari opens any site added to the Home Screen as a web app by default, so a site that never opted in still runs without browser chrome and needs the Navigation rules below. Service workers, offline caching, and push are out of scope. Viewport, safe-area, and on-screen keyboard rules are in `baseline.md`.

## Head and icons

- `apple-touch-icon`: one 180×180 PNG, opaque, with square corners. iOS applies its own mask, so pre-rounded corners show a second curve inside the system one, and transparent pixels composite onto black.
- iOS reads PNG icons only: an SVG or WebP in the manifest or in `apple-touch-icon` is skipped.
- Manifest `icons`: PNG at 192×192 and 512×512 with `purpose: "any"`, plus a separate file with `purpose: "maskable"` whose mark sits inside the central safe zone (a circle about 80% of the width). Never `"any maskable"` on one file: the same art ends up either cropped as maskable or shrunk as any. iOS ignores maskable; Android uses it.
- Render every icon size from one vector mark at build time onto an opaque background, so the sizes can't drift apart.
- The home-screen label comes from manifest `short_name`, then `name`; `apple-mobile-web-app-title` only as a fallback for older iOS. Keep it to about 12 characters, or the system truncates it.
- iOS ignores manifest `background_color`, `orientation`, and `theme_color` for home-screen apps: set the page background and `<meta name="theme-color">` in the HTML (`${CLAUDE_PLUGIN_ROOT}/skills/design/references/dark-mode.md`).
- Icons, the manifest, and startup images are fetched without cookies. Serve them outside auth middleware: a redirect to sign-in or a 401 breaks them with no error anywhere, and iOS saves a screenshot of the page as the icon.
- iOS caches the icon per home-screen entry: a changed icon appears only after the user removes and re-adds the app, so test icon changes on a fresh install.

## Startup images

- On iOS, startup images show only when the rendered HTML has `<meta name="apple-mobile-web-app-capable" content="yes">`. The unprefixed `mobile-web-app-capable` that some frameworks emit instead doesn't count, so check the built HTML, not the source.
- One `<link rel="apple-touch-startup-image">` per device size, pixel ratio, and orientation, its media query matching `device-width`, `device-height` (CSS points, swapped for landscape), `-webkit-device-pixel-ratio`, and `orientation`; image pixels are points × ratio. A device with no matching entry gets a white launch screen, not the nearest image. Generate the images and the links from one device table so they can't disagree.
- The image's background matches the first-rendered `<body>` background and the mark sits centered, well inside the safe area. No text that changes or needs translation: iOS caches the image hard and keeps the light or dark variant it picked at install even after the system appearance changes.

## Navigation without browser chrome

- Standalone display (`display: standalone` and every iOS home-screen app) has no Back button, address bar, or reload. Every screen past the entry screen gets its own Back or close control: the iOS edge swipe goes back only once in-app history exists, and the user can't type a URL to get out of a dead end.
- Data that can go stale gets its own refresh (a button or automatic updates), since there is no browser reload; pull to refresh is never the only way (`gestures.md`).
- A link outside the manifest `scope` opens in an in-app browser that has its own Done control; don't add an app-level close on top of it. On iOS, links from Mail or Messages always open Safari, never the installed app, so a magic-link or OAuth return lands outside the app: prefer a code the user types into the app.
- Detect standalone with `matchMedia("(display-mode: standalone)")` (plus `navigator.standalone` for older iOS) and style it with `@media (display-mode: standalone)`, never from the viewport height or a guess about the address bar.
- Recent iPadOS opens home-screen apps in resizable windows whose system window controls cover the top-left corner, and `env(safe-area-inset-*)` doesn't report them: keep primary controls out of that corner when the window is smaller than the screen.

## Install prompt and hint

- Chromium fires `beforeinstallprompt`: call `preventDefault()`, keep the event, and show your own Install button that calls `prompt()` on click. iOS has no install API; there the most you can show is a hint pointing at Share, then Add to Home Screen.
- Show either only when all of these hold: the app isn't already running standalone, this is at least the second visit or the user just did something the product already counts as engagement, and the user hasn't dismissed it before. A prompt on first paint for everyone is a banner nobody asked for.
- Dismissal is permanent (persisted, not per session) and the hint has a visible close control.
- The iOS hint names Safari's menu, so show it only in iOS Safari: in-app browsers (Instagram, Facebook, Gmail) can't add to the Home Screen, and Chrome and Firefox on iOS reach it through different menus. This is the one allowed user-agent check, an exception to `baseline.md` (Pointer and touch), because the copy describes a browser's menu, which no feature test can detect; iPadOS reports a Mac user agent, so tell it apart with `navigator.maxTouchPoints > 1`.
- The copy states the benefit, then the steps, and on iOS avoids "install", since nothing gets installed: "Open it full screen from your Home Screen: tap Share, then Add to Home Screen", with the Share glyph drawn rather than described.

## Storage and relaunch

- On iOS the installed app has its own cookie and storage jar. Safari copies its cookies in once at install and nothing else, so `localStorage` and IndexedDB start empty and the two jars drift apart afterwards: don't assume a preference set in Safari exists in the app.
- iOS kills suspended standalone apps and may evict their storage. Restore recoverable UI state (route, scroll, drafts, filters) from persistent storage on launch, and keep anything irreplaceable on the server.

## Checks

- [ ] A 180×180 opaque PNG `apple-touch-icon`; manifest PNG icons at 192 and 512 with `purpose: "any"`, and maskable as a separate file.
- [ ] The manifest, icons, and startup images return 200 with an image or manifest content type when requested without cookies (`curl -sI <url>` with no cookie), not a redirect, 401, or HTML.
- [ ] Startup images exist only alongside `apple-mobile-web-app-capable` in the built HTML.
- [ ] In standalone, every screen past the entry screen has Back or close, and stale data has a refresh.
- [ ] Install button or hint: hidden in standalone, shown from the second visit or after engagement, dismissed for good; iOS copy only in iOS Safari.
- [ ] Recoverable state comes back after the app is killed and relaunched.
- [ ] `ui-check` reports no `install-asset`, `install-icon`, or `install-meta` finding.
