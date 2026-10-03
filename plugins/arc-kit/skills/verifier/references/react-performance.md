# React performance review

Flag a rule only where the diff breaks it on a path that matters: a component that renders often, a long list, the first load, or a hot interaction. When the project enables React Compiler (`babel-plugin-react-compiler`, or `reactCompiler` in `next.config`), skip the memoization rules; the compiler memoizes. Rules marked (correctness) are defects, not cost: report them with category `correctness`.

## Waterfalls

- Independent `await`s in sequence → `Promise.all`, or start the promise early and await it where it is used.
- A child fetches in `useEffect` after its parent's fetch resolves → fetch both at the route level (loader, parallel queries).
- An `await` before a cheap synchronous check that can return early → check first.

## Bundle

- An import through an internal barrel (`index.ts` re-exporting a large folder) or a library root that doesn't tree-shake → import the module file directly. Vite's dev server loads every module a barrel re-exports; Next has `optimizePackageImports` for listed packages.
- A heavy component shown on demand (chart, rich editor, map, PDF viewer) in the main bundle → `React.lazy` with `Suspense`, or `next/dynamic`.
- `import()` with a template-literal path → explicit imports per branch; the bundler includes every file the pattern matches.
- A whole library for one function → the per-function import, or the native API.
- Analytics, chat, or support scripts loaded before the app is interactive → load after hydration (`defer`, `next/script` `lazyOnload`).

## Re-renders

- A store subscription to a whole object, or to a value used only inside a callback → a selector for the derived value (`s => s.cart.length > 0`); read with `getState()` inside the callback.
- A selector that returns a new object or array on every call → `useShallow` or separate selectors. (correctness when it loops)
- A context provider `value` built inline → memoize it, or split state and actions into two contexts.
- State derived in `useEffect` + `setState` → compute it during render.
- `useState(prop)` copying a prop that later changes → derive it during render, or reset the child with `key`. (correctness)
- An effect whose `setState` triggers another effect → compute the result in render, or in the handler that started the change.
- A parent's `onChange` called from an effect after local state changes → call it in the handler that sets the state. (correctness)
- `.sort()`, `.reverse()`, or `.splice()` on props or state mutates them in place → `toSorted()`, `toReversed()`, `toSpliced()`, or copy first. (correctness)
- `?? []`, `{}`, or an inline function passed to a memoized child or into effect deps → a module-level constant, primitive deps, or `useCallback`.
- A component defined inside another component → move it to module scope; it remounts and loses state on every render. (correctness)
- Logic that responds to a click placed in an effect watching a flag → run it in the handler.
- A value that changes on every mousemove or scroll kept in state while only handlers read it → `useRef`.
- An expensive update blocking typing → `startTransition` or `useDeferredValue`.
- `useState(expensive())` → `useState(() => expensive())`.
- `useMemo` or `useCallback` around a primitive or something no memoized consumer receives → remove.

## Rendering

- `{count && <X />}` with a numeric `count` renders `0` → `count > 0 ? <X /> : null`. (correctness)
- Index keys on a list that reorders, inserts, or deletes → stable ids. (correctness)
- Hundreds of rows rendered at once → virtualize (TanStack Virtual), or `content-visibility: auto` with `contain-intrinsic-size` on rows.
- Animating `width`, `height`, `top`, or `left`, or transforming an SVG element itself → `transform` and `opacity` on a wrapper.
- A `window` or `document` listener added per component instance → one shared listener; scroll and touch listeners `{ passive: true }`.

## Client data

- Shared data fetched with `useEffect` + `fetch` in several components when the project already has TanStack Query or SWR → use the query library.
- A fetch in an effect without an abort or ignore flag on cleanup → a fast parameter change lets the stale response win. (correctness)
- `localStorage` read on every render, or JSON stored without a version field → read once; store a version and discard old shapes.

## Next.js App Router

- Sequential `await`s across nested Server Components → `Promise.all`, or sibling `Suspense` boundaries that fetch in parallel.
- The same fetch in several Server Components for one request → `React.cache`.
- A large object passed to a Client Component → pass only the fields it renders; props are serialized into the HTML.
- `"use client"` high in the tree → push it down to the interactive leaves.
- Mutable module-level state in server code → it is shared across requests and users. (correctness)
- Non-critical work (logging, analytics) before the response → `after()`.
- A Server Action or route handler without an authentication and authorization check → report under security.
