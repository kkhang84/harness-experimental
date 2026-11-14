# US-001 Install Harness Into A Project

## Status

implemented

## Lane

normal

## Product Contract

A user can apply the Harness v0 operating files and folder structure to a
target project directory without introducing an application stack, package
scripts, CI, tests, or product implementation.

## Relevant Product Docs

- `README.md`
- `docs/HARNESS.md`
- `docs/FEATURE_INTAKE.md`
- `scripts/README.md`

## Acceptance Criteria

- The installer defaults to the current directory when no target is provided.
- The installer accepts a specific target path through a command-line option or
  positional argument.
- If `AGENTS.md`, `docs/`, or `scripts/` already exists in the target, an
  interactive install shows a warning and asks whether to `1. Merge`,
  `2. Override`, or `3. Stop`.
- If `AGENTS.md`, `docs/`, or `scripts/` already exists in the target, a
  non-interactive install stops before writing files unless `--merge` or
  `--override` is provided.
- A piped `curl | bash` install can still ask interactive questions through the
  controlling terminal when `--yes` is not provided.
- Existing non-protected files are not overwritten by default.
- Forced overwrites create a timestamped backup before replacing non-protected
  files.
- A dry-run mode reports planned file operations without writing files.
- The installer copies only Harness v0 operating files and does not scaffold
  application code, package scripts, CI, or validation commands.
- The installer script and this installer story are not copied into target
  projects.

## Design Notes

- Commands: `scripts/install-harness.sh [--directory path] [--yes] [--force] [--dry-run]`
- Remote install: `curl -fsSL "https://raw.githubusercontent.com/hoangnb24/harness-experimental/main/scripts/install-harness.sh?$(date +%s)" | bash -s -- --yes`
- Queries: none.
- API: none.
- Tables: none.
- Domain rules: preserve Harness v0 as a generic, spec-intake-first operating
  framework.
- UI surfaces: terminal prompts and summary output only.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Shell syntax check for `scripts/install-harness.sh`. |
| Integration | Dry-run into a temporary target reports expected file creation. |
| E2E | Install into a temporary target creates the harness file structure. |
| Platform | POSIX shell execution on the local macOS environment. |
| Release | Not applicable until packaging exists. |

## Harness Delta

Adds the first real harness automation script while keeping installer internals
out of target projects and preserving the Harness v0 rule that application
implementation surfaces are not scaffolded.

## Evidence

- `bash -n scripts/install-harness.sh`
- `scripts/install-harness.sh --directory "$LOCAL_TARGET" --yes`
- `scripts/install-harness.sh --directory "$README_TARGET" --yes` after adding a
  custom `README.md` in the target
- `scripts/install-harness.sh --directory "$AGENTS_CONFLICT" --yes`
- `scripts/install-harness.sh --directory "$DOCS_CONFLICT" --yes`
- `scripts/install-harness.sh --directory "$SCRIPTS_CONFLICT" --yes --force`
- `scripts/install-harness.sh --directory "$NONINTERACTIVE_MERGE" --merge --yes`
- `scripts/install-harness.sh --directory "$NONINTERACTIVE_OVERRIDE" --override --yes`
- interactive conflict prompt with `1` choice to merge missing files
- interactive conflict prompt with `2` choice to back up and override protected
  paths
- interactive conflict prompt with `3` or default choice to stop without writing
  files
- `HARNESS_SOURCE_BASE_URL="file:///Users/themrb/Documents/personal/harness-experimental" bash -s -- --directory "$REMOTE_TARGET" --yes < scripts/install-harness.sh`
- `curl -fsSL "file:///Users/themrb/Documents/personal/harness-experimental/scripts/install-harness.sh" | HARNESS_SOURCE_BASE_URL="file:///Users/themrb/Documents/personal/harness-experimental" bash -s -- --directory "$TARGET" --yes`
- `HARNESS_SOURCE_BASE_URL="file:///Users/themrb/Documents/personal/harness-experimental" bash -s -- --directory "$DRY_TARGET" --yes --dry-run < scripts/install-harness.sh`

Validated behaviors: dry-run writes no files, real install creates the harness
structure, existing `README.md` is left untouched by default, non-interactive
targets containing `AGENTS.md`, `docs/`, or `scripts/` stop with a warning
before writing files unless `--merge` or `--override` is provided, interactive
users can stop, merge missing files, or back up and override protected paths
even when the script is piped into Bash, remote-source mode works when the
script is piped into Bash, and target projects do not receive
`scripts/install-harness.sh` or this installer story.

## Pilot 02 — Codex-Reported Local Verification (2026-11-14)

**Evidence status:** reported by the Codex Cloud task operator; **not independently
re-run or archived in this repository**. This section records a handoff, not a
new verification result or release sign-off.

- Baseline commit: `2e8856af4ffc2a590ed3a689f9a5ba2b15f5960a`.
- Work classification: maintenance request, normal lane; local installer
  verification related to US-001.
- Execution scope: local checkout and disposable temporary target only; no
  remote installer execution or repository modifications.
- Task-reported result: **22/22 assertions passed**; Bash syntax exited `0`;
  expected non-interactive conflict refusal exited `1`.
- Reported behavior: exact 25-file installed payload, byte-for-byte content
  matching, installer/story exclusion, conflict refusal without target changes,
  custom-content preservation on merge, missing-file restoration, repeatable
  merge, non-writing dry-run on fresh/existing targets, and unchanged checkout.
- Reported tool versions: Bash 5.2.37, Git 2.52.0, Python 3.12.14.
- Session-local evidence was reported at
  `/tmp/harness-pilot02-F2CxVCOF/` (`report.md`, `commands.json`,
  `assertions.json`, `run.py`, `baseline.json`). These absolute paths
  belong to the Codex execution environment, are **not durable repository
  links**, and may no longer exist. They were not available for an independent
  review in this documentation-only PR.
- The reported checkout-integrity check is **not** a system-wide write audit.

**Not covered by Pilot 02:** interactive prompts, remote distribution,
force/override backup behavior, other platforms, fresh-task restoration, or
application builds/tests.

**Next evidence gate:** obtain or regenerate a reviewable run record (source
revision, runner, commands, exit codes, machine-checkable assertions and
artifacts), then have an independent verifier re-run or audit it before
claiming independently established coverage. The historical US-001 evidence
above remains distinct from this Codex-reported Pilot 02 execution.
