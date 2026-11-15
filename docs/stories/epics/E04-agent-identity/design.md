# E04 Design: trusted publisher boundary

~~~text
Codex change bundle (untrusted)
    | proposal.json + Markdown file + sha256
    v
Trusted runner + read-only human policy (separate from Codex)
    | exact repo/task/base-SHA/path/size checks; no HTTP server
    | GitHub App private key loaded only here
    v
GitHub App JWT -> one-hour repo-scoped installation token
    | GET base and target existence -> POST blob/tree/commit/agent ref/Draft PR
    v
Bot-authored PR -> independent verifier (future) -> human approval (future)
~~~

## Trust boundaries

- **Human policy** must not be agent-editable. An allowlist inside the same agent bundle is **not** authorization.
- **Publisher version** must be pinned outside the agent branch. Running an agent-edited publisher with private-key access breaks the boundary.
- **App scope:** only one public pilot repository; ask GitHub for contents:write and pull_requests:write and only that repository.
- **No merge capability in the exposed CLI:** implementation contains no endpoint or method for merge, review approval, release, or settings. Since the GitHub App token still has write powers, this is only a software control; require GitHub rulesets and organizational actor restrictions for production-grade enforcement.
- **Publication idempotency:** refusal if base moved or branch already exists. On a partial publish, report for human inspection rather than force-push or auto-cleanup.
- **No arbitrary payload execution:** Markdown data is read with file size, checksum, encoding and symlink checks; no generated script is executed.
- **Independent eval:** separate future task must validate the actual GitHub PR head SHA and actor, archive assertions, and require human approval; in-process mocks are insufficient.

## Deferred design choices

Internal Java Spring Boot service, authenticated API/webhook, evidence store, CI workflow and branch restrictions all require separate approval and implementation phases. This narrow CLI is not a full-fledged production broker.
