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
