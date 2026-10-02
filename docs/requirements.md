# Requirements Specification: WebUI Terminal Watch/Steer & Agent Delegation

## 1. Overview & Context

Agentic Hive is a persistent Unix habitat for coding agents (Claude Code, Codex, OpenCode) operating in `/srv/hive`.
Currently:
1. `hive-web` serves a read-only HTTP dashboard displaying host telemetry, active members, claims, and `ROOM.md`.
2. Interaction is strictly out-of-band via SSH, `tmux attach`, and Git.
3. Member spawning and tasking are strictly reserved for the human Beekeeper.

The user requests two architectural extensions:
- **Feature A (WebUI Terminal Watch & Steer)**: Attach terminal to watch member sessions live and steer chat directly to a session via the WebUI.
- **Feature B (Autonomous Agent Delegation & Room Coordination)**: Allow an agent to split a large task, trigger/wake another session, and coordinate execution via Room without blocking.

---

## 2. Requirements in EARS Notation

### Feature A: WebUI Terminal Watch & Steer

#### Ubiquitous Requirements
- **REQ-A-01**: THE SYSTEM SHALL provide a browser-accessible terminal viewport for each active member session in `hive-web`.
- **REQ-A-02**: THE SYSTEM SHALL maintain default read-only ("Watch") mode upon connecting to prevent accidental disruption to running agents.
- **REQ-A-03**: THE SYSTEM SHALL stream raw ANSI escape sequences and resize events from the underlying session to an xterm-compatible web frontend via WebSockets.

#### Event-Driven Requirements
- **REQ-A-04**: WHEN the Beekeeper toggles "Steer Mode" for a member session, THE SYSTEM SHALL permit bidirectional keystroke and PTY interaction with the target member's tmux pane.
- **REQ-A-05**: WHEN the Beekeeper submits a structured steering message (e.g. chat injection prompt), THE SYSTEM SHALL cleanly format and transmit the input to the target agent harness without corrupting terminal escape state.
- **REQ-A-06**: WHEN a member process terminates or disconnects, THE SYSTEM SHALL visibly notify the web client and transition the terminal viewport to a disconnected state.

#### State-Driven Requirements
- **REQ-A-07**: WHILE in "Watch Mode", THE SYSTEM SHALL discard all client input keystrokes at the backend proxy before they can reach the member's PTY.
- **REQ-A-08**: WHILE multiple web clients are observing the same member session, THE SYSTEM SHALL fan out PTY output broadcast streams without creating multiple tmux client windows.

#### Unwanted Behavior & Security Requirements
- **REQ-A-09**: IF an incoming WebSocket connection attempts to attach or steer without authorized Beekeeper credentials or valid Tailscale/localhost network isolation, THEN THE SYSTEM SHALL reject the connection immediately with HTTP 403 / WebSocket close code 1008.
- **REQ-A-10**: IF a terminal session crashes or generates unbounded burst output, THEN THE SYSTEM SHALL apply flow control / backpressure to prevent memory exhaustion in `hive-web`.

---

### Feature B: Agent-Triggered Delegation & Room Coordination

#### Ubiquitous Requirements
- **REQ-B-01**: THE SYSTEM SHALL enforce that task delegation operates strictly through deterministic Hive primitives (`ROOM.md`, claims, Git worktrees, and `hive` CLI).
- **REQ-B-02**: THE SYSTEM SHALL maintain a maximum delegation recursion depth of 1 (delegated sub-agents are forbidden from delegating further).

#### Event-Driven Requirements
- **REQ-B-03**: WHEN an active member decides to delegate a subtask, THE SYSTEM SHALL require the delegating member to post a structured delegation announcement to `ROOM.md` containing target member identity, task specification, designated Git branch/worktree, and claimed file paths.
- **REQ-B-04**: WHEN an agent initiates a subtask delegation via `hive delegate <target-member> --task <spec> --worktree <dir>`, THE SYSTEM SHALL wake or resume the target member session and deliver the task prompt cleanly.
- **REQ-B-05**: WHEN the delegated member completes or fails its subtask, THE SYSTEM SHALL announce the outcome in `ROOM.md`, release all held claims, and notify the delegating member.

#### State-Driven Requirements
- **REQ-B-06**: WHILE a delegation is active, THE delegating member SHALL continue its own independent work or wait asynchronously without holding claims required by the delegated member.

#### Unwanted Behavior & Constraints
- **REQ-B-07**: IF a proposed delegation attempts to claim resources already claimed by another member, THEN THE SYSTEM SHALL reject the delegation command before session wake.
- **REQ-B-08**: IF no idle pre-configured member is available in the habitat, THEN THE SYSTEM SHALL prevent dynamic, unbounded process spawning and alert the delegating agent that delegation capacity is exhausted.
- **REQ-B-09**: IF an agent attempts recursive delegation (delegation depth > 1), THEN THE SYSTEM SHALL abort the request with an explicit error code.

---

## 3. Constraints & Non-Goals

1. **Host Physics Invariant**: System-level administrative privileges (NixOS rebuilds, root sudo, user management) remain exclusively Beekeeper-controlled.
2. **Deterministic Primitives**: No black-box autonomous orchestration daemons, LLM supervisors, or Redis/Kafka brokers. Coordination must remain inspectable in `/srv/hive/ROOM.md`.
3. **No Unauthenticated Public Exposure**: Terminal steering must never be exposed on open public internet ports.
