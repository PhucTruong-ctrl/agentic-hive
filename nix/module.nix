# Agentic Hive — NixOS module (the "tree", SPEC §4).
#
# Declares the host physics only: the `hive` user, /srv/hive ownership,
# baseline tools, Hive Core, and the Claude Code adapter hooks. Room, claims,
# members and knowledge are mutable habitat state and never live here.
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.services.agentic-hive;
  hookCmd = event: "${cfg.package}/bin/hive-claude-hook ${event}";
  hook = event: [ { hooks = [ { type = "command"; command = hookCmd event; } ]; } ];
in
{
  options.services.agentic-hive = {
    enable = lib.mkEnableOption "Agentic Hive habitat";

    beekeeper = lib.mkOption {
      type = lib.types.str;
      description = "Human owner account; added to the hive group for read/write habitat access.";
    };

    root = lib.mkOption {
      type = lib.types.path;
      default = "/srv/hive";
      description = "Mutable habitat root.";
    };

    package = lib.mkOption {
      type = lib.types.package;
      default = pkgs.callPackage ./package.nix { };
      description = "Hive Core package (protected in the Nix store).";
    };

    harnesses = lib.mkOption {
      type = lib.types.listOf lib.types.package;
      default = with pkgs; [
        claude-code
        codex
      ];
      description = "Agent harnesses available to members.";
    };

    claudeHooks = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = ''
        Install the Hive adapter as Claude Code managed-settings hooks
        (/etc/claude-code/managed-settings.json). The hooks are no-ops for any
        session without HIVE_MEMBER set, including the Beekeeper's own.
      '';
    };
  };

  config = lib.mkIf cfg.enable {
    users.groups.hive = { };

    users.users.hive = {
      isNormalUser = true;
      group = "hive";
      home = "/home/hive";
      createHome = true;
      description = "Agentic Hive members";
      # No wheel, no password: the Beekeeper enters via sudo or SSH keys.
    };

    users.users.${cfg.beekeeper}.extraGroups = [ "hive" ];

    # Let the Beekeeper launch/attach member sessions without a root shell.
    security.sudo.extraRules = [
      {
        users = [ cfg.beekeeper ];
        runAs = "hive";
        commands = [
          {
            command = "ALL";
            options = [ "NOPASSWD" ];
          }
        ];
      }
    ];

    # Setgid + default ACL: everything created in the habitat stays
    # group-writable for hive and the Beekeeper regardless of umask.
    systemd.tmpfiles.rules = [
      "d ${cfg.root} 2770 hive hive -"
      "a+ ${cfg.root} - - - - default:group:hive:rwX,group:hive:rwX,default:user:hive:rwX"
    ];

    systemd.services.agentic-hive-init = {
      description = "Initialize Agentic Hive habitat (idempotent)";
      wantedBy = [ "multi-user.target" ];
      after = [ "systemd-tmpfiles-setup.service" ];
      serviceConfig = {
        Type = "oneshot";
        User = "hive";
        Group = "hive";
        UMask = "0002";
        Environment = "HIVE_ROOT=${cfg.root}";
        ExecStart = "${cfg.package}/bin/hive init";
      };
    };

    environment.etc."claude-code/managed-settings.json" = lib.mkIf cfg.claudeHooks {
      text = builtins.toJSON {
        hooks = {
          SessionStart = hook "SessionStart";
          UserPromptSubmit = hook "UserPromptSubmit";
          PostToolUse = [
            {
              matcher = "*";
              hooks = [ { type = "command"; command = hookCmd "PostToolUse"; } ];
            }
          ];
          Stop = hook "Stop";
          SessionEnd = hook "SessionEnd";
        };
      };
    };

    environment.variables.HIVE_ROOT = cfg.root;

    programs.direnv = {
      enable = true;
      nix-direnv.enable = true;
    };

    environment.systemPackages =
      [ cfg.package ]
      ++ cfg.harnesses
      ++ (with pkgs; [
        tmux
        git
        git-lfs
        ripgrep
        fd
        fzf
        tree
        jq
        curl
        wget
        rsync
        lsof
        strace
        procps
        psmisc
        iproute2
        btop
        ncdu
        inotify-tools
        acl
        bubblewrap
        xvfb
        python3
      ]);
  };
}
