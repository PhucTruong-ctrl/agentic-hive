# Harness bridge contracts

`pi-on.js` targets Pi's extension API and OMP's hook API. Both provide
`ctx.cwd`, `ctx.sessionManager.getSessionId()`, custom-message objects, and a
`before_agent_start` result with `message`. OMP additionally supports
`tool_result.additionalContext`; Pi receives a custom message instead.

- [Pi extension types](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/core/extensions/types.ts)
- [OMP hook types](https://github.com/can1357/oh-my-pi/blob/main/packages/coding-agent/src/extensibility/hooks/types.ts)
- [OMP hook dispatch](https://github.com/can1357/oh-my-pi/blob/main/packages/coding-agent/src/extensibility/hooks/runner.ts)

`opencode.js` targets OpenCode's V1 plugin contract. `chat.message` reads
`output.parts` and records the prompt/session ID without consuming context.
`experimental.chat.system.transform` appends the member instruction and Room
context to `output.system`. `tool.execute.after` appends context to the existing
`output.output`. V2's plugin API requires a separate adapter; this module does
not claim compatibility with that API.

- [OpenCode V1 plugin types](https://github.com/anomalyco/opencode/blob/dev/packages/plugin/src/index.ts)
- [OpenCode V2 migration guide](https://opencode.ai/v2/docs/build/plugins/migrate-v1)

`hive-runner.js` serializes hook processes, handles asynchronous spawn errors,
and bounds output and execution time. It requests deferred delivery, injects
the result through the vendor callback, then acknowledges that generation.
Lifecycle-only callbacks request telemetry without Room consumption. A failed
helper or injection does not acknowledge pending entries. An acknowledgement
failure may cause a retry to deliver the same entry again; it never discards
undelivered entries. Direct JSON-hook harnesses retain their stdout delivery
contract.

`test/bridge.mjs` exercises these contracts against the real Hive commands
with strict vendor API mocks. `test/session.sh` verifies installation, imports,
config preservation, and resume arguments without launching real vendors.
