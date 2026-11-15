# E04 Execution Plan & Checkpoints

1. Baseline: record main SHA, inspect AGENTS.md and Harness v0 scope.
2. Build: add tools/pr-publisher/ CLI, exact-path policy contract, GitHub App authentication and draft-only publication methods.
3. Test: unit tests and negative cases with mock GitHub API; no GitHub secret or remote publication.
4. Evidence: capture test commands and results, audit allowed file diff before PR creation; do not claim independently executed CI.
5. Propose: create a **Draft PR** under current authorized GitHub connection. This PR's author will **not** prove bot attribution.
6. Human gate: obtain review of code and permissions, separately configure trusted runner and branch rules, and authorize a new docs-only bot smoke task before any live publisher invocation.

## Stop conditions

Stop if unexpected file changes, new GitHub permissions, attempt to post a secret, deviation from allowlisted repo/path/branch, actual merge or deployment, or mismatch between stated and verified actor. No retries following ambiguous partial publish without manual inspection.

## Handoff record

Include base SHA, head SHA, changed file list, test command/version/count, known limits, and the next human-owned action. Runner state is not durable until evidence is stored outside the execution environment.
