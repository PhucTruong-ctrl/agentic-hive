// Exercise real hive-hook delivery against strict harness API contracts.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import bridge from '../share/hive-bridge/pi-on.js';
import { Plugin } from '../share/hive-bridge/opencode.js';
import { createRunner } from '../share/hive-bridge/hive-runner.js';

const repo = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const root = mkdtempSync(join(tmpdir(), 'hive-bridge-test-'));
Object.assign(process.env, { HIVE_ROOT: root, HIVE_SHARE: repo + '/share',
  HIVE_BIN_DIR: repo + '/bin', PATH: repo + '/bin:' + process.env.PATH });
const hive = (...args) => execFileSync(repo + '/bin/hive', args, { encoding: 'utf8' });
const telemetry = member => JSON.parse(readFileSync(join(root, 'telemetry/members', member + '.json')));
const cursor = member => Number(readFileSync(join(root, 'members', member, 'state/last-delivered-generation')));
const post = text => execFileSync(repo + '/bin/hive', ['say', text], {
  env: { ...process.env, HIVE_MEMBER: 'peer' }, encoding: 'utf8' });
const generation = () => Number(readFileSync(join(root, '.room-generation')));
let checks = 0;
const checked = label => { checks++; console.log('ok   ' + label); };

try {
  hive('init'); hive('join', 'peer');
  for (const harness of ['omp', 'pi']) {
    const member = harness + '-agent';
    hive('join', member);
    Object.assign(process.env, { HIVE_MEMBER: member, HIVE_HARNESS: harness });
    const handlers = {}, sent = [];
    const api = {
      on: (name, handler) => { handlers[name] = handler; },
      sendMessage: message => {
        assert.equal(typeof message, 'object');
        assert.equal(message.customType, 'hive-room');
        assert.equal(typeof message.content, 'string');
        assert.equal(message.display, true);
        sent.push(message);
      },
    };
    bridge(api);
    const ctx = { cwd: root, sessionManager: { getSessionId: () => harness + '-real-id' } };
    await handlers.session_start({}, ctx);
    assert(sent.some(message => message.content.includes('member: ' + member)));
    assert.equal(telemetry(member).session_id, harness + '-real-id');
    assert.equal(telemetry(member).cwd, root);
    checked(harness + ' startup injects context and records its real resume ID');

    post(harness + '-prompt-marker');
    const before = await handlers.before_agent_start({ prompt: 'actual user prompt' }, ctx);
    assert(before.message.content.includes(harness + '-prompt-marker'));
    assert.equal(cursor(member), generation());
    assert.equal(before.message.customType, 'hive-room');
    checked(harness + ' before_agent_start returns a valid context message');

    const previous = sent.length;
    const noChange = await handlers.tool_result({ toolName: 'bash' }, ctx);
    assert.equal(noChange, undefined);
    assert.equal(sent.length, previous);
    checked(harness + ' remains silent when no new context exists');

    post(harness + '-tool-marker');
    const tool = await handlers.tool_result({ toolName: 'bash' }, ctx);
    const delivered = harness === 'pi' ? sent.at(-1).content : tool.additionalContext;
    assert(delivered.includes(harness + '-tool-marker'));
    assert.equal(cursor(member), generation());
    checked(harness + ' tool context uses its supported injection API');

    if (harness === 'pi') {
      post('retry-after-injection-failure');
      const oldCursor = cursor(member);
      const send = api.sendMessage;
      api.sendMessage = () => { throw new Error('injection unavailable'); };
      await handlers.tool_result({ toolName: 'bash' }, ctx);
      assert.equal(cursor(member), oldCursor);
      api.sendMessage = send;
      await handlers.tool_result({ toolName: 'bash' }, ctx);
      assert(sent.at(-1).content.includes('retry-after-injection-failure'));
      assert.equal(cursor(member), generation());
      checked('failed injection leaves Room context pending for retry');
    } else {
      post('concurrent-tool-marker');
      const replies = await Promise.all([handlers.tool_result({ toolName: 'bash' }, ctx),
        handlers.tool_result({ toolName: 'read' }, ctx)]);
      assert.equal(replies.filter(reply => reply?.additionalContext?.includes('concurrent-tool-marker')).length, 1);
      checked('concurrent consuming callbacks deliver each Room update once');
    }
    await handlers.agent_end({}, ctx);
    assert.equal(telemetry(member).status, 'idle');
    await handlers.session_shutdown({}, ctx);
    assert.equal(telemetry(member).status, 'ended');
    checked(harness + ' lifecycle telemetry preserves the resume ID');
  }

  hive('join', 'open-agent');
  Object.assign(process.env, { HIVE_MEMBER: 'open-agent', HIVE_HARNESS: 'opencode' });
  post('opencode-initial-marker');
  const initialCursor = cursor('open-agent');
  const plugin = await Plugin({ directory: root });
  await plugin.event({ event: { type: 'session.created', properties: { info: { id: 'open-real-id' } } } });
  await plugin['chat.message']({ sessionID: 'open-real-id' }, {
    message: {}, parts: [{ type: 'text', text: 'real user text' }, { type: 'text', text: 'synthetic', synthetic: true }],
  });
  assert.equal(cursor('open-agent'), initialCursor);
  assert.equal(telemetry('open-agent').session_id, 'open-real-id');
  const receipt = readFileSync(join(root, 'members/open-agent/state/last-submitted-prompt'), 'utf8');
  assert(receipt.includes(createHash('sha256').update('real user text').digest('hex')));
  checked('OpenCode lifecycle/prompt telemetry never consumes Room updates');

  const system = { system: ['existing system text'] };
  await plugin['experimental.chat.system.transform']({ sessionID: 'open-real-id' }, system);
  assert.equal(system.system[0], 'existing system text');
  assert(system.system[1].includes('opencode-initial-marker'));
  assert(system.system[1].includes(readFileSync(repo + '/share/member-instruction.md', 'utf8').trim()));
  assert.equal(cursor('open-agent'), generation());
  checked('OpenCode system transform injects instructions and pending Room context');

  post('opencode-tool-marker');
  const tool = { output: 'original tool output', title: 'original', metadata: { retained: true } };
  await plugin['tool.execute.after']({ sessionID: 'open-real-id', tool: 'bash' }, tool);
  assert(tool.output.startsWith('original tool output'));
  assert(tool.output.includes('opencode-tool-marker'));
  assert.deepEqual(tool.metadata, { retained: true });
  assert.equal(cursor('open-agent'), generation());
  checked('OpenCode tool callback injects Room context without replacing tool output');

  await plugin.event({ event: { type: 'session.created', properties: { info: { id: 'child', parentID: 'open-real-id' } } } });
  await plugin.event({ event: { type: 'session.idle', properties: { sessionID: 'child' } } });
  assert.equal(telemetry('open-agent').session_id, 'open-real-id');
  assert.equal(telemetry('open-agent').status, 'working');
  await plugin.event({ event: { type: 'session.idle', properties: { sessionID: 'open-real-id' } } });
  assert.equal(telemetry('open-agent').status, 'idle');
  checked('OpenCode subagent events cannot overwrite the member session');
  await plugin['chat.message']({ sessionID: 'selected-existing-session' }, { parts: [{ type: 'text', text: 'resume selected session' }] });
  assert.equal(telemetry('open-agent').session_id, 'selected-existing-session');
  await plugin['chat.message']({ sessionID: 'child' }, { parts: [{ type: 'text', text: 'child prompt' }] });
  assert.equal(telemetry('open-agent').session_id, 'selected-existing-session');
  checked('OpenCode records native primary-session switching and ignores child prompts');

  process.env.HIVE_BIN_DIR = root + '/missing-binary-directory';
  const runner = createRunner('pi', root);
  const oldCursor = cursor('open-agent');
  await runner.deliver('PostToolUse', {}, () => assert.fail('missing helper cannot inject'));
  assert.equal(cursor('open-agent'), oldCursor);
  checked('missing hook executable is handled without crashing or acknowledging');
  delete process.env.HIVE_MEMBER;
  await runner.deliver('PostToolUse', {}, () => assert.fail('outside Hive cannot inject'));
  checked('bridge is inactive outside a Hive member session');
  console.log('all ' + checks + ' bridge checks passed');
} finally {
  rmSync(root, { recursive: true, force: true });
}
