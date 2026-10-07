# `hive-install` — portable Agentic Hive installer

`install/hive-install` is the non-NixOS equivalent of `nix/module.nix`. It
installs the Hive commands and shared assets under a prefix, creates the
non-root `hive` account and habitat root, and writes the systemd units, sudoers
rule, login profile, Claude Code hooks and tmux drop-in. All OS-specific
knowledge lives here; `bin/` and `share/` stay distro-agnostic.

```sh
sudo install/hive-install --beekeeper alice
sudo install/hive-install --beekeeper alice --port 80 --address 0.0.0.0
sudo install/hive-install --beekeeper alice --uninstall
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--beekeeper <user>` | — (required) | Human account added to group `hive` and granted NOPASSWD sudo to the hive user. |
| `--hive-user <name>` | `hive` | Habitat account to create. |
| `--hive-group <name>` | `hive` | Habitat group to create. |
| `--hive-root <dir>` | `/srv/hive` | Mutable habitat root (setgid 2770 + default ACL). |
| `--prefix <dir>` | `/usr/local` | Prefix for commands (`bin`) and assets (`share/agentic-hive`). |
| `--port <n>` | `8080` | Dashboard port. Below 1024 adds `CAP_NET_BIND_SERVICE` to `hive-web.service`. |
| `--address <addr>` | `127.0.0.1` | Dashboard bind address. Non-loopback drives member terminals and a host shell as the hive user, so a warning is printed. |
| `--no-web` | off | Skip `hive-web.service`. |
| `--no-hooks` | off | Skip `/etc/claude-code/managed-settings.json`. |
| `--no-deps` | off | Skip package installation (the package list is still printed). |
| `--dry-run` | off | Print every action as `would ...`, change nothing. |
| `--uninstall` | off | Remove exactly what a prior install created. |
| `-h`, `--help` | — | Usage. |

## Staging with `DESTDIR`
`DESTDIR` writes every absolute path under that prefix and skips user/group
creation, tmpfiles application, `systemctl` and package installation, so an
unprivileged user can build a staged tree:
`DESTDIR=/tmp/stage install/hive-install --beekeeper alice`.

## Adding a package-manager family
Each family is one row in `family_row()`: `<install command>|<packages>`.
Detection (`pkg_family()`) is by which binary exists; add one case arm with the
family's package names — no other code changes.
