import { spawn } from 'node:child_process';

// Serialize delivery per agent and acknowledge only after context injection.
export function createRunner(harness, cwd) {
  let queue = Promise.resolve();
  const serialize = work => {
    const next = queue.then(work);
    queue = next.catch(() => {});
    return next;
  };
  const run = (event, payload, telemetryOnly = false) => {
    if (!process.env.HIVE_MEMBER) return Promise.resolve({});
    return new Promise(resolve => {
      const hook = process.env.HIVE_BIN_DIR ? process.env.HIVE_BIN_DIR + '/hive-hook' : 'hive-hook';
      let child, timer;
      let output = '';
      let settled = false;
      const finish = value => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve(value);
      };
      try {
        child = spawn(hook, [harness, event], {
          cwd: payload.cwd || cwd,
          env: { ...process.env, HIVE_HOOK_TELEMETRY_ONLY: telemetryOnly ? '1' : '0', HIVE_HOOK_DEFER_DELIVERY: '1' },
          stdio: ['pipe', 'pipe', 'ignore'],
        });
        child.on('error', () => finish({}));
        child.stdin.on('error', () => {});
        child.stdout.on('data', data => {
          output += data;
          if (output.length > 1024 * 1024) { child.kill('SIGKILL'); finish({}); }
        });
        child.on('close', code => {
          if (code !== 0 || !output.trim()) return finish({});
          try {
            const value = JSON.parse(output);
            const context = value?.hookSpecificOutput?.additionalContext;
            const generation = value?.hiveDelivery?.generation;
            finish({ context: typeof context === 'string' ? context : '',
              generation: Number.isSafeInteger(generation) && generation >= 0 ? generation : null });
          } catch { finish({}); }
        });
        timer = setTimeout(() => { child.kill('SIGKILL'); finish({}); }, 2500);
        child.stdin.end(JSON.stringify({ ...payload, cwd: payload.cwd || cwd }));
      } catch { finish({}); }
    });
  };
  return {
    telemetry: (event, payload) => serialize(() => run(event, payload, true)),
    deliver: (event, payload, inject) => serialize(async () => {
      const response = await run(event, payload);
      const result = response.context ? await inject(response.context) : undefined;
      if (response.generation != null) {
        await run('Acknowledge', { ...payload, delivery_generation: response.generation });
      }
      return result;
    }),
  };
}
