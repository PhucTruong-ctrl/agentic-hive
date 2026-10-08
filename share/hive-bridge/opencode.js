import { spawn } from 'node:child_process';
// Harness from HIVE_HARNESS (launcher sets); fallback 'opencode' only if absent.
export const Plugin = async ({ project, client, $ }) => ({
  event: async (input, output) => {
    // Notification-only telemetry; no injection available at session.created/session.idle.
    if (!process.env.HIVE_MEMBER) return;
    const ev = input?.event?.type || input?.event;
    if (ev === 'session.created' || ev === 'session.idle') {
      try {
        const harness = process.env.HIVE_HARNESS || 'opencode'; // fallback when var absent
        const hookPath = process.env.HIVE_BIN_DIR ? `${process.env.HIVE_BIN_DIR}/hive-hook` : 'hive-hook';
        const child = spawn(hookPath, [harness, ev], { timeout: 2000, cwd: process.cwd() });
        child.stdin.write(JSON.stringify({ cwd: process.cwd(), session_id: '' })); child.stdin.end();
      } catch (_) {}
    }
  },
  'chat.message': async (input) => {
    if (!process.env.HIVE_MEMBER) return;
    const harness = process.env.HIVE_HARNESS || 'opencode';
    const hookPath = process.env.HIVE_BIN_DIR ? `${process.env.HIVE_BIN_DIR}/hive-hook` : 'hive-hook';
    try {
      const child = spawn(hookPath, [harness, 'UserPromptSubmit'], { timeout: 2000, cwd: process.cwd() });
      child.stdin.write(JSON.stringify({ cwd: process.cwd(), prompt: input?.message || '', session_id: '' })); child.stdin.end();
    } catch (_) {}
  },
  'experimental.chat.system.transform': async (input, output) => {
    if (!process.env.HIVE_MEMBER) return;
    try {
      const harness = process.env.HIVE_HARNESS || 'opencode';
      const hookPath = process.env.HIVE_BIN_DIR ? `${process.env.HIVE_BIN_DIR}/hive-hook` : 'hive-hook';
      const child = spawn(hookPath, [harness, 'UserPromptSubmit'], { timeout: 2000, cwd: process.cwd() });
      child.stdin.write(JSON.stringify({ cwd: process.cwd(), prompt: input?.message || '', session_id: '' })); child.stdin.end();
      let out = '';
      child.stdout.on('data', d => out += d);
      await new Promise(r => setTimeout(r, 2100));
      try {
        const parsed = JSON.parse(out);
        const ctx = parsed?.hookSpecificOutput?.additionalContext || '';
        if (ctx) output.system = output.system || []; output.system.push(ctx);
      } catch (_) {}
    } catch (_) {}
  },
  'tool.execute.after': async (input, output) => {
    if (!process.env.HIVE_MEMBER) return;
    try {
      const harness = process.env.HIVE_HARNESS || 'opencode';
      const hookPath = process.env.HIVE_BIN_DIR ? `${process.env.HIVE_BIN_DIR}/hive-hook` : 'hive-hook';
      const child = spawn(hookPath, [harness, 'PostToolUse'], { timeout: 2000, cwd: process.cwd() });
      child.stdin.write(JSON.stringify({ cwd: process.cwd(), prompt: JSON.stringify(input), tool_name: input?.tool || '', session_id: '' })); child.stdin.end();
    } catch (_) {}
  },
});
// Note: SessionEnd has no documented event in opencode; omitted intentionally.
