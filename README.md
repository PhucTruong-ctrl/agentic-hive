# Agentic Hive v0.1

A persistent NixOS/Unix habitat for coding-agent sessions. See `SPEC.md`.

```
bin/hive               Hive Core CLI (Room, claims, cursors, knowledge search)
bin/hive-hook          harness adapter: `hive-hook claude|codex <event>` (SessionStart/UserPromptSubmit/PostToolUse/Stop/SessionEnd)
bin/hive-launch        tmux launcher: one session per member, runs as the `hive` user
bin/hive-dash          read-only terminal dashboard (SPEC §18): members, claims, Room, host
bin/hive-web           browser dashboard, member control, Room chat and terminal (port 80, Tailscale only)
share/dashboard.html   the page hive-web serves
bin/hive-attach        jump into a member's tmux session (picker, prefix match, -r read-only)
bin/hive-member        wake (resume last conversation) / restart / kill / status for members
bin/hive-session       compatibility alias for hive-member
bin/hive-statusline    Claude Code status line for members; records account quota for the dashboards
share/member-instruction.md   the §13 instruction, appended to Claude's system prompt
nix/module.nix         NixOS module (the "tree")
nix/package.nix        Hive Core package
test/smoke.sh          smoke test against a throwaway HIVE_ROOT
```

## Install (Beekeeper)

Clone the repository on the NixOS host:

```sh
git clone git@github.com:tctinh/agentic-hive.git ~/agentic-hive
```

In `/etc/nixos/configuration.nix`, import the module from the checkout:

```nix
imports = [ ./hardware-configuration.nix /home/YOUR_USER/agentic-hive/nix/module.nix ];
services.agentic-hive = { enable = true; beekeeper = "YOUR_USER"; };
```

Replace `YOUR_USER` with the Beekeeper account. Run `sudo nixos-rebuild switch`,
then log out and back in to pick up the new `hive` group membership. Rebuild
again after updating the checkout to install newer dashboard and CLI code.

One-time harness login for the `hive` user:

```
sudo -u hive -i claude      # /login, then exit
sudo -u hive -i codex login
```

## Use

```
hive-launch claude-opus-game claude /srv/hive/projects/game   # start or attach
hive-launch --list
hive-member status | wake <m> [--fresh] [--message <text>] | restart <m> [--force] [--message <text>] | kill <m> [--force]
hive-member send <m> <message>                                 # wake/resume and prompt a member
hive message <member> <message...>                               # agent-facing send, recorded in Room
hive-attach [member]        # or -r to watch read-only; detach with Ctrl-b d; mouse-drag copies to your clipboard
hive observe                                                    # read-only view
hive delegate <target> --task <msg> [--worktree <dir>] [--branch <br>] [--claim <res>]  # delegate subtask
hive delegate done [summary]                                    # complete delegated subtask & release claims
hive-dash                                                       # live dashboard (q quits); --once for a snapshot
# web dashboard: http://<tailscale-ip>/  (services.agentic-hive.web.{enable,port,openFirewallOn})
# Web dashboard includes member terminals, a host shell, Room chat and lifecycle controls.
```

Everything is plain files under `/srv/hive`; `cat ROOM.md` always works.

The browser dashboard shows Members alongside Room, and Claims alongside Recent
commits in a second view. Member
cards are grouped as Working, Idle or Inactive, show their latest Room post, and
offer icon controls for Terminal, Wake, Restart, Kill and copying a `hive-attach` command as
appropriate. Room posts show member identity and status, highlight mentions,
and support replies. Mention `@member` to wake and message one member or `@all`
to reach every joined agent member. The Host shell runs as the non-root
`hive` account. Browser control is available to anyone with access to the
dashboard address, so keep its firewall scope limited to trusted viewers.

Hive launches Claude with `--permission-mode auto` and Codex with
`--approve-for-me --add-dir /srv/hive`. These defaults apply to new launches,
resumed sessions, and restarts. Agents still run as the non-root `hive` user;
the agent harness may automatically approve actions within that account's
access. Restart an already running member to apply the new flags.

## Room file format

Each entry is preceded by an invisible marker used for deterministic parsing:

```
<!-- hive:entry gen=42 member=claude-opus-game -->
## 2026-09-30T18:42:17+07:00 — claude-opus-game

body

Generation: 42
```

## Not built yet (by design, SPEC §2.6 / §23)

- OpenCode adapter. Codex hooks are installed by `hive-launch` into `~hive/.codex/hooks.json` (not yet validated live).
- Sandbox levels 1–4 helpers — only `bubblewrap` is installed.

## Test

```
nix-build -E 'with import <nixpkgs> {}; callPackage ./nix/package.nix {}'
test/smoke.sh
bash test/session.sh
python3 test/web.py
```
