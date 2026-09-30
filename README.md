# Agentic Hive v0.1

A persistent NixOS/Unix habitat for coding-agent sessions. See `SPEC.md`.

```
bin/hive               Hive Core CLI (Room, claims, cursors, knowledge search)
bin/hive-hook          harness adapter: `hive-hook claude|codex <event>` (SessionStart/UserPromptSubmit/PostToolUse/Stop/SessionEnd)
bin/hive-launch        tmux launcher: one session per member, runs as the `hive` user
bin/hive-dash          read-only terminal dashboard (SPEC §18): members, claims, Room, host
bin/hive-web           the same dashboard over HTTP (systemd service hive-web, port 80, Tailscale only)
share/dashboard.html   the page hive-web serves
share/member-instruction.md   the §13 instruction, appended to Claude's system prompt
nix/module.nix         NixOS module (the "tree")
nix/package.nix        Hive Core package
test/smoke.sh          smoke test against a throwaway HIVE_ROOT
```

## Install (Beekeeper)

In `/etc/nixos/configuration.nix`:

```nix
imports = [ ./hardware-configuration.nix /home/tctinh/agentic-hive/nix/module.nix ];
services.agentic-hive = { enable = true; beekeeper = "tctinh"; };
```

Then `sudo nixos-rebuild switch`, and log out/in (new `hive` group membership).

One-time harness login for the `hive` user:

```
sudo -u hive -i claude      # /login, then exit
sudo -u hive -i codex login
```

## Use

```
hive-launch claude-opus-game claude /srv/hive/projects/game   # start or attach
hive-launch --list
sudo -u hive -i tmux attach -t hive-claude-opus-game
hive observe                                                    # read-only view
hive-dash                                                       # live dashboard (q quits); --once for a snapshot
# web dashboard: http://<tailscale-ip>/  (services.agentic-hive.web.{enable,port,openFirewallOn})
```

Everything is plain files under `/srv/hive`; `cat ROOM.md` always works.

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
```
