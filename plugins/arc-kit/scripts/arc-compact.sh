#!/bin/sh
# Silent unless /arc-kit:arc was typed earlier in this transcript.
transcript=$(sed -n 's/.*"transcript_path" *: *"\([^"]*\)".*/\1/p')
[ -f "$transcript" ] || exit 0
grep -qE '"type":"user".*<command-name>/(arc-kit:)?arc</command-name>' "$transcript" || exit 0
printf 'Arc daily defaults (/arc-kit:arc, invoked earlier in this session) still apply:\n\n'
sed -n '/^# Arc/,$p' "${CLAUDE_PLUGIN_ROOT}/skills/arc/SKILL.md" | grep -v '^On invocation:'
