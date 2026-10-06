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
  # A mid-operation diff succeeds but is not the change, so warn instead of failing; --git-path also resolves inside linked worktrees.
  op=
  while IFS= read -r p; do
    [ -e "$p" ] || continue
    case $p in
      *rebase-merge) op="a rebase" ;;
      # `git am` also uses rebase-apply and leaves an `applying` file there.
      *rebase-apply) if [ -e "$p/applying" ]; then op="an am"; else op="a rebase"; fi ;;
      *MERGE_HEAD) op="a merge" ;;
      *CHERRY_PICK_HEAD) op="a cherry-pick" ;;
      *REVERT_HEAD) op="a revert" ;;
    esac
    break
  done <<EOF
$(git rev-parse --git-path rebase-merge --git-path rebase-apply --git-path MERGE_HEAD --git-path CHERRY_PICK_HEAD --git-path REVERT_HEAD)
EOF
  [ -z "$op" ] || echo "collect-diff: warning: $op is in progress, the diff mixes it with the change under review" >&2
  if [ -n "$base" ]; then
    git diff --no-color --no-ext-diff "$base" -- "$@" > "$out" || fail "cannot diff from $base"
  elif ! git rev-parse -q --verify HEAD >/dev/null; then
    git diff --no-color --no-ext-diff "$(git hash-object -t tree /dev/null)" -- "$@" > "$out" || fail "cannot diff the index"
  elif [ -n "$(git status --porcelain -- "$@")" ]; then
    from=HEAD
    if git rev-parse -q --verify '@{u}' >/dev/null 2>&1 && [ "$(git rev-list --count '@{u}..HEAD')" -gt 0 ]; then
      from=$(git merge-base '@{u}' HEAD) || fail "cannot find the merge base with the upstream"
    fi
    git diff --no-color --no-ext-diff "$from" -- "$@" > "$out" || fail "cannot diff from $from"
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
