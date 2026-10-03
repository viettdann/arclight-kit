#!/bin/sh
# Usage: collect-diff.sh [--base <commit>] <path>... ; prints the diff file path, exits 2 when the diff is empty.
set -u

base=
if [ "${1:-}" = --base ]; then
  [ $# -ge 2 ] || { echo "collect-diff: --base needs a commit" >&2; exit 64; }
  base=$2
  shift 2
fi
[ $# -gt 0 ] || { echo "collect-diff: no paths given" >&2; exit 64; }

out=$(mktemp "${TMPDIR:-/tmp}/verifier-diff.XXXXXX") || exit 1
fail() { echo "collect-diff: $1" >&2; rm -f "$out"; exit 1; }

append_whole_files() {
  rc=0
  while IFS= read -r f; do
    git diff --no-index --no-color --no-ext-diff -- /dev/null "$f" >> "$out"
    [ $? -le 1 ] || rc=1
  done
  return $rc
}

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if [ -n "$base" ]; then
    git diff --no-color --no-ext-diff "$base" -- "$@" > "$out" || fail "cannot diff from $base"
  elif ! git rev-parse -q --verify HEAD >/dev/null; then
    git diff --no-color --no-ext-diff "$(git hash-object -t tree /dev/null)" -- "$@" > "$out" || fail "cannot diff the index"
  elif [ -n "$(git status --porcelain -- "$@")" ]; then
    git diff --no-color --no-ext-diff HEAD -- "$@" > "$out" || fail "cannot diff HEAD"
  elif git rev-parse -q --verify '@{u}' >/dev/null 2>&1; then
    git diff --no-color --no-ext-diff '@{u}...HEAD' -- "$@" > "$out" || fail "cannot diff the upstream"
  fi
  git ls-files --others --exclude-standard -- "$@" | append_whole_files || fail "cannot read an untracked file"
else
  for p in "$@"; do
    [ -e "$p" ] || fail "no such path: $p"
    find "$p" -type f | append_whole_files || fail "cannot read a file under $p"
  done
fi

if [ ! -s "$out" ]; then
  rm -f "$out"
  echo "collect-diff: empty diff for $*" >&2
  exit 2
fi
echo "$out"
