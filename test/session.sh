#!/usr/bin/env bash
# Exercise session routing and harness flags without starting real agents.
set -euo pipefail
repo=$(readlink -f "$(dirname "$0")/..")
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
export HIVE_ROOT="$tmp/hive" HIVE_USER="$(id -un)" HIVE_TEST_LOG="$tmp/log"
export HIVE_TEST_AGENT_PID=$$
export HIVE_MEMBER=bob
mkdir -p "$HIVE_ROOT/members/bob/state" "$HIVE_ROOT/telemetry/members" "$HIVE_ROOT/projects" "$tmp/bin" "$tmp/share"
printf '%s\n' '{"harness":"codex","dir":"'"$HIVE_ROOT/projects"'"}' >"$HIVE_ROOT/members/bob/state/launch.json"
printf '%s\n' '{"session_id":"test-session","harness":"codex"}' >"$HIVE_ROOT/telemetry/members/bob.json"
cat >"$tmp/bin/tmux" <<'EOF'
#!/usr/bin/env bash
if [[ $1 == has-session ]]; then [[ ${HIVE_TEST_LIVE:-0} == 1 ]]; exit; fi
if [[ $1 == list-panes ]]; then [[ ${HIVE_TEST_LIVE:-0} == 1 ]] && printf '%s\n' "$HIVE_TEST_AGENT_PID"; exit; fi
printf 'tmux %s\n' "$*" >>"$HIVE_TEST_LOG"
EOF
cat >"$tmp/bin/hive-launch" <<'EOF'
#!/usr/bin/env bash
printf 'launch %s\n' "$*" >>"$HIVE_TEST_LOG"
EOF
cat >"$tmp/bin/sleep" <<'EOF'
#!/usr/bin/env bash
printf 'sleep %s\n' "$*" >>"$HIVE_TEST_LOG"
EOF
chmod +x "$tmp/bin/"*
export PATH="$tmp/bin:$repo/bin:$PATH"
"$repo/bin/hive-member" send bob 'do the next task' >/dev/null
rg -q '^launch bob codex .* -- resume test-session do the next task$' "$HIVE_TEST_LOG"
printf 'cold wake delivered initial prompt\n'

: >"$HIVE_TEST_LOG"
printf '%s\n' '{"harness":"bash","dir":"/tmp"}' >"$HIVE_ROOT/members/bob/state/launch.json"
printf '%s\n' '{"pid":99999,"harness":"bash","status":"idle"}' >"$HIVE_ROOT/telemetry/members/bob.json"
HIVE_TEST_LIVE=1 "$repo/bin/hive-member" send bob 'do live task' >/dev/null
rg -q '^tmux load-buffer -b hive-send-[0-9]+-[0-9]+ -$' "$HIVE_TEST_LOG"
rg -q '^tmux paste-buffer -d -p -b hive-send-[0-9]+-[0-9]+ -t =hive-bob:0.0$' "$HIVE_TEST_LOG"
rg -q '^tmux send-keys .* Enter$' "$HIVE_TEST_LOG"
mapfile -t send_events <"$HIVE_TEST_LOG"
[[ ${#send_events[@]} == 4 && ${send_events[0]} == tmux\ load-buffer* &&
   ${send_events[1]} == tmux\ paste-buffer* && ${send_events[2]} == 'sleep 1' && ${send_events[3]} == *' Enter' ]]
printf 'live member prompted\n'

cat >"$tmp/bin/claude" <<'EOF'
#!/usr/bin/env bash
printf 'claude %s\n' "$*" >>"$HIVE_TEST_LOG"
EOF
cat >"$tmp/bin/codex" <<'EOF'
#!/usr/bin/env bash
printf 'codex %s\n' "$*" >>"$HIVE_TEST_LOG"
EOF
chmod +x "$tmp/bin/claude" "$tmp/bin/codex"
printf 'member instruction\n' >"$tmp/share/member-instruction.md"
HIVE_SHARE="$tmp/share" "$repo/bin/hive-launch" --run claude 'first task' </dev/null >/dev/null
HIVE_SHARE="$tmp/share" "$repo/bin/hive-launch" --run codex 'first task' </dev/null >/dev/null
rg -q '^claude --permission-mode auto .*first task$' "$HIVE_TEST_LOG"
rg -q '^codex --approve-for-me --add-dir '"$HIVE_ROOT"' .*first task$' "$HIVE_TEST_LOG"
printf 'autonomous launch flags applied\n'

mkdir -p "$HIVE_ROOT/members/bob/notes" "$HIVE_ROOT/claims/demo"
printf 'keep work here\n' >"$HIVE_ROOT/members/bob/notes/work.md"
printf 'bob\n' >"$HIVE_ROOT/claims/demo/owner"
"$repo/bin/hive-member" delete bob >/dev/null
[[ ! -e $HIVE_ROOT/members/bob && ! -e $HIVE_ROOT/telemetry/members/bob.json && ! -e $HIVE_ROOT/claims/demo ]]
printf 'delete removes member session state and claims\n'
