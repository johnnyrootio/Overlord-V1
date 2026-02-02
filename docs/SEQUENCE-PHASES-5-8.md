# Sequence Diagram: Worker and Phases 5–8

This document describes how **multiclaude workers** and **Overlord phases 5 through 8** (Review Orchestrator, Deadlock Breaker, Stop Controller, Loop Controller) work and interact.

**Rendered diagram:** Open **sequence-phases-5-8-diagram.html** in this folder in a browser to view the diagram.

---

## Sequence Diagram

The diagram below shows the flow from **Phase 4 (Execution Manager)** dispatching workers through **Phase 5 (Review)** → **Phase 6 (Deadlock Breaker)** → **Phase 7 (Stop Controller)** → **Phase 8 (Loop Controller)**, and how multiclaude workers, reviewer, supervisor, and merge-queue participate.

```mermaid
sequenceDiagram
    participant GR as Graph Runtime
    participant P4 as Phase 4 (Execution Manager)
    participant P5 as Phase 5 (Review Orchestrator)
    participant P6 as Phase 6 (Deadlock Breaker)
    participant P7 as Phase 7 (Stop Controller)
    participant P8 as Phase 8 (Loop Controller)
    participant MC as multiclaude (CLI)
    participant W as Worker(s)
    participant Rev as Reviewer (multiclaude)
    participant Sup as Supervisor (multiclaude)
    participant MQ as Merge-Queue (multiclaude)
    participant GH as GitHub (PRs/issues)

    Note over GR,P4: Dispatch (Phase 4)
    GR->>P4: invoke(state)
    P4->>MC: create-worker-with-auto-accept(repo, task)
    MC->>W: spawn worker
    W->>W: implement to spec, run check.sh
    W->>GH: open PR
    W->>MC: message send workspace "PR #N opened"
    P4->>MC: list-workspace-replies / check-worker-status
    P4->>GR: state updated (workers, PRs)

    Note over GR,P5: Review (Phase 5)
    GR->>P5: invoke(state)
    P5->>MC: review <pr-url>
    MC->>Rev: spawn review agent
    Rev->>GH: read PR, spec, tests
    Rev->>Rev: spec compliance (primary), tests (secondary)
    alt blocking issues
        Rev->>GH: post comments (blocking tasks)
        Rev->>MQ: "Review complete. Blocking issues. Not safe to merge."
        P5->>MC: create-worker-with-auto-accept("Fix blocking issues PR #N")
        MC->>W: spawn fix worker
        W->>GH: push fixes
        P5->>MC: review <pr-url> (re-run)
    else no blocking, CI green
        Rev->>GH: post comments (optional suggestions)
        Rev->>MQ: "Review complete. Spec compliance ✅. Safe to merge."
        Rev->>MC: agent complete
        MQ->>GH: merge PR
    end
    P5->>GR: state updated (reviews done, PRs merged)

    Note over GR,P6: Deadlock Breaker (Phase 6)
    GR->>P6: invoke(state)
    P6->>MC: worker list; check-worker-status
    P6->>GH: PR/issue state (conflicts, duplicates)
    alt merge conflict
        P6->>GH: create issue "Resolve merge conflict PR A vs B"
        P6->>MC: create-worker-with-auto-accept("Resolve conflict...")
    else duplicate work
        P6->>Sup: (supervisor chooses winner per workflow)
        Sup->>GH: close/abandon duplicate PRs
    else manual prompt stall
        P6->>MC: auto_accept_workers or escalate to human
    else test arbitration stall
        P6->>Sup: supervisor decides or escalates
        P6->>GR: optional: human decision needed
    end
    P6->>GR: state updated (deadlocks cleared or escalated)

    Note over GR,P7: Stop Controller (Phase 7)
    GR->>P7: invoke(state)
    P7->>GH: issue/PR status; work graph
    P7->>P7: evaluate: wave complete? milestone? budget guard?
    alt wave complete
        P7->>GR: continue to next wave or Phase 8
    else budget / pause
        P7->>GR: emit progress summary; pause for human
    end
    P7->>GR: state updated (stop decision, summary)

    Note over GR,P8: Loop Controller (Phase 8)
    GR->>P8: invoke(state)
    P8->>P8: prior cycle outcomes; more features?
    alt repeat cycle
        P8->>GR: transition to Phase 1 (or Phase 0)
        Note over GR: Loop: Brainstorm → Spec → Work graph → Issues → Dispatch → 5→6→7→8
    else done
        P8->>GR: end (progress visible, inspectable)
    end
```

## Summary of roles

| Participant | Role |
|-------------|------|
| **Graph Runtime** | Invokes phase agents in order; holds state; decides next node (e.g. Phase 5 → 6 → 7 → 8 or loop). |
| **Phase 4 (Execution Manager)** | Dispatches workers via create-worker-with-auto-accept; monitors via check-worker-status, list-workspace-replies; updates state. |
| **Phase 5 (Review Orchestrator)** | Runs review agent per PR; ensures spec compliance (primary) and tests (secondary); spawns fix workers if blocking; merge-queue merges when safe. |
| **Phase 6 (Deadlock Breaker)** | Detects merge conflicts, duplicate work, manual prompt stalls, test arbitration stalls; creates issues or spawns conflict-resolver; involves supervisor or human when needed. |
| **Phase 7 (Stop Controller)** | Evaluates wave complete, milestone, budget guard; emits progress summary; continues or pauses for human. |
| **Phase 8 (Loop Controller)** | Decides whether to repeat from Phase 1 (or Phase 0) for next features or end; keeps progress inspectable. |
| **Worker(s)** | Implement to operational spec; run check.sh; open PR; reply to workspace. |
| **Reviewer** | Spec compliance first, tests second; post comments; message merge-queue; agent complete. |
| **Supervisor** | Test arbitration; duplicate-work winner; escalate to Overlord/human when needed. |
| **Merge-Queue** | Merges PR when review says "safe to merge" and CI green. |

Overlord phase agents (P4–P8) interact with multiclaude **only via CLI and documented scripts**; they do not use tmux, socket API, or direct state access.

---

See **DESIGN-AND-ARCHITECTURE.md** and **OVERLORD-AGENT-V1-SPEC.md** in this folder for the full architecture and spec; see **foundational/palpatine/** for the authoritative workflow and prompt sources.
