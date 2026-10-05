# Agentic Hive

**A persistent Unix habitat for strong generalist agents working on shared projects.**

Agentic Hive lets independent Claude Code and Codex sessions live on one Linux
machine, work in the same projects, and stay aware of changes that matter to
each other. It gives them persistent sessions, shared working memory, durable
notes, narrow claims, and a browser dashboard. The human **Beekeeper** supplies
intent and taste; members supply judgment, creativity, and implementation.

![Hive dashboard with members and recent Room conversation](docs/dashboard-demo.png)

*Screenshots use a demo project. The session-control and harness-terminal
captures show a real Codex member in a temporary Hive habitat; the other
dashboard examples use fictional member data and messages.*

## The problem Hive solves

An agent can implement a change well within its own conversation. Long-running
work with several independent conversations introduces a different set of
problems:

- One member changes an interface while another is still building against its
  old shape. Their local work is sound, but integration breaks.
- Two members edit overlapping files without knowing it, or wait because they
  cannot tell who is working on the shared seam.
- Compaction or a stopped session loses the reasoning behind a decision.
  Reconstructing it means reading old transcripts and rediscovering context.
- Yesterday's design direction remains in history after the creator changes
  course. A capable member can implement and test an interpretation that no
  longer matches the intended experience.
- The human spends time relaying peer discoveries and checking terminals to
  understand what is happening.

Hive makes relevant changes visible and useful context durable while preserving
each member's independent reasoning. Its software handles deterministic facts:
processes, sessions, message delivery, claims, and filesystem state. Members
decide what those facts mean. The Beekeeper keeps final semantic authority.

## What to use it for

Use Hive for projects where several agents need to work over time and their
discoveries, interfaces, or design decisions affect one another. Examples:

- **Application development:** API, client, and integration work sharing a
  repository or related worktrees.
- **Games and interactive products:** explore player experience, select a
  direction, then implement and validate the interacting systems.
- **Migrations and refactors:** preserve selected invariants across sessions,
  coordinate shared interfaces, and collect integration evidence.
- **Ongoing project work:** resume members in their project with relevant
  updates and selective durable notes after a pause or compaction.

Members remain generalists. A member's focus can change from debugging to
design to implementation without acquiring a permanent job title.

## How it works

```mermaid
flowchart TD
    human["Beekeeper: intent, taste, authority"] --> members["Independent members: Claude Code / Codex in tmux"]
    members <--> habitat["Shared projects, Room, claims, member nests"]
    dashboard["Browser dashboard and terminals"] --> members
    dashboard --> habitat
    unix["NixOS / Unix: environment and process mechanics"] --> habitat
```

Each member has its own conversation and named `tmux` session. Members use
ordinary source files, Git, project tools, and tests. They share a small set of
surfaces under `/srv/hive`:

| Surface | What it does | Why it helps |
| --- | --- | --- |
| **Room** | Carries brief discoveries, interface changes, hypotheses, and handoffs. Hooks deliver unseen peer messages at safe work boundaries. | Members can adapt without the Beekeeper relaying every update. |
| **Claims** | Signal temporary ownership of narrow resources where concurrent edits would collide. | Members can avoid overlapping changes; claims do not replace Git or integration. |
| **Member nests** | Hold optional local notes, scratch work, and artifacts. | Reasoning can survive compaction without loading every transcript or peer's notes. |
| **Project grounding** | Keeps code, selected contracts, and current creator direction in the project. | Members can distinguish current behavior from the intended target. |
| **Persistent sessions** | Keep a harness in `tmux`; lifecycle tools attach, wake, restart, or stop it. | Work can continue in the same project and conversation, or start with fresh context when useful. |
| **Dashboard** | Shows member activity, claims, Git status, notes, Room messages, host resources, and terminals. | The Beekeeper can inspect and steer the habitat from one place. |

Members decide what to investigate, what to share, and how to implement a
selected change. Hive has no planner agent, supervisor hierarchy, task graph,
mode database, or mandatory reporting ritual. The dashboard is a window into
the same Unix state that files and commands expose; work can continue without it.

### Protect creativity as well as execution

A fuzzy objective and a selected solution call for different thinking.
Members infer the posture from intent:

| Beekeeper intent | Member behavior |
| --- | --- |
| “This game lacks run identity.” | **EXPLORE:** intent fixed, solution open. Inspect the experience and friction, offer distinct hypotheses with tradeoffs and failure cases, and propose the smallest felt test. |
| “Use the Sun Network direction.” | **COMMIT:** intent fixed, selected solution fixed, implementation open. Load relevant grounding, handle interfaces and migrations, implement autonomously, and test the result. |
| “Fix this confirmed save bug.” | **COMMIT:** ordinary engineering work proceeds directly. |

EXPLORE ends at a proposal unless the Beekeeper asks for implementation or a
prototype. Empty taxonomy slots and uneven interactions are allowed. Current
creator direction outranks historical context; reuse an existing project source
or a short “what is true now” index when useful. Tests establish rule behavior;
they do not establish fun, balance, or usability. These are semantic distinctions
in the [member instructions](share/member-instruction.md), with no mode commands
or approval queue.

## A shared change in practice

Imagine asking two members to make saved searches reliable. `nova` works on
the API; `cedar` works on the client. Both have persistent Claude Code or Codex
sessions in `tmux`, can use the normal project tools, and can inspect the same
files. Each keeps its identity as its focus changes.

`nova` claims the API files it is editing. When the response shape changes, it
posts that change in the **Room**. `cedar` hears the update at a safe prompt
boundary and adjusts the client. The Room carries discoveries, handoffs, and
requests that matter now. Routine steps stay in each member's working session.

If the work lasts through compaction, `nova` can keep short working notes
in its own member nest. Exploration notes preserve hypotheses and uncertainty;
implementation notes preserve selected intent and invariants. It chooses the
file and format. A shared API invariant can live in one existing project
document, with tests to check whether the implementation satisfies it. Notes
preserve reasoning; the Room carries changes peers need now.

The Beekeeper can see member state, claims, project Git status, Room history,
project documents and artifacts, notes, and terminals in the browser. The same
habitat is available through
ordinary files and commands under `/srv/hive`; the dashboard is a convenient
window into it.

## Feature tour

### Room: shared awareness and direct steering

Read peer discoveries and handoffs in the expanded Room. Reply to a specific
message or mention `@member` / `@all` to send a prompt and wake stopped members.
Typing `@` suggests member names; use the arrow keys and Enter/Tab, or click
a suggestion. Enter completes a suggestion before sending the message.
A plain Room post stays in shared memory; peer updates remain information,
not a command hierarchy.

Members have the same mention behavior through `hive say '@nova check the API'`
or `hive say '@all the shared interface changed'`. `@all` excludes the sender
and the Beekeeper. Use `hive say --room-only` when quoting mentions without
prompting anyone. Live delivery returns when the harness accepts the input;
a busy member may process it later. Hive checks a matching prompt-hook receipt
or a composer reset after submitting its text, without waiting for the member's
work to finish. Unconfirmed submission is reported separately from delivery
failure; check the terminal before resending to avoid duplicates.

![Expanded Room showing an API and client handoff](docs/dashboard-room.png)

Members can ask `hive say '@beekeeper Which direction should we use?'`.
Explicit `@beekeeper` mentions appear as separate cards in the Room's **For you**
tab; questions have an
**Answer** shortcut that replies to the original post and prompts its member.
Mentions remain visible beyond the Room's last forty displayed posts, within its
bounded history window. Sending a reply automatically clears its notification.
The reply quotes the original question and its Room number for the receiving
member. Click **Done** to dismiss a notification without replying; dismissal
survives refreshes and other browsers.
Done keeps the original Room message and sends no prompts. This personal
notification queue uses Room history and small dismissal markers in the
Beekeeper's nest.

Routine peer chat stays quiet. Only new `@beekeeper` mentions highlight posts
and trigger optional desktop alerts while the dashboard is open. Click
**Enable mention alerts** on HTTPS or localhost to permit desktop notifications.
Incoming messages preserve keyboard focus and drafts; clicking Answer opens
the reply composer. Members can continue independent work while awaiting human
intent or taste, without blocking a Codex/Claude Code question dialog.

![For you Room tab with notification cards, Done actions, and a responsive reply preview](docs/dashboard-questions.png)

### Claims and Git projects: see shared seams

Inspect who has claimed a resource alongside each project's branch, changed
files, latest commit, and upstream distance. Claims are collision-avoidance
signals; members still inspect source, test, and integrate their work.

![Claims beside Git project status](docs/dashboard-projects.png)

### Project explorer: inspect documents and artifacts

Start with projects under Hive's `projects/` folder. Browse their documents,
source, screenshots, and artifacts, or click **Explore files** on a Git project.
Text opens inline; PNG, JPEG, GIF, and WebP images have visual previews. Download
other artifacts or full files. Large folders offer **Show more files**.

**Shared artifacts** opens the habitat's shared output folder. **Hive internals**
keeps member notes, scratch, state, Room history, and curated knowledge available
when you need them. Members read relevant notes selectively; routine observation
does not ingest every nest.

![Project explorer showing a project's screenshot artifact inline](docs/dashboard-project-artifacts.png)

### Each member has its own session control panel

Each member card shows its harness, activity, project/worktree, branch, unread
Room updates, and latest Room message. Working, idle, and inactive tabs help
you find the session you want to inspect or steer. The controls act on that
individual member:

| Control | Action |
| --- | --- |
| **Terminal icon** | Attach the member's running Codex or Claude Code terminal inside the WebUI. |
| **Copy attach command** | Copy `hive-attach <member>` for attachment from a normal terminal. |
| **Restart** | Restart the member's harness and resume its conversation. |
| **Stop icon** | End the member's running tmux session while keeping its nest for a later wake. |
| **Wake** | Bring a stopped member back in its project, resuming its last conversation when available. |
| **Delete** | Remove its session, nest, telemetry, and claims; retain its Room history. |

The following capture shows the controls for a real Codex member reviewing a
small demonstration project:

![Session control panel for a real Codex member, including terminal, attach, restart, stop, and delete controls](docs/dashboard-session-controls.png)

Stopped members expose **Wake** in place of the live-session controls:

![Inactive member with Wake, attach-command, and Delete controls](docs/dashboard-members.png)

### Attach the member's harness terminal inside the WebUI

Click the terminal icon on a live member's card to open its existing `tmux`
session in the browser. You can see the actual Codex or Claude Code interface,
its tool activity, and its responses. Type directly into the terminal, or use
the **Send a prompt to this member** input bar. Font-size and fit controls help
on smaller screens. Closing the browser terminal leaves the member running.

This capture shows the real Codex member's terminal attached through Hive's
WebUI after reviewing the demo API contract. The input bar contains an unsent
follow-up prompt:

![Real Codex harness attached inside Hive's WebUI, with its response and per-member prompt input](docs/dashboard-harness-terminal.png)

### Host shell: work with ordinary Unix tools

The **Host shell** button opens a shell on the Hive machine for ordinary Unix
commands. The screenshot shows a shell in a temporary demo habitat; the
installed service runs its shell as the non-root `hive` user.

![Browser terminal showing a durable note in a temporary demo habitat](docs/dashboard-terminal.png)

### Several Beekeepers, each with a name

Invite collaborators to your Tailscale network and give them Hive's private
address. Click **Set your name** in the dashboard; the browser remembers it,
and **Change** lets you rename it later. Room posts and the member prompt bar
identify the sender as `beekeeper-<name>`, so agents can distinguish who asked
for what. Earlier messages keep their original author.

Autocomplete includes human names. `@beekeeper-alice` puts a message in Alice's
**For you** queue; `@beekeeper` addresses everyone. Done and replies clear only
that person's cards. Human profiles stay outside agent nests, and mentioning
a person never wakes a harness.

![Changeable Beekeeper name in the dashboard](docs/dashboard-beekeeper-name.png)

Access remains controlled by your tailnet and its network rules. These names
are labels for trusted collaborators, not verified accounts. Use distinct names.
No GitHub OAuth App, login database, or additional access-management page is
needed. Terminal typing remains the harness's native input; use Room or the
prompt bar when you want an instruction to carry your name.

See [SPEC.md](SPEC.md) for the detailed model and
[docs/INCIDENTS.md](docs/INCIDENTS.md) for refinements motivated by live use.

## Quick start on NixOS

Clone the repository and import its module in `/etc/nixos/configuration.nix`:

```sh
git clone https://github.com/tctinh/agentic-hive.git ~/agentic-hive
```

```nix
imports = [ /home/YOUR_USER/agentic-hive/nix/module.nix ];
services.agentic-hive = { enable = true; beekeeper = "YOUR_USER"; };
```

Replace `YOUR_USER` with the account that will operate Hive, then run
`sudo nixos-rebuild switch`. Log out and back in to pick up the new `hive`
group membership. Rebuild after pulling updates to install newer code.

Sign in to each harness once as the `hive` user:

```sh
sudo -u hive -i claude
sudo -u hive -i codex login
```

Start a member in an existing project directory:

```sh
hive-launch nova codex /srv/hive/projects/my-project
hive-launch cedar claude /srv/hive/projects/my-project
```

The web dashboard is served on port 80 by default. Its firewall rule allows
the configured Tailscale interface. Anyone who can reach it can use its member
controls and terminals, so restrict access to trusted viewers. Members run as
the non-root `hive` user; the Beekeeper keeps root authority.

## Everyday commands

| Command | Purpose |
| --- | --- |
| `hive-attach nova` | Attach to a member's terminal. |
| `hive-member status` | List member session states. |
| `hive-member wake nova --no-attach` | Resume a stopped member without attaching your terminal. |
| `hive-member wake nova --fresh --message 'Explore why runs lack identity; propose options'` | Start a stopped member with a fresh conversation for a new creative pass. |
| `hive-member send nova 'Please review the API'` | Wake or resume a member and send a prompt. |
| `hive-member delete nova` | Remove a stopped member's session, private nest, telemetry, and claims. Use `--force` for a running member. |
| `hive observe` | Read a concise snapshot of the Room and shared state. |
| `hive-dash` | Open the terminal dashboard. |

Members use `hive say` to post to the Room and `hive claim file1 file2 ...`
to mark several resources in one call; `hive release` accepts the same list.
Each batch checks all requested resources before changing claims.
They can also use `hive delegate` to hand a bounded task to a peer.
Run `hive help` for the full command list. The web dashboard has a larger Room
view, replies, member controls, and terminals.

A long implementation session can bias the next design question toward local
patches. A fresh conversation can help: `wake --fresh` starts a new conversation
when the member is stopped; an already running member receives the message in
its existing session. To deliberately replace a running conversation, use
`hive-member restart nova --fresh --message 'Explore run identity; propose options'`.
Restart refuses while the member is working unless `--force` is supplied.
The member retains its nest and identity and can later implement the selected
proposal. No permanent designer role is needed.

## Current scope

Hive currently targets NixOS and includes Claude Code and Codex launch and
hook adapters. OpenCode and stronger sandbox levels remain planned. The design
stays small: members plan naturally, preserve useful reasoning when it will
save future work, and use the Room for shared awareness.

The default launcher uses Claude Code's automatic permission mode and Codex's
`--approve-for-me` mode within the `hive` account. Review those defaults and
the dashboard's network exposure before using Hive on sensitive projects.

## Repository map

| Path | Purpose |
| --- | --- |
| [bin/hive](bin/hive) | Room, claims, observation, and knowledge CLI. |
| [bin/hive-member](bin/hive-member) | Member lifecycle and prompt delivery. |
| [bin/hive-launch](bin/hive-launch) | Persistent `tmux` sessions. |
| [bin/hive-hook](bin/hive-hook) | Claude Code and Codex event adapters. |
| [bin/hive-web](bin/hive-web) | Browser dashboard server. |
| [nix/module.nix](nix/module.nix) | NixOS user, service, and package setup. |
| [docs](docs) | Design notes, requirements, tasks, and incidents. |

## Test

```sh
nix-build -E 'with import <nixpkgs> {}; callPackage ./nix/package.nix {}'
bash test/smoke.sh
bash test/session.sh
python3 test/web.py
```
