# share/harness.sh — per-harness fact table for Agentic Hive.
#
# Sourced, never executed: no shebang, no set options.
#   harness_fact <harness> <fact>  value + newline; unknown harness or fact
#                                  prints nothing and returns non-zero —
#                                  never guess, never default.
#   harness_list                   supported harnesses, sorted, one per line.
# facts: exe resume hook_config hook_module hook_module_src out prompt event:<HiveEvent>

harness_list() {
  printf '%s\n' claude cline codex cursor letta omp openhands opencode pi qwen
}

harness_fact() {
  case $2 in
    # The binary Hive runs; liveness matches it against /proc/<pid>/comm,
    # which is not always the harness name.
    exe)
      case $1 in
        cursor) printf '%s\n' agent ;;
        claude|codex|qwen|letta|openhands|cline|omp|pi|opencode) printf '%s\n' "$1" ;;
        *) return 1 ;;
      esac ;;
    # argv word the stored session id is appended to as its own argument;
    # empty would mean no resume by id. codex is a bare subcommand, rest flags.
    resume)
      case $1 in
        codex) printf '%s\n' resume ;;
        claude|qwen|cursor|openhands) printf '%s\n' --resume ;;
        letta) printf '%s\n' --conversation ;;
        omp) printf '%s\n' --resume ;;
        pi|opencode) printf '%s\n' --session ;;
        cline) printf '%s\n' --id ;;
        *) return 1 ;;
      esac ;;
    # Settings/hooks file relative to $HOME; empty = no single file (claude
    # hooks are host-registered, cline uses a hooks directory). openhands'
    # user-level file is real but a fallback: the SDK's HookConfig.load
    # prefers {working_dir}/.openhands/hooks.json, then ~/.openhands/hooks.json
    # (software-agent-sdk openhands/sdk/hooks/config.py).
    hook_config)
      case $1 in
        codex) printf '%s\n' .codex/hooks.json ;;
        qwen) printf '%s\n' .qwen/settings.json ;;
        letta) printf '%s\n' .letta/settings.json ;;
        cursor) printf '%s\n' .cursor/hooks.json ;;
        openhands) printf '%s\n' .openhands/hooks.json ;;
        claude|cline) printf '\n' ;;
        omp|pi|opencode) printf '\n' ;;
        *) return 1 ;;
      esac ;;
    hook_module)
      case $1 in
        omp) printf '%s\n' .omp/agent/hooks/pre/hive.js ;;
        pi) printf '%s\n' .pi/agent/extensions/hive.js ;;
        opencode) printf '%s\n' .config/opencode/plugins/hive.js ;;
        *) return 1 ;;
      esac ;;
    hook_module_src)
      case $1 in
        omp|pi) printf '%s\n' hive-bridge/pi-on.js ;;
        opencode) printf '%s\n' hive-bridge/opencode.js ;;
        *) return 1 ;;
      esac ;;
    # shape hive-hook emits
    out)
      case $1 in
        claude|codex|qwen|letta|cursor) printf '%s\n' claude ;;
        openhands) printf '%s\n' top ;;
        cline) printf '%s\n' mod ;;
        omp|pi|opencode) printf '%s\n' claude ;;
        *) return 1 ;;
      esac ;;
    # how the member instruction text is injected
    prompt)
      case $1 in
        claude|qwen) printf '%s\n' flag-append:--append-system-prompt ;;
        codex) printf '%s\n' config:developer_instructions ;;
        letta) printf '%s\n' flag-replace:--system-custom ;;
        cline) printf '%s\n' flag-replace:--system ;;
        cursor|openhands) printf '%s\n' hook ;;
        omp|pi) printf '%s\n' flag-append:--append-system-prompt ;;
        opencode) printf '%s\n' hook ;; # no CLI flag; SessionStart hook instead
        *) return 1 ;;
      esac ;;
    # Hive event -> vendor hook event name; empty = no vendor equivalent
    event:SessionStart)
      case $1 in
        cursor) printf '%s\n' sessionStart ;;
        openhands) printf '%s\n' session_start ;;
        cline) printf '%s\n' TaskStart ;;
        claude|codex|qwen|letta) printf '%s\n' SessionStart ;;
        omp|pi) printf '%s\n' session_start ;;
        opencode) printf '%s\n' session.created ;;
        *) return 1 ;;
      esac ;;
    event:UserPromptSubmit)
      case $1 in
        cursor) printf '%s\n' beforeSubmitPrompt ;;
        openhands) printf '%s\n' user_prompt_submit ;;
        claude|codex|qwen|letta|cline) printf '%s\n' UserPromptSubmit ;;
        omp|pi) printf '%s\n' before_agent_start ;;
        opencode) printf '%s\n' chat.message ;;
        *) return 1 ;;
      esac ;;
    event:PostToolUse)
      case $1 in
        cursor) printf '%s\n' postToolUse ;;
        openhands) printf '%s\n' post_tool_use ;;
        claude|codex|qwen|letta|cline) printf '%s\n' PostToolUse ;;
        omp|pi) printf '%s\n' tool_result ;;
        opencode) printf '%s\n' tool.execute.after ;;
        *) return 1 ;;
      esac ;;
    event:Stop)
      case $1 in
        cursor) printf '%s\n' stop ;;
        openhands) printf '%s\n' stop ;;
        cline) printf '\n' ;;
        claude|codex|qwen|letta) printf '%s\n' Stop ;;
        omp|pi) printf '%s\n' agent_end ;;
        opencode) printf '%s\n' session.idle ;;
        *) return 1 ;;
      esac ;;
    event:SessionEnd)
      case $1 in
        cursor) printf '%s\n' sessionEnd ;;
        openhands) printf '%s\n' session_end ;;
        cline) printf '\n' ;;
        claude|codex|qwen|letta) printf '%s\n' SessionEnd ;;
        omp|pi) printf '%s\n' session_shutdown ;;
        opencode) printf '\n' ;;
        *) return 1 ;;
      esac ;;
    *) return 1 ;;
  esac
}
