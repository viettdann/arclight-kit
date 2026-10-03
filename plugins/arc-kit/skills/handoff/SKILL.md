---
name: handoff
description: "Save or resume a concise, verified session handoff with the task, current files, checks, decisions, and next action. Use for wrap up, save progress, resume a handoff, lưu tiến độ, ghi handoff, tạm dừng, or tiếp tục từ handoff. Complements Codex compaction and session resume."
---

# Handoff

Write a short Markdown file that lets a fresh session continue from verified state. Use Vietnamese in chat and English in files unless requested otherwise. Follow applicable AGENTS.md instructions. A handoff supplements the runtime's context compaction and session resume features.

## Save progress

1. Identify the project root from the workspace context and git when available. Read the current branch, scoped status and diff, relevant recent commits, and the files you describe. Inspect only the task's paths; avoid exposing unrelated edits and secrets. Use `rg --files` for file discovery. If there is no repository, inspect the relevant files directly and record that change tracking could not be verified.
2. Capture the active goal, latest user corrections, authorization boundaries, completed work, remaining items, and actual verification results. Distinguish observed facts from assumptions and from work reported by another worker. Do not claim a test ran if its result is unavailable.
3. Choose `docs/handoff-YYYY-MM-DD-<slug>.md` under the verified project root, using the local date and a short lowercase kebab-case task slug. Create the directory if needed. If the destination already exists, append the lowest free suffix (`-2`, `-3`, etc.). Never overwrite a previous handoff. If no writable project root is identifiable, ask where to save it.
4. Read [assets/handoff-template.md](assets/handoff-template.md), relative to this loaded skill directory, and fill the applicable sections. Consult [references/example.md](references/example.md) only when a density example would help. Keep the result to a screen or two and omit empty sections.
5. Recheck file names, commands, branch, and completion claims. Redact credentials and tokens from excerpts. State the saved path and the concrete next action. Leave `docs/` unstaged unless the user explicitly asks to commit it.

Include a source session ID only when it is actually exposed by the runtime or supplied and verified in this session. Do not invent a session environment variable, scrape unrelated transcripts, or manufacture an ID. When a verified Codex session ID is available and the installed CLI supports it, record `codex resume <session-id>`; otherwise omit the resume command. Reading the handoff in a fresh session is always sufficient to use the saved context.

## Resume progress

Find relevant `docs/handoff-*.md` files beneath the current project root. Prefer the task and date matching the request; ask only if several files are plausible. If none exists, ask for its location or the missing task context instead of inventing earlier work.

Read the entire handoff and recheck the referenced files, current branch, status, and scoped diff. Trust the repository when it disagrees with stale notes. Preserve existing changes and identify any assumption that no longer holds.

State the current goal and next action briefly, then continue the user's authorized task. Resume only the scope recorded and requested; a handoff does not itself authorize deployment, messaging, or unrelated changes. Verify any session resume command against the available CLI before suggesting it.

## Retention

When the task is closed, mention archiving or deleting its handoff if useful. Do not delete saved context without authorization.
