# Evolution Notes

Items we're tracking to evolve the Overlord system. Updated as we iterate (e.g. on Robotic Barista or other projects).

## Reliably capturing messages from multiclaude status stream

**Source:** Robotic Barista Overlord iteration.

**Issue:** Overlord sends status requests via `multiclaude message send`; agents reply to workspace. Capturing those replies (e.g. with `./scripts/list-workspace-replies.sh`) is not always reliable—Overlord can have trouble consistently seeing and acting on replies from the multiclaude “status stream.”

**Current approach:** See [CAPTURING-REPLIES.md](./CAPTURING-REPLIES.md) and `scripts/list-workspace-replies.sh`. Overlord runs the script to read `~/.multiclaude/messages/<repo>/workspace/` and optionally `--ack-all`.

**Tracked for evolution:**
- More reliable capture (polling, clearer output format, or Overlord tooling integration).
- Whether multiclaude or the workflow should expose a more stream-friendly or machine-readable way to consume agent replies.
- Workarounds that help (e.g. run script at intervals, ack-after-read).

---

*Add new items below with the same structure: source, issue, current approach, tracked for evolution.*
