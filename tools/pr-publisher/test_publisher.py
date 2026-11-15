import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import importlib.util

spec = importlib.util.spec_from_file_location("publisher", Path(__file__).with_name("publisher.py"))
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)

BASE = "a" * 40

class FakeGitHub:
    def __init__(self, branch_exists=False, wrong_actor=False, changed_base=False):
        self.calls = []
        self.branch_exists = branch_exists
        self.wrong_actor = wrong_actor
        self.changed_base = changed_base
    def request(self, method, path, payload=None, allow_404=False):
        self.calls.append((method, path, payload))
        if path.endswith("/git/ref/heads/main"):
            return {"object": {"sha": "b"*40 if self.changed_base else BASE}}
        if "/git/ref/heads/agent/" in path:
            return {"object": {"sha": "b"*40}} if self.branch_exists else None
        if "/contents/" in path:
            return None
        if "/git/commits/" in path and method == "GET":
            return {"tree": {"sha": "c"*40}}
        if path.endswith("/git/blobs"):
            return {"sha": "d"*40}
        if path.endswith("/git/trees"):
            return {"sha": "e"*40}
        if path.endswith("/git/commits"):
            return {"sha": "f"*40}
        if path.endswith("/git/refs"):
            return {"ref": payload["ref"]}
        if path.endswith("/pulls"):
            return {"number": 7, "html_url": "https://github.com/kkhang84/harness-experimental/pull/7",
                    "draft": True, "user": {"login": "kkhang84" if self.wrong_actor else publisher.BOT}}
        raise AssertionError((method,path))

class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bundle = self.root / "bundle"
        self.bundle.mkdir()
        self.policy_path = self.root / "trusted-policy.json"
        self.file = self.bundle / "change.md"
        self.file.write_text("# Harmless pilot note\n", encoding="utf-8")
        self.doc = "docs/publisher-pilot/pilot04-smoke.md"
        self.proposal = {"task_id":"smoke", "repository": publisher.REPO, "base_branch":"main",
                         "expected_base_sha":BASE,"title":"docs: publisher smoke", "body":"Documenting a safe bot-authored smoke test.",
                         "changes":[{"path":self.doc,"content_file":"change.md",
                                     "sha256":hashlib.sha256(self.file.read_bytes()).hexdigest()}]}
        self.policy={"task_id":"smoke", "repository":publisher.REPO,"base_branch":"main",
                     "expected_base_sha":BASE,"allowed_paths":[self.doc],"max_files":1,"max_total_bytes":16384}
        self.write()
    def tearDown(self):
        self.tmp.cleanup()
    def write(self):
        (self.bundle/"proposal.json").write_text(json.dumps(self.proposal))
        self.policy_path.write_text(json.dumps(self.policy))
    def plan(self):
        return publisher.validate(self.bundle, self.policy_path)
    def assertRefused(self):
        with self.assertRaises(publisher.PublisherError):
            self.plan()
    def test_validation_accepts_allowed_file(self):
        plan=self.plan(); self.assertEqual(plan["branch"],"agent/pilot04-smoke")
    def test_wrong_repo_refused(self):
        self.proposal["repository"]="other/repo"; self.write(); self.assertRefused()
    def test_unapproved_task_refused(self):
        self.proposal["task_id"]="other"; self.write(); self.assertRefused()
    def test_base_mismatch_refused(self):
        self.proposal["expected_base_sha"]="b"*40;self.write();self.assertRefused()
    def test_main_only(self):
        self.proposal["base_branch"]="release";self.write();self.assertRefused()
    def test_file_scope(self):
        self.proposal["changes"][0]["path"]=".github/workflows/ci.yml";self.write();self.assertRefused()
    def test_code_file_disallowed(self):
        self.policy["allowed_paths"]=["src/main.py"]
        self.proposal["changes"][0]["path"]="src/main.py";self.write();self.assertRefused()
    def test_path_traversal(self):
        self.proposal["changes"][0]["path"]="docs/publisher-pilot/../x.md"
        self.policy["allowed_paths"]=[self.proposal["changes"][0]["path"]]; self.write(); self.assertRefused()
    def test_checksum_mismatch(self):
        self.file.write_text("tampered");self.assertRefused()
    def test_symlink_refused(self):
        self.file.unlink(); self.file.symlink_to(self.policy_path); self.assertRefused()
    def test_policy_in_bundle_refused(self):
        with self.assertRaises(publisher.PublisherError):
            publisher.validate(self.bundle, self.bundle/"proposal.json")
    def test_size_limit(self):
        self.file.write_text("a"*17000)
        self.proposal["changes"][0]["sha256"]=hashlib.sha256(self.file.read_bytes()).hexdigest()
        self.write();self.assertRefused()
    def test_success_publishes_draft_only(self):
        api=FakeGitHub(); result=publisher.publish(self.plan(),api)
        self.assertTrue(result["draft"]); self.assertEqual(result["author"], publisher.BOT)
        writes=[p for method,p,payload in api.calls if method=="POST"]
        self.assertEqual(writes[-2:], [f"/repos/{publisher.REPO}/git/refs",f"/repos/{publisher.REPO}/pulls"])
        create_ref=api.calls[-2][2]
        self.assertEqual(create_ref["ref"],"refs/heads/agent/pilot04-smoke")
        self.assertTrue(api.calls[-1][2]["draft"])
        self.assertNotIn("merge", " ".join(writes).lower())
    def test_stale_base_does_not_write(self):
        api=FakeGitHub(changed_base=True)
        with self.assertRaises(publisher.PublisherError): publisher.publish(self.plan(),api)
        self.assertFalse(any(c[0]=="POST" for c in api.calls))
    def test_branch_exists_does_not_write(self):
        api=FakeGitHub(branch_exists=True)
        with self.assertRaises(publisher.PublisherError): publisher.publish(self.plan(),api)
        self.assertFalse(any(c[0]=="POST" for c in api.calls))
    def test_existing_target_does_not_write(self):
        api=FakeGitHub()
        original=api.request
        def intercept(method,path,payload=None,allow_404=False):
            if "/contents/" in path:
                api.calls.append((method,path,payload))
                return {"sha":"f"*40}
            return original(method,path,payload,allow_404)
        api.request=intercept
        with self.assertRaisesRegex(publisher.PublisherError,"Target already exists"):
            publisher.publish(self.plan(),api)
        self.assertFalse(any(c[0]=="POST" for c in api.calls))
    def test_explicit_redirect_refusal(self):
        with self.assertRaisesRegex(publisher.PublisherError,"redirect refused"):
            publisher.NoRedirect().redirect_request(None,None,302,"",{},"https://evil.example")
    def test_actor_mismatch_not_marked_success(self):
        api=FakeGitHub(wrong_actor=True)
        with self.assertRaisesRegex(publisher.PublisherError,"attribution"):
            publisher.publish(self.plan(),api)
    def test_signing_jwt(self):
        from cryptography.hazmat.primitives.asymmetric import rsa, padding
        from cryptography.hazmat.primitives import hashes,serialization
        import base64
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        pem=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
        token=publisher.app_jwt("1234",pem,now=1700000000)
        h,p,s=token.split(".")
        key.public_key().verify(base64.urlsafe_b64decode(s+"="*(-len(s)%4)),(h+"."+p).encode(),padding.PKCS1v15(),hashes.SHA256())
        payload=json.loads(base64.urlsafe_b64decode(p+"="*(-len(p)%4)))
        self.assertEqual(payload["iss"],"1234")
        self.assertEqual(payload["exp"]-payload["iat"],600)

if __name__=="__main__":unittest.main()
