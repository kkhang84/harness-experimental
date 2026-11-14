# Harness Backlog

Use this file when an agent discovers a missing harness capability but should
not change the operating model immediately.

## Template

```md
## Missing Harness Capability

### Title

Short name.

### Discovered While

Task or story that exposed the gap.

### Current Pain

What was hard, repeated, ambiguous, or unsafe?

### Suggested Improvement

What should be added or changed?

### Risk

Tiny, normal, or high-risk.

### Status

proposed | accepted | implemented | rejected
```

## Items

## Durable Evidence and Repeatable Verification

### Discovered While

Pilot 02 Codex Cloud local installer validation (2026-11-14).

### Current Pain

The task reported 22 passing assertions, but its runner, command logs and
assertions lived under an ephemeral `/tmp` path. Reviewers cannot reproduce
or independently inspect the original run from the repository.

### Suggested Improvement

Propose a bounded, repeatable local verification runner and an evidence
manifest recording source commit, command/exit-code pairs, assertion outcomes
and artifact hashes. Define a durable storage location and retention policy
before recording future runs as verified. Keep generated evidence separate
from the source-of-truth product specification.

### Risk

normal

### Status

proposed

## Task Checkpoint and Resume Handoff

### Discovered While

Pilot 01 readiness assessment and Pilot 02 execution handoff.

### Current Pain

Fresh Codex tasks must reconstruct prior progress from conversation and
session-local files; no small checkpoint/resume record is required.

### Suggested Improvement

Propose a compact handoff template: repository and base commit, task/lane,
approved scope, completed steps, commands and outcomes, artifacts, blockers,
retry/stop conditions, and next safe action. Test restoration in a separate
fresh task before adopting a mandatory workflow.

### Risk

normal

### Status

proposed

## Independent Evaluation and Human Review Gate

### Discovered While

Pilot 02 self-reported assertions and the proposed Pilot 03 documentation PR.

### Current Pain

Agent-reported validation is not yet separated from independent verification;
there is no explicit reviewer checklist for proof quality, allowed changed
files, and human merge ownership.

### Suggested Improvement

Propose an independent verifier or CI run against an immutable commit,
evidence freshness checks, a diff/evidence review checklist, and explicit
human ownership of merge/release decisions. Keep this **proposal only** until
the human approves any changes to the operating policy or CI setup.

### Risk

high-risk

### Status

proposed

