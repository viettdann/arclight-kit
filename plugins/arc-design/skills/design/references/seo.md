# SEO and share metadata

What search engines, link previews, and AI search tools read before anyone sees the page. A wrong `noindex` or canonical drops a page from search silently: nothing on screen shows it, so check the built output, not the source.

Contents: One source · Title and description · Canonical and indexing · Share cards · Structured data · Crawlers · Checks

## One source

- One mechanism per page (the framework's metadata API, a head component, or hand-written `<head>`), with site defaults in the root layout and per-page overrides on top: two systems emit two titles or two canonicals and crawlers pick one at random.
- Follow the project's existing mechanism; fixing a tag is not a reason to add or swap an SEO library.
- Values are deterministic: no timestamps, random ids, or session data in title, description, canonical, or JSON-LD, or each crawl sees a different page. Escape user-generated strings before they reach `<head>`.
- Title, description, canonical, and `og:url` describe the same page; `og:url` equals the canonical exactly (scheme, host, trailing slash).

## Title and description

- Every page has a unique `<title>`, page first and brand last, in one pattern site-wide ("Invoices · Acme"); client-side routes update it (`${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/navigation.md`).
- Every page that can be searched or shared has a meta description: plain text saying what the page holds, unique per page, no markdown or keyword lists.
- About 60 characters for a title and 160 for a description are lint thresholds, not limits: results truncate by pixel width and may rewrite both from page content. A warning means re-read it, not cut it.

## Canonical and indexing

- Each indexable page has one absolute, self-referencing canonical; sort, filter, and tracking-parameter variants point to the clean URL.
- Each page of a paginated list canonicalizes to itself, not to page 1, or crawlers treat the later pages' items as duplicates.
- `noindex` only for pages that must not appear in search: signed-in or private pages, duplicates with no canonical alternative, staging and previews, and landing pages built only for an ad campaign or a time-bound offer. Everything else stays indexable.
- Staging and previews get `noindex` (meta or `X-Robots-Tag`) from the environment, never from a hand-edited tag: a staging `noindex` that ships to production is the costliest metadata bug.
- Don't also disallow a `noindex` page in robots.txt: a crawler that can't fetch it never sees the `noindex`, and the URL can still be listed from links.

## Share cards

- Shareable pages set `og:title`, `og:description`, `og:image` (with `og:image:alt`), `og:url`, and `og:type` (`website`, `article` for a post), plus `twitter:card` `summary_large_image`: X falls back to the og tags but shows a small card without it.
- `og:image` and `twitter:image` are absolute `https://` URLs: preview fetchers don't resolve a relative path. With a metadata API, set the base URL (`metadataBase` in Next.js) so relative paths come out absolute.
- Share image 1200×630, under 5 MB, key content away from the edges because some apps crop toward a square.
- Share metadata must be in the server HTML: preview fetchers don't run JS, so tags set only by client code never show.
- Verify the preview on a deployed public URL; fetchers can't reach localhost.

## Structured data

- JSON-LD only for content the page renders (the article, the product and its visible price, the breadcrumb on screen); never invent ratings, reviews, prices, or organization facts to win a rich result.
- One block per page, the most specific type that fits, valid JSON with `@context`: a parse error drops the whole block, and valid syntax still doesn't promise a rich result.

## Crawlers

- robots.txt controls crawling, not indexing: disallow private areas and endless parameter spaces, never the CSS, JS, or images the page needs to render, and list the sitemap's absolute URL.
- The sitemap lists only canonical, indexable URLs (no redirects, no `noindex`, no parameter variants), with `lastmod` changed only when the content changes; Google ignores `changefreq` and `priority`, so leave them out.
- AI crawlers come in two groups with separate user agents. Search and user-fetch agents (`OAI-SearchBot`, `ChatGPT-User`, `Claude-SearchBot`, `Claude-User`, `PerplexityBot`) decide whether the site appears in AI answers; training and AI-use agents (`GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`) decide whether content feeds models. Blocking a training agent doesn't hide the site from AI search; blocking a search agent does. Ask the owner which they want and confirm current names in each vendor's docs.
- `llms.txt` is an unadopted proposal: add it only when asked, never instead of crawlable HTML.

## Checks

- [ ] One metadata source per page; title, description, canonical, and `og:url` agree.
- [ ] `og:image`/`twitter:image` absolute, `twitter:card` is `summary_large_image`, share tags present in the server HTML.
- [ ] `noindex` only on pages from the list above, checked in the built output.
- [ ] JSON-LD parses and describes only rendered content.
- [ ] Sitemap holds canonical URLs only; robots.txt doesn't block render assets.
- [ ] ui-check leaves no `title`, `meta-duplicate`, `canonical`, `share-image`, `noindex`, `json-ld`, or `meta-js-only` finding unexplained.
