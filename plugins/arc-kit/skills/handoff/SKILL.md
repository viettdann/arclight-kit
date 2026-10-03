---
name: handoff
description: Write a verified handoff file so work can continue in a fresh session, another repo or harness, or with a colleague; with `resume`, pick up from the latest one.
argument-hint: "[resume]"
disable-model-invocation: true
effort: high
---

# Handoff

A handoff is a short, accurate Markdown file that lets a brand-new session pick up exactly where this one stopped. It lives in `${CLAUDE_PROJECT_DIR}/docs/` (written `docs/` below), is named with today's date and the task, and is written from verified facts.

Accuracy is the whole point - a confident-but-wrong handoff is worse than useless.

Invoked with `resume`, or as the first thing in a session with no work yet: go to Resuming. Otherwise write one.

A handoff carries work somewhere this session can't follow: a later session after `/clear` or a restart, another repo or directory, another harness, a colleague, or a side task forked off without derailing this one. When the next step continues the same task in this session, `/compact <what the next phase needs>` keeps more of the reasoning. If the user invokes it in that case, write the handoff as asked and end the reply with that alternative ready to paste: `/compact <focus>` alone in a code block, the focus naming the next step, the files it touches, and the decisions it must keep.

## Writing a handoff

### Step 1 - Ground yourself in reality first

Read the actual current state of the repo and any file you're about to describe; do not rely on your recollection of the chat (memory drift is exactly what compaction gets wrong).

```bash
date +%F                  # today's date for the filename
git status                # staged / modified / untracked
git diff HEAD --stat      # which files changed (staged + unstaged), how much
git diff HEAD -- . ':(exclude)*.env*' ':(exclude)*.pem' ':(exclude)*.key' ':(exclude)*.p12' \
  ':(exclude)*.pfx' ':(exclude)*id_rsa*' ':(exclude)*id_ed25519*' ':(exclude)*credentials*'
git log --oneline -10     # recent commits for context
```

The `:(exclude)` patterns keep env files, private keys, certificates and credential files out of the diff. Before pasting any diff content into the handoff, scan it for secrets (API keys, tokens, credentials) and redact them - the handoff is plaintext and may be committed.

If git is unavailable, list the working directory (`ls -R` scoped to the area you worked in) and read the files you touched. Warn the user that without version control the handoff's change-tracking is unverified, and record that caveat in _Open questions_.

### Step 2 - Choose the filename

Format: `docs/handoff-YYYY-MM-DD-<slug>.md` (e.g. `docs/handoff-2026-06-06-auth-token-refresh.md`).

- `YYYY-MM-DD` is today's date (date-first so files sort chronologically).
- `<slug>` is 2-4 kebab-case words naming the task: `auth-token-refresh`, `csv-import-bug`.

Create the dir if missing (`mkdir -p docs`). Same-day same-slug collisions are common, so enumerate existing matches before writing and append the lowest free numeric suffix after the slug:

```bash
ls docs/handoff-YYYY-MM-DD-<slug>*.md 2>/dev/null
```

If the base name is taken, use `-2`, then `-3`, etc. (`handoff-2026-06-06-<slug>-2.md`). Never overwrite an existing handoff.

### Step 3 - Write the file

Read [assets/handoff-template.md](assets/handoff-template.md) and fill every section from what you verified in Step 1. The template's session ID is `${CLAUDE_SESSION_ID}`. If you're unsure how much detail a section needs, [references/example.md](references/example.md) is a filled-in handoff at the right density - read it only when that calibration is missing.

The template's inline notes carry the per-section rules. Two calibrations worth restating: a claim you can't verify moves to _Open questions_ or gets dropped, never into _Current state_, _Files in flight_, or _Changed_; and hedged uncertainty is the correct register there. "I think the migration ran but didn't confirm" is useful; asserting "the migration ran" when you didn't check is the failure mode this skill prevents.

Keep the file to a screen or two - density beats length. Omit empty sections rather than padding them. After writing, tell the user the path and suggest: review it, `/clear`, then start the next session by reading it.

### Retention

Handoff files accumulate. Recommend deleting or archiving a handoff once its task is closed (merged/shipped), so the dir stays current.

## Resuming

1. Find the latest handoff: `ls -t docs/handoff-*.md | head -5`, pick the relevant one (confirm if ambiguous). If none exist, say so and ask whether to start cold or point you at a specific file - do not invent prior context.
2. Read it fully.
3. Re-ground as in Step 1: run `git status` and `git diff`, confirm the repo still matches _Current state_ and _Files in flight_ (files may have changed since it was written).
4. State the plan back in one or two lines (goal + next step), then proceed.

If the repo and the handoff disagree, trust the repo and say so; don't act on stale notes. If the handoff lacks a detail you need, tell the user they can reopen the original transcript with `claude --resume` and the session ID in its header.
