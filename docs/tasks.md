# Implementation Plan: WebUI Terminal Watch/Steer & Agent Delegation

## Phase 1: Environment & Dependency Baseline
- [x] 1.1 Verify Python environment and WebSocket support in NixOS package definition (`nix/package.nix`).
- [x] 1.2 Bundle minimal client-side terminal assets (`xterm.js`, `xterm-addon-fit.js`) into `share/` or vendored directory to ensure self-contained offline operation.

## Phase 2: WebUI Terminal Watch & Steer Backend (`bin/hive-web`)
- [x] 2.1 Add WebSocket endpoint support to `hive-web` (`/ws/terminal/<member>`).
- [x] 2.2 Implement pseudo-terminal (`pty`) spawner attaching to `tmux attach-session -r -t =hive-<member>` for Watch mode.
- [x] 2.3 Implement Steer mode toggling with bidirectional write support (`master_fd.write(data)`).
- [x] 2.4 Implement resize event handler (`resize` payload translating to PTY `TIOCSWINSZ` and tmux window-size updates).
- [x] 2.5 Add authentication/authorization checks (origin check, optional bearer token, Tailscale header check).

## Phase 3: WebUI Dashboard Frontend Updates (`share/dashboard.html`)
- [x] 3.1 Add Terminal Drawer modal component with collapsible viewport.
- [x] 3.2 Initialize `Terminal` instance connected to `/ws/terminal/<member>`.
- [x] 3.3 Add Mode Switcher button: `Watch (read-only)` vs `Steer (interactive)`.
- [x] 3.4 Add quick-steer input bar to type instructions or prompts directly without raw terminal capture.
- [x] 3.5 Test across dark/light mode and mobile/desktop responsive viewports.

## Phase 4: Agent-Triggered Delegation Engine (`bin/hive` CLI)
- [x] 4.1 Implement `hive delegate` subcommand parser (`target_member`, `--task`, `--worktree`, `--branch`, `--claims`).
- [x] 4.2 Add delegation depth validation (read `members/<current>/state/delegation.json`; block if depth >= 1).
- [x] 4.3 Add target status & availability validation (ensure target is idle or dead, not active).
- [x] 4.4 Implement claim transfer check and pre-registration for the delegated member.
- [x] 4.5 Post structured delegation event to `/srv/hive/ROOM.md`.
- [x] 4.6 Trigger wake sequence via `hive-member wake <target>` passing initial task prompt.
- [x] 4.7 Record active delegation metadata in `members/<target>/state/delegation.json`.

## Phase 5: Room Completion Handshake & Cleanup
- [x] 5.1 Update `hive-hook` PostToolUse/Stop handlers to recognize completion of a delegated task.
- [x] 5.2 Release delegated claims and append completion record to `ROOM.md`.
- [x] 5.3 Reset delegation state file upon completion (`hive delegate done`).

## Phase 6: Automated Testing & Validation
- [x] 6.1 Add unit tests for `hive delegate` command line parsing, claim validation, and depth limiting.
- [x] 6.2 Test WebSocket streaming with dummy tmux sessions under `hive` user privileges.
- [x] 6.3 Execute full end-to-end integration test: delegating a subtask, monitoring in WebUI watch/steer, and validating Room entries.
- [x] 6.4 Update `SPEC.md` and `README.md` documentation reflecting the new primitives.
