# Test Matrix

This file maps product behavior to proof. Harness tooling verification is
tracked separately below so it is not mistaken for application-test coverage.

No product behavior has been defined or implemented yet. Do not mark a row
implemented until tests or validation evidence exist.

## Status Values

| Status | Meaning |
| --- | --- |
| planned | Accepted as intended behavior, not implemented |
| in_progress | Actively being built |
| implemented | Implemented and proof exists |
| changed | Contract changed after earlier implementation |
| retired | No longer part of the product contract |

## Matrix

| Story | Contract | Unit | Integration | E2E | Platform | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TBD | Add rows when story packets are created | no | no | no | no | planned | none |

## Evidence Rules

- Unit proof covers pure domain and application rules.
- Integration proof covers backend enforcement, data integrity, provider
  behavior, jobs, or service contracts.
- E2E proof covers user-visible browser flows.
- Platform proof covers only shell, deployment, mobile, desktop, or runtime
  behavior that cannot be proven in lower layers.
- A story can be implemented without every proof column if the story packet
  explains why.

## Harness Tooling Verification (separate from product behavior)

The installer is a harness utility, not a product application. US-001 is
marked `implemented` in its story. The following checks record **reported**
Pilot 02 outcomes; the underlying temporary artifacts have not been archived
or independently inspected. They do not make the product matrix above pass.

| Story | Scope | Syntax | Local install / payload | Conflict / merge / dry-run | Platform / remote | Story status | Evidence quality |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [US-001](stories/US-001-install-harness.md) | Harness installer (Pilot 02) | reported pass | reported pass (25 files) | reported pass, including expected exit 1 | not covered by Pilot 02 | implemented (per story) | 22/22 assertions reported; session-local artifacts not retained in repo; independent verification pending |

### Evidence Interpretation

- **Reported pass** means the task operator supplied a result; it is not
  equivalent to a CI pass or a reproducible, independently verified artifact.
- Pilot 02 baseline: `2e8856af4ffc2a590ed3a689f9a5ba2b15f5960a`.
- The task reported `bash -n scripts/install-harness.sh` passing, plus local
  disposable-target installation, file comparison, refusal, merge,
  repeatability and dry-run assertions. See US-001's Pilot 02 handoff section.
- Interactive prompt behavior, remote-source execution, override/backup,
  cross-platform checks and fresh-task restoration remain **unverified by
  this pilot**, regardless of historical notes in the installer story.
- No application stack, product contract, app tests or CI runner exists in
  Harness v0. No application test result is implied by this documentation.
