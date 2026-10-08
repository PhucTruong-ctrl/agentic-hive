import { spawn } from 'node:child_process';
// Harness from HIVE_HARNESS (launcher sets); fallback 'omp' only if absent.
export default function (pi) {
  const harness = process.env.HIVE_HARNESS || 'omp';
  const hookPath = process.env.HIVE_BIN_DIR ? `${process.env.HIVE_BIN_DIR}/hive-hook` : 'hive-hook';

  const fireAndAwait = async (name, payload) => {
    if (!process.env.HIVE_MEMBER) return { additionalContext: '' };
    return new Promise((resolve) => {
      let timer = null;
      try {
        const child = spawn(hookPath, [harness, name], {
          cwd: payload.cwd || process.cwd(),
          timeout: 2000,
        });
        child.stdin.on('error', () => {});
        child.stdin.write(JSON.stringify({ ...payload, cwd: payload.cwd || process.cwd(), prompt: payload.prompt, tool_name: payload.tool_name, session_id: payload.session_id || '' }));
        child.stdin.end();
        let out = '';
        child.stdout.on('data', d => out += d);
        child.on('close', () => {
          clearTimeout(timer);
          try {
            const parsed = JSON.parse(out);
            resolve({ additionalContext: parsed?.hookSpecificOutput?.additionalContext || '' });
          } catch (_) {
            resolve({ additionalContext: '' });
          }
        });
        timer = setTimeout(() => resolve({ additionalContext: '' }), 2200);
      } catch (_) {
        clearTimeout(timer);
        resolve({ additionalContext: '' });
      }
    });
  };

  pi.on('session_start', () => { fireAndAwait('SessionStart', { cwd: process.cwd() }).catch(() => {}); });
  pi.on('before_agent_start', (evt) => { fireAndAwait('UserPromptSubmit', { cwd: process.cwd(), prompt: evt.prompt || '', session_id: '' }).catch(() => {}); return null; });
  pi.on('agent_before_settle', async () => { const r = await fireAndAwait('Stop', { cwd: process.cwd() }); return r; });
  pi.on('turn_end', (input) => { fireAndAwait('Stop', { cwd: process.cwd(), prompt: '' }).catch(() => {}); });
  pi.on('tool_result', async (input) => {
    const r = await fireAndAwait('PostToolUse', { cwd: process.cwd(), prompt: input?.prompt || '', tool_name: input?.toolName || input?.tool || '' });
    // additionalContext is omp-documented; pi uses its own message API
    if (harness === 'pi') {
      if (typeof pi.sendMessage === 'function') {
        pi.sendMessage(r.additionalContext || '');
      }
      return {};
    }
    return r;
  });
  pi.on('session_shutdown', () => { fireAndAwait('SessionEnd', { cwd: process.cwd() }).catch(() => {}); });
};
