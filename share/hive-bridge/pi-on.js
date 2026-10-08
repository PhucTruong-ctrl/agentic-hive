import { createRunner } from './hive-runner.js';

export default function (pi) {
  const harness = process.env.HIVE_HARNESS || 'omp';
  const runner = createRunner(harness, process.cwd());
  const payload = (ctx, extra = {}) => ({
    cwd: ctx?.cwd || process.cwd(),
    session_id: ctx?.sessionManager?.getSessionId() || '',
    ...extra,
  });
  const message = content => ({ customType: 'hive-room', content, display: true });
  const safely = work => async (...args) => {
    try { return await work(...args); } catch { /* No acknowledgement on failed injection. */ }
  };
  pi.on('session_start', safely(async (_event, ctx) => {
    await runner.deliver('SessionStart', payload(ctx), context => pi.sendMessage(message(context)));
  }));
  pi.on('before_agent_start', safely((event, ctx) =>
    runner.deliver('UserPromptSubmit', payload(ctx, { prompt: event.prompt || '' }),
      context => ({ message: message(context) }))));
  pi.on('tool_result', safely((event, ctx) =>
    runner.deliver('PostToolUse', payload(ctx, { tool_name: event.toolName || '' }), context => {
      if (harness === 'pi') {
        pi.sendMessage(message(context), { deliverAs: 'steer' });
        return undefined;
      }
      // OMP supports passive additionalContext; Pi uses its custom-message API.
      return { additionalContext: context };
    })));
  pi.on('agent_end', safely((_event, ctx) => runner.telemetry('Stop', payload(ctx))));
  pi.on('session_shutdown', safely((_event, ctx) => runner.telemetry('SessionEnd', payload(ctx))));
}
