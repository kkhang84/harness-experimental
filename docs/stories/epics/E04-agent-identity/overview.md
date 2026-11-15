# E04 Pilot 04 — GitHub App Draft PR Publisher

**Input type:** harness improvement / controlled implementation.
**Lane:** high-risk (external API permissions, GitHub actor and audit).
**Status:** PR proposed for human review.
**Implementation approval:** user authorized building a Publisher on a separate branch, with no merge or deployment.

**Intent:** separate AI agent publishing identity from the human GitHub approver using the installed kkhang84-harness-codex-publisher App and a trusted publisher boundary. Codex supplies only a change bundle; it never receives App secrets or a GitHub installation token.

**Current constraint:** repository is generic Harness v0. This pilot creates narrowly scoped tooling, not a product application or service platform. The existing PR #1 created under kkhang84 cannot retroactively become a bot-owned PR. A separate smoke PR is required to prove attribution.

**Acceptance:** safe offline validation plus negative tests, documented authentication boundary, and a reviewable Draft PR **for this implementation**. Actual bot PR publication is a distinct approval/deployment gate.

**Out of scope:** GitHub App configuration changes, credentials, installation IDs, live bot publication, branch rules changes, workflows/CI, applications, merge or release.
