#!/usr/bin/env python3
"""Bounded GitHub-App Draft-PR publisher (no merge/review/deployment API)."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import time
import urllib.error
import urllib.request

API = "https://api.github.com"
REPO = "kkhang84/harness-experimental"
BOT = "kkhang84-harness-codex-publisher[bot]"
TASK_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,39}\Z")
SHA_RE = re.compile(r"[0-9a-f]{40}\Z")

class PublisherError(Exception):
    pass

def read_json(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise PublisherError("JSON document must be an object")
    return obj

def validate(bundle: Path, policy_file: Path) -> dict:
    bundle = bundle.resolve(strict=True)
    policy_file = policy_file.resolve(strict=True)
    if policy_file.is_relative_to(bundle):
        raise PublisherError("Trusted policy cannot live inside an agent-controlled bundle")
    proposal = read_json(bundle / "proposal.json")
    policy = read_json(policy_file)
    task = proposal.get("task_id")
    if not isinstance(task, str) or not TASK_RE.fullmatch(task):
        raise PublisherError("Invalid task_id")
    if task != policy.get("task_id"):
        raise PublisherError("Task is not authorized by trusted policy")
    if proposal.get("repository") != REPO or policy.get("repository") != REPO:
        raise PublisherError("Repository is not allowlisted")
    if proposal.get("base_branch") != "main" or policy.get("base_branch") != "main":
        raise PublisherError("Only main is an allowed base")
    expected = proposal.get("expected_base_sha")
    if not isinstance(expected, str) or not SHA_RE.fullmatch(expected) or expected != policy.get("expected_base_sha"):
        raise PublisherError("Base SHA must match trusted authorization")
    title, body = proposal.get("title"), proposal.get("body")
    if not isinstance(title, str) or not 8 <= len(title) <= 120 or "\n" in title:
        raise PublisherError("Invalid PR title")
    if not isinstance(body, str) or not 16 <= len(body) <= 4000:
        raise PublisherError("Invalid PR body")
    changes = proposal.get("changes")
    allow_paths = policy.get("allowed_paths")
    if not isinstance(allow_paths, list) or not allow_paths or any(not isinstance(p, str) for p in allow_paths):
        raise PublisherError("Trusted allowed_paths required")
    if not isinstance(changes, list) or not 1 <= len(changes) <= min(policy.get("max_files", 3), 3):
        raise PublisherError("Invalid change count")
    seen = set()
    staged = []
    total = 0
    for change in changes:
        if not isinstance(change, dict):
            raise PublisherError("Invalid change entry")
        path, source, digest = change.get("path"), change.get("content_file"), change.get("sha256")
        if not isinstance(path, str) or path not in allow_paths or path in seen:
            raise PublisherError("Duplicate or unauthorized target path")
        seen.add(path)
        pp = PurePosixPath(path)
        if pp.as_posix() != path or path.startswith("/") or "\\" in path or any(part in (".", "..") or part.startswith(".") for part in path.split("/")):
            raise PublisherError("Unsafe target path")
        if not path.startswith("docs/publisher-pilot/") or not path.endswith(".md"):
            raise PublisherError("Only pilot Markdown files are allowed")
        if not isinstance(source, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+\.md", source):
            raise PublisherError("Invalid bundle content_file name")
        file = bundle / source
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(bundle):
            raise PublisherError("Bundle file must be a regular local file")
        data = file.read_bytes()
        if len(data) > 16384 or b"\x00" in data:
            raise PublisherError("Only small textual files are permitted")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PublisherError("Bundle content must be UTF-8") from exc
        if not isinstance(digest, str) or hashlib.sha256(data).hexdigest() != digest:
            raise PublisherError("Content checksum mismatch")
        total += len(data)
        staged.append({"path": path, "content": data.decode("utf-8")})
    if total > min(policy.get("max_total_bytes", 32768), 32768):
        raise PublisherError("Total size exceeds trusted policy")
    return {"task_id": task, "base_sha": expected, "title": title, "body": body,
            "branch": "agent/pilot04-" + task, "changes": staged}

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def app_jwt(app_id: str, pem: bytes, now: int | None = None) -> str:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    if not app_id.isdecimal():
        raise PublisherError("App ID must be numeric")
    now = int(time.time()) if now is None else now
    header = _b64(b'{"alg":"RS256","typ":"JWT"}')
    payload = _b64(json.dumps({"iat": now-60, "exp": now+540, "iss": app_id}, separators=(",", ":")).encode())
    sign_input = (header + "." + payload).encode("ascii")
    key = serialization.load_pem_private_key(pem, password=None)
    signature = key.sign(sign_input, padding.PKCS1v15(), hashes.SHA256())
    return header + "." + payload + "." + _b64(signature)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PublisherError("GitHub API redirect refused")

class GitHub:
    def __init__(self, token: str):
        self.token = token
    def request(self, method: str, path: str, payload: dict | None = None, allow_404: bool = False):
        if not path.startswith("/") or "//" in path or ".." in path or "?" in path:
            raise PublisherError("Invalid GitHub API path")
        req = urllib.request.Request(
            API + path,
            method=method,
            data=(json.dumps(payload).encode("utf-8") if payload is not None else None),
            headers={"Accept": "application/vnd.github+json", "Authorization": "Bearer " + self.token,
                     "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.build_opener(NoRedirect).open(req, timeout=15) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and allow_404:
                return None
            # Do not print headers, token or error response body.
            raise PublisherError(f"GitHub request {method} {path} failed (HTTP {exc.code})") from None
        except urllib.error.URLError:
            raise PublisherError(f"GitHub request {method} {path} failed (network error)") from None

def mint_installation_token(app_id: str, installation_id: str, private_key: bytes) -> str:
    if not installation_id.isdecimal():
        raise PublisherError("Installation ID must be numeric")
    jwt = app_jwt(app_id, private_key)
    issued = GitHub(jwt).request("POST", f"/app/installations/{installation_id}/access_tokens", {
        "repositories": [REPO.split("/")[1]],
        "permissions": {"contents": "write", "pull_requests": "write"},
    })
    if not isinstance(issued, dict) or not isinstance(issued.get("token"), str):
        raise PublisherError("No installation token returned")
    return issued["token"]

def publish(plan: dict, api: GitHub) -> dict:
    repo_path = f"/repos/{REPO}"
    base_ref = api.request("GET", repo_path + "/git/ref/heads/main")
    current_sha = base_ref.get("object", {}).get("sha")
    if current_sha != plan["base_sha"]:
        raise PublisherError("Base SHA changed; refuse to publish")
    new_branch = plan["branch"]
    if api.request("GET", repo_path + "/git/ref/heads/" + new_branch, allow_404=True) is not None:
        raise PublisherError("Task branch exists; refusing duplicate or overwrite")
    # Pilot is new-file-only: never overwrite existing documents.
    for change in plan["changes"]:
        file = api.request("GET", repo_path + "/contents/" + change["path"], allow_404=True)
        if file is not None:
            raise PublisherError("Target already exists on main")
    base_commit = api.request("GET", repo_path + "/git/commits/" + plan["base_sha"])
    base_tree = base_commit.get("tree", {}).get("sha")
    if not isinstance(base_tree, str) or not SHA_RE.fullmatch(base_tree):
        raise PublisherError("Missing base tree SHA")
    entries = []
    for change in plan["changes"]:
        blob = api.request("POST", repo_path + "/git/blobs", {"content": change["content"], "encoding": "utf-8"})
        entries.append({"path": change["path"], "mode": "100644", "type": "blob", "sha": blob["sha"]})
    tree = api.request("POST", repo_path + "/git/trees", {"base_tree": base_tree, "tree": entries})
    commit = api.request("POST", repo_path + "/git/commits", {
        "message": "docs(publisher): " + plan["task_id"], "tree": tree["sha"], "parents": [plan["base_sha"]]
    })
    # Non-force creation. This creates ONLY the agent-prefixed branch.
    api.request("POST", repo_path + "/git/refs", {"ref": "refs/heads/" + new_branch, "sha": commit["sha"]})
    try:
        pr = api.request("POST", repo_path + "/pulls", {"title": plan["title"], "body": plan["body"],
                       "head": new_branch, "base": "main", "draft": True, "maintainer_can_modify": False})
    except PublisherError as exc:
        raise PublisherError(f"Branch {new_branch} was created but Draft PR creation failed; inspect manually: {exc}") from None
    login = pr.get("user", {}).get("login")
    if login != BOT or pr.get("draft") is not True:
        raise PublisherError(f"PR #{pr.get('number')} created, but bot attribution/draft status mismatch. Stop and inspect manually")
    return {"task_id": plan["task_id"], "branch": new_branch, "pr_number": pr["number"],
            "url": pr["html_url"], "head_sha": commit["sha"], "author": login, "draft": True}

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Bounded GitHub App Draft PR publisher")
    parser.add_argument("action", choices=["validate", "publish"])
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        plan = validate(args.bundle, args.policy)
        if args.action == "validate":
            print(json.dumps({"status": "VALIDATED_OFFLINE", "task_id": plan["task_id"],
                              "branch": plan["branch"], "files": [c["path"] for c in plan["changes"]]}, indent=2))
            return 0
        key_path = Path(os.environ["GITHUB_APP_PRIVATE_KEY_PATH"]).resolve(strict=True)
        bundle = args.bundle.resolve(strict=True)
        if key_path.is_relative_to(bundle) or key_path.is_relative_to(Path.cwd().resolve()):
            raise PublisherError("Private key must be outside bundle and current checkout")
        token = mint_installation_token(os.environ["GITHUB_APP_ID"], os.environ["GITHUB_INSTALLATION_ID"], key_path.read_bytes())
        result = publish(plan, GitHub(token))
        print(json.dumps(result, indent=2))
        return 0
    except (PublisherError, KeyError, ValueError, OSError) as exc:
        # Never print PEM, token, HTTP response body or env variable values.
        print(f"Publisher refused: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
