---
name: debug
description: "Find and fix the root cause of a bug: pin the symptom in one line, reproduce it with a command that fails now, narrow it with ranked hypotheses and the cheapest experiment that could disprove each (recent changes and git bisect first), fix it once in the shared path, and keep the repro as a regression test seen failing before the fix. Use when something errors, crashes, returns the wrong result, a test fails, or behavior regressed (\"debug\", \"fix this bug\", \"why does this fail\", \"sửa lỗi\", \"tại sao lỗi\", \"bị lỗi\", \"không chạy\", \"crash\", \"test fail\", \"trước chạy được giờ hỏng\"). Asked only why, it stops at the diagnosis. Not for a UI control that does nothing or resets state (see the arc-design state-check skill), rendering defects (see the arc-design ui-check skill), or build errors with an obvious message."
---

# Debug

Find the cause before changing code, then fix it once, with a test that failed before the fix. A diff that makes the symptom disappear without a confirmed cause is a guess.

Before starting, read `references/codex-workflow.md` for the complete workflow, checks, and report format. Load its other references only when the relevant step calls for them.

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.
