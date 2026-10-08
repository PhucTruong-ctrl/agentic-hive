import { createRunner } from './hive-runner.js';

// OpenCode V1: text is in chat.message's output.parts; injection mutates output.
export const Plugin = async ({ directory }) => {
  const cwd = directory || process.cwd();
  const runner = createRunner(process.env.HIVE_HARNESS || 'opencode', cwd);
  let activeSession = '';
  const childSessions = new Set();
  const payload = (sessionID, extra = {}) => ({ cwd, session_id: sessionID || activeSession, ...extra });
  const safely = work => async (...args) => {
    try { return await work(...args); } catch { /* Leave failed deliveries pending. */ }
  };
  const isActive = sessionID => !activeSession || !sessionID || sessionID === activeSession;
  return {
    event: safely(async ({ event }) => {
      if (event.type === 'session.created') {
        const info = event.properties?.info;
        if (!info?.id) return;
        if (info.parentID) { childSessions.add(info.id); return; }
        activeSession = info.id;
        await runner.telemetry('SessionStart', payload(activeSession));
      } else if (event.type === 'session.idle' && isActive(event.properties?.sessionID)) {
        await runner.telemetry('Stop', payload(event.properties?.sessionID));
      }
    }),
    'chat.message': safely(async (input, output) => {
      if (childSessions.has(input.sessionID)) return;
      // Native session switching can select an existing conversation without
      // creating a new session. The next primary user message selects its ID.
      activeSession = input.sessionID || activeSession;
      const prompt = (output.parts || []).filter(part => part.type === 'text' && !part.synthetic)
        .map(part => part.text).join('\n');
      await runner.telemetry('UserPromptSubmit', payload(input.sessionID, { prompt }));
    }),
    'experimental.chat.system.transform': safely(async (input, output) => {
      if (!isActive(input.sessionID)) return;
      activeSession = input.sessionID || activeSession;
      await runner.deliver('Context', payload(input.sessionID), context => {
        output.system ||= [];
        output.system.push(context);
      });
    }),
    'tool.execute.after': safely(async (input, output) => {
      if (!isActive(input.sessionID)) return;
      await runner.deliver('PostToolUse', payload(input.sessionID, { tool_name: input.tool }), context => {
        output.output = (output.output || '') + '\n\n' + context;
      });
    }),
  };
};
