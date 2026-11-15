# E04 Validation & Evidence

## Commands executed in isolated preparation environment

~~~sh
python -m unittest discover -s tools/pr-publisher -p 'test_publisher.py' -v
python -m py_compile tools/pr-publisher/publisher.py tools/pr-publisher/test_publisher.py
~~~

At preparation: **19 local unit/negative tests passed**, using a **mock** GitHub API. Re-run after review or changes; independent CI is not yet present.

## Required follow-up gates

1. Review actual PR diff and confirm the code contains no merge, approval, release or deploy endpoints.
2. Human verify App installation permissions and selected repository in GitHub.
3. Human select trusted key manager/runner, record App ID and installation ID **without exchanging any PEM/token in chat**.
4. Run a separate live bot smoke task against a newly approved docs-only path, capture actual PR user.login and head SHA, independently verify the change, store durable evidence.
5. Require a formal human review (separate GitHub identity) before merge decisions.

**Not claimed:** remote integration tests, GitHub-App-token issuance, actual bot-authored PR, CI independence, hardened branch rules, or production readiness.
