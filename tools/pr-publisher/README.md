# Pilot 04 — Bounded GitHub App Draft PR Publisher

**Status:** proof-of-control CLI; not deployed or production hardened.

This trusted-runner CLI accepts a Codex change bundle, validates it against an operator-owned policy outside the bundle, and creates a new agent/pilot04-* branch and **Draft PR only** through the kkhang84-harness-codex-publisher GitHub App. No merge, review, release, deploy or settings operations exist.

## Security restrictions

- Repository fixed: kkhang84/harness-experimental; base branch fixed: main.
- Target paths must be exactly allowlisted by trusted policy under docs/publisher-pilot/ and end in .md; only new files. Maximum 3 files / 32 KiB, and 16 KiB per file.
- Task ID and expected base commit SHA must match the trusted, non-agent-editable policy.
- Abort on an existing branch, existing destination file or changed base SHA; never force-push, merge or overwrite.
- Private key may only exist on a trusted runner outside the agent checkout and input bundle.
- Only an App installation access token is used for GitHub writes. Do not log token or private key.
- PR creation forces draft=true; returned author must equal kkhang84-harness-codex-publisher[bot].
- This wrapper cannot by itself eliminate the App token's full GitHub write capabilities. Verify branch rules separately.
- The runner must use a trusted pinned script copy, not arbitrary source from a Codex-proposed branch.

## Proposed bundle

Create an untrusted directory such as /runner/inbox/pilot04-smoke containing pilot-note.md and proposal.json:

~~~json
{
  "task_id": "smoke",
  "repository": "kkhang84/harness-experimental",
  "base_branch": "main",
  "expected_base_sha": "<actual 40-char main commit SHA>",
  "title": "docs: publish identity smoke",
  "body": "Proposed documentation-only identity smoke test for Pilot 04.",
  "changes": [{
    "path": "docs/publisher-pilot/pilot04-smoke.md",
    "content_file": "pilot-note.md",
    "sha256": "<sha256 of pilot-note.md>"
  }]
}
~~~

Human-controlled policy at /etc/harness/pilot04-approval.json **outside the untrusted bundle**:

~~~json
{
  "task_id": "smoke",
  "repository": "kkhang84/harness-experimental",
  "base_branch": "main",
  "expected_base_sha": "<matching human-approved main SHA>",
  "allowed_paths": ["docs/publisher-pilot/pilot04-smoke.md"],
  "max_files": 1,
  "max_total_bytes": 16384
}
~~~

The policy cannot be considered human authorization if the agent can edit it. Human approval of scope, code and runner configuration must be separate.

## Offline validation (no GitHub credentials required)

~~~bash
python3 -m pip install -r tools/pr-publisher/requirements.txt
python3 -m unittest discover -s tools/pr-publisher -p 'test_publisher.py' -v
python3 tools/pr-publisher/publisher.py validate --bundle /runner/inbox/pilot04-smoke --policy /etc/harness/pilot04-approval.json
~~~

## Actual publication (DEFERRED until human-provisioned runner)

~~~bash
export GITHUB_APP_ID='<numeric App ID>'
export GITHUB_INSTALLATION_ID='<numeric Installation ID>'
export GITHUB_APP_PRIVATE_KEY_PATH='/secure/secret-mount/github-app.pem'
python3 tools/pr-publisher/publisher.py publish --bundle /runner/inbox/pilot04-smoke --policy /etc/harness/pilot04-approval.json
~~~

The CLI signs an RS256 JWT, requests an installation token narrowed to the selected repository with contents:write and pull_requests:write, validates base and target path, then creates blob/tree/commit/ref and opens a Draft PR. The returned PR creator is checked, not just the commit author string.

**Do not send secrets to ChatGPT or Codex.** If GitHub creates a branch but the PR operation fails, the CLI stops and leaves the branch for manual inspection; do not blindly retry.

## Evidence and limitations

Local unit tests use **mock GitHub responses**. Passing them does not establish real token issuance, real bot PR attribution, GitHub branch protection, independent CI, or production safety. A fresh live docs-only pilot, independent check against immutable head SHA, durable evidence and formal human approval are subsequent approval gates.

## Implementation choice

This initial non-network-exposed Python 3.12 CLI is a minimal proof and does not select a new stack for Harness v0. A future approved ADR can move the trusted service into Java Spring Boot if needed. No public API listener or deployment is included.
