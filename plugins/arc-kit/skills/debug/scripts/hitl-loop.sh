#!/usr/bin/env bash
# Human-in-the-loop repro: copy it, edit the steps, run it. The user answers in the terminal; the agent reads the KEY=VALUE lines at the end.
# Capture observations only; sign-in and secrets stay a `step`, because `capture` echoes its answer back.
# Adapted from mattpocock/skills diagnosing-bugs (MIT, Copyright (c) 2026 Matt Pocock).

set -euo pipefail

# step "<instruction>": show the instruction, wait for Enter.
step() {
  printf '\n>>> %s\n' "$1"
  read -r -p "    [Enter when done] " _
}

# capture VAR "<question>": show the question, read the answer into VAR.
capture() {
  local var="$1" question="$2" answer
  printf '\n>>> %s\n' "$question"
  read -r -p "    > " answer
  printf -v "$var" '%s' "$answer"
}

step "Open the app at http://localhost:3000 and sign in."
capture ERRORED "Click 'Export'. Did it throw an error? (y/n)"
capture ERROR_MSG "Paste the error message (or 'none'):"

printf '\n--- Captured ---\n'
printf 'ERRORED=%s\n' "$ERRORED"
printf 'ERROR_MSG=%s\n' "$ERROR_MSG"
