# Patterns: words and examples

## Vocabulary

Match inflected forms (`leverage`, `leveraging`, `leveraged`), but judge by sense: `real` meaning factual, `robust` as a statistics term, and `ecosystem` naming an actual package ecosystem are fine.

**Always replace.**

| Word | Plain form |
| --- | --- |
| delve (into), deep dive, dive into, unpack | look at, explain |
| landscape, realm, tapestry, symphony (as metaphors) | field, area, or describe the thing |
| leverage (verb), utilize, harness | use |
| robust, comprehensive | reliable, complete, or say what it covers |
| seamless(ly) | smooth, without extra steps, or say what is skipped |
| pivotal, crucial, paramount | key, important, or say why |
| cutting-edge, state-of-the-art, best-in-class | newest, or cite the comparison |
| testament to, underscores, showcases | shows |
| meticulous(ly), intricate | careful, detailed, or name the detail |
| embark on, commence | start |
| game-changer, transformative, revolutionize | say what changed |
| empower, unleash, elevate, foster | let, enable, improve, build |
| actionable, impactful, holistic | practical, effective, complete |
| in order to, due to the fact that | to, because |
| ascertain, endeavor, facilitate | find out, try, help |
| at its core, fundamentally, the reality is | delete |

**Flag when two or more share a paragraph.** navigate, streamline, bolster, spearhead, resonate, underpin, nuanced, multifaceted, myriad, plethora, encompass, catalyze, reimagine, cultivate, illuminate, cornerstone, poised to, burgeoning, nascent, overarching, ecosystem, synergy, interplay.

**Flag only when dense.** significant, innovative, effective, dynamic, scalable, compelling, unprecedented, remarkable, sophisticated, exceptional. Replace some with the number, the comparison, or the example.

**Transitions to cut or plain-word.** Moreover, Furthermore, Additionally → "and", "also", or a sentence that makes the link obvious. "In conclusion", "In summary", "When it comes to", "At the end of the day", "That being said" → cut.

## Before and after

**Narrating the diff (docs).**
Before: "This function was added to replace the previous approach of scanning every item."
After: "Looks items up in a hash map keyed by id."

**Negation reveal.**
Before: "The bottleneck isn't the database. It's the serializer."
After: "The serializer is the bottleneck: it takes 70% of the request time."

**Significance inflation.**
Before: "This release marks a pivotal moment in the evolution of our API."
After: "This release adds cursor pagination to every list endpoint."

**Narrated candor.**
Before: "Two caveats I'd rather flag now than let you discover later: it's untested on Windows, and the cache isn't invalidated on rename."
After: "Two caveats: it's untested on Windows, and the cache isn't invalidated on rename."

**Self-label.**
Before: "Two indexes for tiered storage. That last move is the clever one."
After: "Two indexes for tiered storage, so the hot path never reads cold pages."

**Bare-noun bullets.**
Before: "- Robust error handling / - Seamless integration / - Optimized performance"
After: "- Retries failed uploads three times, then keeps the file for a manual retry / - Reads the existing `appsettings.json`; no new config"

**Hedge stack.**
Before: "This could potentially reduce load times."
After: "This should cut load time; it hasn't been measured yet."

**Recap-flattery reply.**
Before: "Thanks so much for the detailed migration script and the careful rollback plan you put together! I think this approach looks great overall."
After: "Thanks, this looks right. One question on the rollback step below."

**Chatbot closer.**
Before: "…and that's how the export works. I hope this helps! Let me know if you have any other questions."
After: "…and that's how the export works."

**Staccato drama.**
Before: "No config. No setup. No waiting. Just results."
After: "It runs with no config file and returns results in under a second."

**Vietnamese.**
Before: "Dưới đây là tổng quan về tính năng xuất file. Tính năng này đóng vai trò quan trọng, không chỉ giúp tiết kiệm thời gian mà còn nâng cao hiệu quả công việc một cách đáng kể. Hy vọng thông tin này hữu ích!"
After: "Xuất file chạy nền, nên danh sách 50.000 dòng không còn khoá màn hình trong lúc chờ."

## Leaks to delete on sight

- Placeholders: `[Your Name]`, `[Insert source]`, `[Describe …]`, `2025-XX-XX`, `<!-- add citation -->`.
- Chat citation markup: `citeturn0search0`, `contentReference[oaicite:0]`, `oai_citation`, `[attached_file:1]`.
- AI referrer parameters on URLs: `utm_source=chatgpt.com`, `utm_source=openai`, `utm_source=claude.ai`, `utm_source=perplexity.ai`. Remove only that parameter; keep the URL.
- Cutoff disclaimers: "As of my last update", "I don't have access to real-time data", "Based on available information".
