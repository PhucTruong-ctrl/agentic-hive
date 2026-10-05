# Hive incidents

Concrete evidence behind changes to Hive physics (SPEC §2.6, §21).

## 2026-09-30 — members start new work without announcing it

Crew: claude-opus-game, claude-opus-game-2 on debter (Claude Code).

Observed (Room generation 1–5, member transcripts):
- Both members announced their first task and later shared incidental findings
  (git sync state).
- New Beekeeper prompts ("check the Blacksmith work", "a new sync, check
  again") went straight to reading and `git` with no Room line. One member
  found a shared-code bug ("Crop care slot can never fill in a new run") and
  kept it in its own context.

Cause: the member instruction explained what the Room is but not when to use
it, and ended with "Keep coordination cheap", which reads as "stay quiet".

Change:
- member-instruction.md names three moments to post (starting, finding,
  done/blocked) and what not to post.
- hive-hook adds a one-line reminder on UserPromptSubmit only when the member
  has not posted for HIVE_QUIET_MINUTES (default 20; 0 disables).

Watch for: chatter volume rising, reminders ignored, or reminders prompting
low-value posts. Revert or tune if so.

## 2026-10-05 — WebUI mention delivery cannot allocate temporary files

Observed: Send reported `mktemp: failed to create directory via template
‘/tmp/tmp.XXXXXXXXXX’: Read-only file system`. The running dashboard unit had
`ProtectSystem=strict` and writable paths for `/srv/hive` and `/home/hive`,
but omitted `/tmp`. A mention post had already been recorded before delivery
allocated its temporary result directory, so a retry could duplicate it.

Change: allow the service to write shared `/tmp`, retaining access to existing
tmux sockets. Allocate delivery scratch before appending the Room post. A
focused regression test verifies that an unavailable temporary directory leaves
Room history and generation unchanged and sends no prompts.

## 2026-10-05 — accepted prompt reported as unconfirmed

Observed: a WebUI post to `sol-3` at 03:38:54 reported unconfirmed delivery.
The member received and answered it; its matching UserPromptSubmit receipt was
written at 03:39:14, after the roughly eleven-second confirmation window.
The informational `already running (idle)` line obscured that timeout.

Change: allow roughly 45 seconds for submission receipts, including queued
input on busy harnesses, and give WebUI subprocesses enough time for delivery
batches. Working and idle members still share the same paste/submit path;
stopped members launch with the prompt. Send results omit the running-state
line. Confirmation still requires the matching hook receipt and never repastes.
An isolated real Codex check queued a second prompt during a running tool and
confirmed its submission 31 seconds later. A delayed-receipt regression also
checks that accepted input gets one paste and one Enter.

## 2026-10-05 — waiting for processing makes accepted mentions look failed

Observed again after extending the receipt window: `sol-3` displayed the
Beekeeper's reply to Room #2706 in its transcript while Send reported unconfirmed
delivery. A busy Codex can accept input into its own queue before running the
prompt hook, so a longer receipt timeout delays the WebUI without establishing
that delivery failed.

Change: return on a matching hook receipt or two consecutive composer resets
after Hive's guarded Enter, with the harness still alive. A queued prompt is
accepted input, not evidence of processing or completed work. Live confirmation
that remains uncertain returns exit 2 and a separate `unconfirmed` report;
definite delivery errors remain failures. Retry Enter only while the submitted
text stays in the composer, never repaste it, and leave dialogs untouched.

Evidence: an isolated real Codex accepted idle input in 2621ms and busy input in
2858ms while its hook receipt remained unchanged, then answered the queued prompt
once. Regression checks cover swallowed Enter, an unchanged composer, missing
receipts, dialogs, and concurrent submissions. Production member sessions were
not changed.
