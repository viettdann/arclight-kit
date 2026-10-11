import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_tells.py")


class ScanTellsTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def tells(self, name, content):
        path = os.path.join(self.root, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        r = subprocess.run([sys.executable, SCRIPT, path, "--json"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return [h["tell"] for hs in json.loads(r.stdout).values() for h in hs]

    def assertTell(self, name, content, prefix):
        self.assertTrue(any(prefix in t for t in self.tells(name, content)), f"expected '{prefix}' in {content!r}")

    def assertNoTell(self, name, content, prefix):
        self.assertEqual([t for t in self.tells(name, content) if prefix in t], [], f"unexpected '{prefix}' in {content!r}")

    def test_side_border_tailwind(self):
        self.assertTell("a.tsx", '<div className="border-l-4 border-blue-500 p-4">x</div>\n', "colored side border")
        self.assertNoTell("a.tsx", '<div className="border-l-4 border-zinc-200 p-4">x</div>\n', "colored side border")
        self.assertNoTell("a.tsx", '<div className="border-l-2 border-accent/20 pl-4">x</div>\n', "colored side border")

    def test_side_border_current_item_is_kept(self):
        self.assertNoTell("a.tsx", '<a aria-current="page" className="border-l-2 border-blue-500">Home</a>\n', "colored side border")

    def test_side_border_css(self):
        self.assertTell("a.css", ".card {\n  border-left: 4px solid #2563eb;\n}\n", "colored side border")
        self.assertNoTell("a.css", ".card {\n  border-left: 4px solid #e5e7eb;\n}\n", "colored side border")
        self.assertNoTell("a.css", "blockquote {\n  border-left: 4px solid #2563eb;\n}\n", "colored side border")

    def test_overshoot_easing(self):
        self.assertTell("a.css", ".a { transition-timing-function: cubic-bezier(0.34, 1.56, 0.64, 1); }\n", "overshoot easing")
        self.assertTell("a.tsx", '<div className="ease-[cubic-bezier(0.6,-0.28,0.74,0.05)]" />\n', "overshoot easing")
        self.assertNoTell("a.css", ":root { --ease-enter: cubic-bezier(0.16, 1, 0.3, 1); }\n", "overshoot easing")

    def test_transition_all(self):
        self.assertTell("a.tsx", '<button className="transition-all duration-200">x</button>\n', "transition: all")
        self.assertTell("a.css", ".a { transition: all 200ms; }\n", "transition: all")
        self.assertNoTell("a.css", ".a { transition: opacity 200ms, transform 200ms; }\n", "transition: all")

    def test_layout_transition(self):
        self.assertTell("a.css", ".a { transition: height 300ms ease; }\n", "layout property")
        self.assertTell("a.tsx", '<div className="transition-[width] duration-200" />\n', "layout property")
        self.assertNoTell("a.css", ".a { transition: background-color 150ms, border-color 150ms; }\n", "layout property")

    def test_tight_tracking(self):
        self.assertTell("a.tsx", '<h1 className="tracking-[-0.05em]">x</h1>\n', "tracking tighter")
        self.assertTell("a.css", "h1 { letter-spacing: -0.06em; }\n", "tracking tighter")
        self.assertTell("a.tsx", '<h1 className="tracking-tighter">x</h1>\n', "tracking tighter")
        self.assertNoTell("a.css", "h1 { letter-spacing: -0.04em; }\n", "tracking tighter")
        self.assertNoTell("a.tsx", '<h1 className="tracking-[-0.02em]">x</h1>\n', "tracking tighter")

    def test_hairline_with_large_shadow(self):
        self.assertTell("a.tsx", '<div className="rounded-xl border shadow-2xl">x</div>\n', "hairline border plus")
        self.assertTell("a.css", ".card {\n  border: 1px solid #e5e5e5;\n  box-shadow: 0 20px 40px rgba(0,0,0,.1);\n}\n", "hairline border plus")
        self.assertNoTell("a.tsx", '<div className="rounded-xl border shadow-sm">x</div>\n', "hairline border plus")
        self.assertNoTell("a.tsx", '<div role="dialog" className="fixed inset-0 rounded-xl border shadow-2xl">x</div>\n', "hairline border plus")
        self.assertNoTell("a.css", ".card {\n  border: none;\n  box-shadow: 0 20px 40px rgba(0,0,0,.1);\n}\n", "hairline border plus")

    def test_justify(self):
        self.assertTell("a.tsx", '<p className="text-justify">x</p>\n', "justified text")
        self.assertTell("a.css", "p { text-align: justify; }\n", "justified text")
        self.assertNoTell("a.tsx", '<div className="flex justify-between">x</div>\n', "justified text")

    def test_outline_without_focus_visible(self):
        self.assertTell("a.tsx", '<input className="outline-none border" />\n', "outline removed")
        self.assertTell("a.css", "button { outline: none; }\n", "outline removed")
        self.assertNoTell("a.tsx", '<input className="outline-none focus-visible:ring-2" />\n', "outline removed")
        self.assertNoTell("a.tsx", '<div className="px-2 outline-none data-[highlighted]:bg-zinc-100">x</div>\n', "outline removed")
        self.assertNoTell("a.tsx", '<div tabIndex={-1} className="fixed inset-0 outline-none">x</div>\n', "outline removed")
        self.assertNoTell("a.css", "button { outline: none; }\nbutton:focus-visible { outline: 2px solid; }\n", "outline removed")
        self.assertNoTell("a.css", "button { outline: none; }\nbutton:focus { outline: 2px solid; }\n", "outline removed")
        self.assertTell("a.css", ".btn:focus { outline: none; }\n", "outline removed")
        self.assertTell("a.css", ".btn:focus { outline: 0; }\n", "outline removed")

    def test_reveal_without_guard(self):
        self.assertTell("a.css", ".reveal {\n  opacity: 0;\n  transform: translateY(16px);\n}\n", "hidden reveal")
        self.assertTell("a.tsx", '<section className="reveal opacity-0 translate-y-4">x</section>\n', "hidden reveal")
        self.assertNoTell("a.css", ".js .reveal {\n  opacity: 0;\n}\n", "hidden reveal")
        self.assertNoTell("a.css", ".tooltip {\n  opacity: 0;\n}\n", "hidden reveal")
        self.assertNoTell("a.css", "@keyframes reveal { from { opacity: 0; } to { opacity: 1; } }\n", "hidden reveal")

    def test_stock_phrases(self):
        self.assertTell("a.html", "<h1>The future of invoicing</h1>\n", "stock headline phrase")
        self.assertTell("a.html", "<h2>Meet your new assistant</h2>\n", "stock headline phrase")
        self.assertTell("a.html", "<p>Built for finance teams</p>\n", "stock headline phrase")
        self.assertNoTell("a.html", "<h1>Close the books in two days</h1>\n", "stock headline phrase")
        self.assertNoTell("a.ts", "// the cache is built for each request\n", "stock headline phrase")

    def test_learn_more(self):
        self.assertTell("a.html", '<a href="/x">Learn more &rarr;</a>\n', "'Learn more'")
        self.assertNoTell("a.html", '<a href="/x">Learn more about pricing</a>\n', "'Learn more'")

    def test_centered_aggregate(self):
        items = "".join(f"<p>line {k}</p>" for k in range(8))
        self.assertTell("a.html", f'<section class="text-center"><h2>T</h2>{items}</section>\n', "text blocks centered")
        self.assertNoTell("a.html", f'<section class="text-center"><h2>T</h2></section><div>{items}</div>\n', "text blocks centered")
        self.assertNoTell("a.html", f'<section class="text-center"><h2>T</h2><div class="text-left">{items}</div></section>\n', "text blocks centered")

    def test_centered_stray_angle_brackets_stay_linear(self):
        content = "const x = a <b ? c : d;\nconst y = a <b ? \"c : d;\nconst z = a <b ? 'c : d;\n" * 1334
        start = time.monotonic()
        self.tells("a.tsx", content)
        self.assertLess(time.monotonic() - start, 2)

    def test_centered_multiline_tag(self):
        items = "".join(f"<p>line {k}</p>\n" for k in range(8))
        self.assertTell("a.tsx", f'<section\n  className="text-center"\n  title="a > b"\n>\n<h2>T</h2>\n{items}</section>\n', "text blocks centered")

    def test_hand_rolled_plural(self):
        self.assertTell("a.tsx", "const s = `${n} item${n !== 1 ? 's' : ''}`;\n", "hand-rolled plural")
        self.assertTell("a.ts", "const s = n === 1 ? 'item' : 'items';\n", "hand-rolled plural")
        self.assertTell("a.ts", 'const s = n + " file" + (count > 1 ? "s" : "");\n', "hand-rolled plural")
        self.assertTell("a.ts", "const s = n !== 1 ? 'matches' : 'match';\n", "hand-rolled plural")
        self.assertNoTell("a.ts", "const s = open ? 'open' : 'closed';\n", "hand-rolled plural")
        self.assertNoTell("a.ts", "const s = tls ? 'https' : 'http';\n", "hand-rolled plural")
        self.assertNoTell("a.ts", "const s = new Intl.PluralRules('en').select(n);\n", "hand-rolled plural")

    def test_sentence_concatenation(self):
        self.assertTell("a.tsx", "const msg = 'You have ' + n + ' new messages';\n", "sentence built by concatenation")
        self.assertNoTell("a.ts", "const url = '/api/' + id + '/items';\n", "sentence built by concatenation")
        self.assertNoTell("a.ts", "console.log('Loaded ' + n + ' items');\n", "sentence built by concatenation")
        self.assertNoTell("a.ts", "const cls = 'btn ' + size;\n", "sentence built by concatenation")

    def test_fixed_width_text_button(self):
        self.assertTell("a.tsx", '<button className="w-32 h-10 rounded-md">Save changes</button>\n', "fixed width on a text button")
        self.assertTell("a.tsx", "<Button style={{ width: 120 }}>Continue</Button>\n", "fixed width on a text button")
        self.assertNoTell("a.tsx", '<button className="w-8 h-8"><XIcon /></button>\n', "fixed width on a text button")
        self.assertNoTell("a.tsx", '<button className="w-full px-4">Save changes</button>\n', "fixed width on a text button")
        self.assertNoTell("a.tsx", '<button className="min-w-32 px-4">Save changes</button>\n', "fixed width on a text button")

    def test_pointer_drag_without_cancel(self):
        drag = "<div onPointerDown={start} onPointerMove={move} onPointerUp={end} />\n"
        self.assertTell("a.tsx", drag, "pointer drag without pointercancel")
        self.assertNoTell("a.tsx", drag.replace(" />", " onPointerCancel={end} />"), "pointer drag")
        self.assertNoTell("a.ts", "el.addEventListener('pointerdown', a);\nel.addEventListener('pointermove', b);\nel.addEventListener('lostpointercapture', c);\n", "pointer drag")
        self.assertNoTell("a.tsx", "<div onPointerMove={hover} />\n", "pointer drag")

    def test_blinking_cursor(self):
        self.assertTell("a.tsx", '<span className="ml-1 animate-pulse">|</span>\n', "blinking cursor")
        self.assertTell("a.tsx", '<span className="caret animate-blink" />\n', "blinking cursor")
        self.assertTell("a.css", ".caret { animation: blink 1s step-end infinite; }\n", "blinking cursor")
        self.assertNoTell("a.tsx", '<div className="h-4 w-32 animate-pulse rounded bg-zinc-200" />\n', "blinking cursor")
        self.assertNoTell("a.css", ".btn[aria-busy] {\n  cursor: wait;\n  animation: blink 1s infinite;\n}\n", "blinking cursor")

    def test_dash_saturation(self):
        self.assertTell("a.html", "<p>Fast — simple — honest.</p>\n" * 4, "em/en dashes in copy")
        self.assertNoTell("a.html", "<p>Fast — simple — honest.</p>\n" * 3, "em/en dashes")
        self.assertNoTell("a.html", "<p>Fast — simple — honest.</p>\n" * 4 + f"<p>{'word ' * 1000}</p>\n", "em/en dashes")
        self.assertNoTell("a.html", "<p>Mon–Fri</p><td>—</td>\n" * 10, "em/en dashes")

    def test_svh_hint(self):
        self.assertTell("a.tsx", '<section className="min-h-screen">x</section>\n', "min-h-svh for a full-height section")

    def test_zero_scale_entrance(self):
        self.assertTell("a.css", "@keyframes pop { from { transform: scale(0); } to { transform: scale(1); } }\n", "entrance from zero scale")
        self.assertTell("a.tsx", "<motion.div initial={{ opacity: 0, scale: 0 }} animate={{ scale: 1 }} />\n", "entrance from zero scale")
        self.assertTell("a.tsx", '<div className="transition-transform data-[state=closed]:scale-0" />\n', "entrance from zero scale")
        self.assertTell("a.tsx", '<div className="scale-0 transition duration-150 group-hover:scale-100" />\n', "entrance from zero scale")
        self.assertNoTell("a.tsx", '<div className="scale-0">x</div>\n', "entrance from zero scale")
        self.assertNoTell("a.css", ".pop { transform: scale(0.95); opacity: 0; }\n", "entrance from zero scale")
        self.assertNoTell("a.css", ".bar { transform: scaleX(0); }\n", "entrance from zero scale")
        self.assertNoTell("a.tsx", '<div className="scale-x-0 transition-transform" />\n', "entrance from zero scale")
        self.assertTell("a.css", ".pop { scale: 0 0; transition: scale 150ms; }\n", "entrance from zero scale")
        self.assertNoTell("a.css", ".u::after { scale: 0 1; }\n", "entrance from zero scale")

    def test_ease_in(self):
        self.assertTell("a.css", ".a { transition: opacity 150ms ease-in; }\n", "ease-in on a UI transition")
        self.assertTell("a.css", ".a { transition-timing-function: ease-in; }\n", "ease-in on a UI transition")
        self.assertTell("a.tsx", '<div className="transition-opacity duration-150 ease-in" />\n', "ease-in on a UI transition")
        self.assertNoTell("a.css", ".a { transition: opacity 150ms ease-in-out; }\n", "ease-in on a UI transition")
        self.assertNoTell("a.tsx", '<div className="transition-opacity ease-in-out" />\n', "ease-in on a UI transition")
        self.assertNoTell("a.css", ".a { transition: opacity 150ms var(--ease-in); }\n", "ease-in on a UI transition")

    def test_off_scale_spacing(self):
        self.assertTell("a.tsx", '<div className="p-[13px]">x</div>\n', "off the spacing scale")
        self.assertTell("a.tsx", '<div className="md:-mt-[6px] gap-4">x</div>\n', "off the spacing scale")
        self.assertTell("a.css", ".a { padding: 8px 13px; }\n", "off the spacing scale")
        self.assertTell("a.css", ".a { margin-inline-start: 10px; }\n", "off the spacing scale")
        self.assertNoTell("a.tsx", '<div className="p-[12px] gap-[2px] m-[1px] px-[1.5rem] py-[var(--x)]">x</div>\n', "off the spacing scale")
        self.assertNoTell("a.css", ".a { padding: 8px 16px; margin: -1px 0 2px; gap: 0; }\n", "off the spacing scale")
        self.assertNoTell("a.css", ".a { border-width: 3px; top: 13px; }\n", "off the spacing scale")
        self.assertTell("a.tsx", "<div style={{ padding: '13px' }}>x</div>\n", "off the spacing scale")
        self.assertNoTell("a.tsx", "<div style={{ padding: '8px', fontSize: '13px' }}>x</div>\n", "off the spacing scale")
        self.assertNoTell("a.html", '<div style="padding: 8px" data-w="13px">x</div>\n', "off the spacing scale")

    def test_mixed_icon_libraries(self):
        mixed = "import { X } from 'lucide-react';\nimport { FaGithub } from 'react-icons/fa';\n"
        self.assertTell("a.tsx", mixed, "icon libraries in one file")
        self.assertTell("a.tsx", "import { FaX } from 'react-icons/fa';\nimport { MdY } from 'react-icons/md';\n", "icon libraries in one file")
        self.assertNoTell("a.tsx", "import { X } from 'lucide-react';\nimport { Check } from 'lucide-react';\n", "icon libraries")
        self.assertNoTell("a.tsx", "import { A } from '@heroicons/react/24/outline';\nimport { B } from '@heroicons/react/20/solid';\n", "icon libraries")

    def test_pulsing_dot(self):
        self.assertTell("a.tsx", '<span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />\n', "pulsing dot")
        self.assertTell("a.tsx", '<span className="size-1.5 animate-pulse rounded-full" />\n', "pulsing dot")
        self.assertTell("a.tsx", '<span className="absolute animate-ping rounded-full" />\n', "pulsing dot")
        self.assertNoTell("a.tsx", '<div className="h-2 w-32 animate-pulse rounded-full bg-zinc-200" />\n', "pulsing dot")
        self.assertNoTell("a.tsx", '<span className="h-2 w-2 rounded-full bg-green-500" />\n', "pulsing dot")

    def test_line_height_unit(self):
        self.assertTell("a.css", "p { line-height: 24px; }\n", "line-height with a unit")
        self.assertTell("a.css", "p { line-height: 1.5rem; }\n", "line-height with a unit")
        self.assertTell("a.tsx", '<p className="leading-[24px]">x</p>\n', "line-height with a unit")
        self.assertTell("a.tsx", "<p style={{ lineHeight: '24px' }}>x</p>\n", "line-height with a unit")
        self.assertNoTell("a.tsx", '<p className="leading-6">x</p>\n', "line-height with a unit")
        self.assertNoTell("a.css", "p { line-height: 1.5; }\n", "line-height with a unit")

    def test_letter_spacing_px(self):
        self.assertTell("a.css", "h1 { letter-spacing: 1px; }\n", "letter-spacing in px")
        self.assertTell("a.tsx", '<h1 className="tracking-[1px]">x</h1>\n', "letter-spacing in px")
        self.assertTell("a.tsx", "<h1 style={{ letterSpacing: 1 }}>x</h1>\n", "letter-spacing in px")
        self.assertTell("a.tsx", "<h1 style={{ letterSpacing: '1px' }}>x</h1>\n", "letter-spacing in px")
        self.assertNoTell("a.tsx", '<h1 className="tracking-[-0.02em]">x</h1>\n', "letter-spacing in px")
        self.assertNoTell("a.tsx", "<h1 style={{ letterSpacing: 0 }}>x</h1>\n", "letter-spacing in px")

    def test_raw_opentype_tag(self):
        self.assertTell("a.css", '.n { font-feature-settings: "tnum" 1; }\n', "raw OpenType tag")
        self.assertTell("a.css", ".h { font-variation-settings: 'wght' 650; }\n", "raw OpenType tag")
        self.assertNoTell("a.css", '.a { font-feature-settings: "ss01" 1; }\n', "raw OpenType tag")
        self.assertNoTell("a.css", '.a { font-variation-settings: "GRAD" 80; }\n', "raw OpenType tag")

    def test_font_default_disabled(self):
        self.assertTell("a.css", "a { text-decoration-skip-ink: none; }\n", "font default disabled")
        self.assertTell("a.css", "h1 { font-kerning: none; }\n", "font default disabled")
        self.assertNoTell("a.css", "h1 { font-kerning: normal; }\n", "font default disabled")

    def test_balance_on_paragraph(self):
        self.assertTell("a.tsx", '<p className="text-balance">x</p>\n', "balance on a paragraph")
        self.assertTell("a.css", "p {\n  text-wrap: balance;\n}\n", "balance on a paragraph")
        self.assertTell("a.vue", "<style>\np {\n  margin: 0;\n  text-wrap: balance;\n}\n</style>\n", "balance on a paragraph")
        self.assertNoTell("a.tsx", '<h2 className="text-balance">x</h2>\n', "balance on a paragraph")
        self.assertNoTell("a.css", "h2 {\n  text-wrap: balance;\n}\n", "balance on a paragraph")
        self.assertNoTell("a.vue", "<style>\np { margin: 0; }\nh2 {\n  text-wrap: balance;\n}\n</style>\n", "balance on a paragraph")

    def test_tight_leading_on_paragraph(self):
        self.assertTell("a.tsx", '<p className="text-sm leading-tight">x</p>\n', "tight line-height on wrapping text")
        self.assertTell("a.tsx", '<p className="leading-none">x</p>\n', "tight line-height on wrapping text")
        self.assertNoTell("a.tsx", '<h1 className="leading-tight">x</h1>\n', "tight line-height on wrapping text")

    def test_unselectable_text(self):
        self.assertTell("a.tsx", '<main className="select-none">x</main>\n', "unselectable text")
        self.assertTell("a.css", "body {\n  user-select: none;\n}\n", "unselectable text")
        self.assertNoTell("a.tsx", '<button className="select-none">x</button>\n', "unselectable text")
        self.assertNoTell("a.css", ".handle {\n  user-select: none;\n}\n", "unselectable text")

    def test_font_smoothing_in_component(self):
        self.assertTell("a.tsx", '<div className="antialiased text-sm">x</div>\n', "font smoothing in a component")
        self.assertTell("a.css", ".card {\n  -webkit-font-smoothing: antialiased;\n}\n", "font smoothing in a component")
        self.assertNoTell("a.tsx", '<body className="antialiased">x</body>\n', "font smoothing")
        self.assertNoTell("a.css", "html {\n  -webkit-font-smoothing: antialiased;\n}\n", "font smoothing")
        self.assertNoTell("a.css", ":root { -webkit-font-smoothing: antialiased; }\n", "font smoothing")

    def test_line_clamp_without_box(self):
        self.assertTell("a.css", ".t {\n  -webkit-line-clamp: 3;\n  overflow: hidden;\n}\n", "line-clamp without a box")
        self.assertNoTell("a.css", ".t {\n  display: -webkit-box;\n  -webkit-box-orient: vertical;\n  -webkit-line-clamp: 3;\n}\n", "line-clamp without")
        self.assertNoTell("a.tsx", '<p className="line-clamp-3">x</p>\n', "line-clamp without")

    def test_full_viewport_width(self):
        self.assertTell("a.tsx", '<div className="w-screen bg-zinc-50">x</div>\n', "100vw width")
        self.assertTell("a.css", ".bar { width: 100vw; }\n", "100vw width")
        self.assertTell("a.tsx", "<div style={{ width: '100vw' }}>x</div>\n", "100vw width")
        self.assertTell("a.css", ".x{width: calc(100vw - 240px)}\n", "100vw width")
        self.assertNoTell("a.tsx", '<div className="fixed bottom-0 w-screen">x</div>\n', "100vw width")
        self.assertNoTell("a.css", ".bar {\n  position: fixed;\n  width: 100vw;\n}\n", "100vw width")
        self.assertNoTell("a.tsx", '<div className="max-w-screen-lg w-full">x</div>\n', "100vw width")
        self.assertNoTell("a.css", ".a { max-width: 100vw; }\n", "100vw width")

    def test_viewport_query_in_component(self):
        self.assertTell("Card.tsx", "const S = styled.div`\n  @media (max-width: 640px) {\n    padding: 0;\n  }\n`;\n", "viewport query in a component")
        self.assertTell("Card.module.css", "@media screen and (width < 40em) {\n  .a { padding: 0; }\n}\n", "viewport query in a component")
        query = "@media (max-width: 640px) {\n  .a { padding: 0; }\n}\n"
        self.assertNoTell("globals.css", query, "viewport query")
        self.assertNoTell("layout.tsx", "const S = styled.div`\n" + query + "`;\n", "viewport query")
        self.assertNoTell("Theme.tsx", "const G = createGlobalStyle`\n" + query + "`;\n", "viewport query")
        self.assertNoTell("Card.module.css", "@media (min-width: 48em) {\n  .a { padding: 0; }\n}\n", "viewport query")
        self.assertNoTell("Card.module.css", "@container (max-width: 30rem) {\n  .a { padding: 0; }\n}\n", "viewport query")
        os.mkdir(os.path.join(self.root, "pages"))
        self.assertNoTell(os.path.join("pages", "Home.tsx"), "const S = styled.div`\n" + query + "`;\n", "viewport query")

    def test_container_variant_without_container(self):
        self.assertTell("a.tsx", '<div className="flex flex-col @md:flex-row">x</div>\n', "container variant with no @container")
        self.assertTell("a.tsx", '<div className="@[34rem]:grid-cols-2">x</div>\n', "container variant with no @container")
        self.assertTell("a.tsx", '<div className="@max-md:hidden">x</div>\n', "container variant with no @container")
        two = '<div className="@md:flex-row">x</div>\n<div className="@lg:grid">y</div>\n'
        self.assertEqual(len([t for t in self.tells("a.tsx", two) if "container variant with no" in t]), 1)
        self.assertNoTell("a.tsx", '<section className="@container">\n<div className="@md:flex-row">x</div>\n</section>\n', "container variant with no")
        self.assertNoTell("a.tsx", '<div className="@md/sidebar:flex-row">x</div>\n', "container variant with no")
        self.assertNoTell("a.vue", '<button @click="x">Go</button>\n', "container variant with no")
        self.assertNoTell("a.css", ".a { @apply @md:flex-row; }\n", "container variant with no")

    def test_container_variant_on_own_container(self):
        self.assertTell("a.tsx", '<div className="@container @md:flex-row">x</div>\n', "@container and an @ variant on one element")
        self.assertNoTell("a.tsx", '<div className="@container"><div className="@md:flex-row">x</div></div>\n', "@container and an @ variant")
        self.assertNoTell("a.tsx", '<div className="@container/card p-4">x</div>\n', "@container and an @ variant")

    def test_false_data_attribute(self):
        self.assertTell("a.html", '<div data-open="false">x</div>\n', "behavior: boolean data attribute")
        self.assertTell("a.tsx", '<li data-selected={isSelected ? "true" : "false"}>x</li>\n', "boolean data attribute")
        self.assertNoTell("a.tsx", "<li data-index={String(index)}>x</li>\n", "boolean data attribute")
        self.assertNoTell("a.tsx", "<div data-open={open || undefined}>x</div>\n", "boolean data attribute")
        self.assertNoTell("a.tsx", '<div aria-expanded={open ? "true" : "false"}>x</div>\n', "boolean data attribute")
        self.assertNoTell("a.tsx", '<div data-state={open ? "open" : "closed"}>x</div>\n', "boolean data attribute")
        self.assertNoTell("a.html", '<a data-turbo="false" data-bs-dismiss="false" data-ad-slot="false">x</a>\n', "boolean data attribute")

    def test_copy_successfully(self):
        self.assertTell("a.tsx", 'toast.success("Project created successfully");\n', "'successfully' in UI copy")
        self.assertTell("a.html", "<p>Your changes were saved successfully.</p>\n", "'successfully' in UI copy")
        self.assertTell("a.ts", "setMsg('Uploaded successfully');\n", "'successfully' in UI copy")
        self.assertNoTell("a.ts", 'console.log("Fetched successfully");\n', "'successfully'")
        self.assertNoTell("a.ts", 'it("renders successfully", () => {});\n', "'successfully'")
        self.assertNoTell("a.ts", 'throw new Error("not completed successfully");\n', "'successfully'")
        self.assertNoTell("a.ts", "const successfullyLoaded = true; // returns successfully\n", "'successfully'")
        self.assertNoTell("a.test.tsx", 'toast.success("Project created successfully");\n', "'successfully'")
        self.assertTell("a.tsx", "<p>Your test (beta) was saved successfully.</p>\n", "'successfully' in UI copy")
        self.assertTell("a.ts", 'setMsg("Exported successfully. Download it.");\n', "'successfully' in UI copy")

    def test_copy_oops(self):
        self.assertTell("a.html", "<h2>Oops! Something went wrong</h2>\n", "'Oops'")
        self.assertTell("a.ts", 'setError("Something went wrong");\n', "'Oops'")
        self.assertTell("a.ts", 'toast.error("Something went wrong");\n', "'Oops'")
        self.assertTell("a.ts", "const t = { title: 'Whoops, try again' };\n", "'Oops'")
        self.assertNoTell("a.ts", "const oopsie = 1;\n", "'Oops'")
        self.assertNoTell("a.ts", 'console.error("something went wrong", e);\n', "'Oops'")
        self.assertNoTell("a.ts", 'logger.warn("oops");\n', "'Oops'")
        self.assertNoTell("a.ts", "// oops, fix later\n", "'Oops'")

    def test_copy_exclamation(self):
        self.assertTell("a.html", "<h1>Welcome aboard!</h1>\n", "exclamation mark")
        self.assertTell("a.ts", 'toast("Saved!");\n', "exclamation mark")
        self.assertTell("a.ts", "const s = x ? 'Done!' : '';\n", "exclamation mark")
        self.assertTell("a.html", "<p>You are all set! </p>\n", "exclamation mark")
        for line in ("if (!user) return;", ".a { color: red !important; }", "const s = '#!/usr/bin/env node';", "const s = '!important';",
                     'const s = a !== b ? "x" : "y";', "{!open && <Menu />}", 'expect(screen.getByText("Saved!"));'):
            self.assertNoTell("a.tsx", line + "\n", "exclamation mark")
        self.assertNoTell("a.spec.ts", 'toast("Saved!");\n', "exclamation mark")
        os.mkdir(os.path.join(self.root, "__tests__"))
        self.assertNoTell(os.path.join("__tests__", "a.ts"), 'toast("Saved!");\n', "exclamation mark")

    def test_vague_link_text(self):
        self.assertTell("a.html", '<a href="/r">Read more</a>\n', "vague link text")
        self.assertTell("a.tsx", '<Link to="/x">click here</Link>\n', "vague link text")
        self.assertTell("a.html", '<a href="/d">Details &rarr;</a>\n', "vague link text")
        self.assertNoTell("a.html", '<a href="/r" aria-label="Read more about the Q3 report">Read more</a>\n', "vague link text")
        self.assertNoTell("a.html", '<a href="/r">Read more about pricing</a>\n', "vague link text")
        self.assertNoTell("a.html", '<a href="/x">Learn more</a>\n', "vague link text")
        self.assertNoTell("a.html", '<a href="/x">More</a>\n', "vague link text")

    def test_hand_built_relative_time(self):
        self.assertTell("a.tsx", "const s = `${mins}m ago`;\n", "hand-built relative time")
        self.assertTell("a.tsx", "<span>{diff} minutes ago</span>\n", "hand-built relative time")
        self.assertTell("a.ts", "const s = `${n} days ago`;\n", "hand-built relative time")
        self.assertNoTell("a.ts", "const s = '2 days ago';\n", "hand-built relative time")
        self.assertNoTell("a.ts", "const s = rtf.format(-n, 'day');\n", "hand-built relative time")

    def test_new_rules_skip_minified_lines(self):
        self.assertNoTell("a.css", ".a{line-height:24px}" + ".b{color:red}" * 200 + "\n", "line-height with a unit")


if __name__ == "__main__":
    unittest.main()
