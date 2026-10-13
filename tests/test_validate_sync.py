import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("validate_sync", Path(__file__).resolve().parents[1] / "scripts/validate_sync.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)
SYNC_SPEC = importlib.util.spec_from_file_location("sync_repositories", Path(__file__).resolve().parents[1] / "scripts/sync_repositories.py")
sync = importlib.util.module_from_spec(SYNC_SPEC)
SYNC_SPEC.loader.exec_module(sync)


class ValidateSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ("config", "reports", "library/imported"):
            (self.root / folder).mkdir(parents=True)
        self.output = self.root / "library/imported/skill.md"
        self.output.write_bytes(b"untrusted text")
        self.config = {"repositories": [{"repo": "owner/repo", "ref": "main"}]}
        self.manifest = {"sources": [{"repo": "owner/repo", "ref": "main", "selected_files": 1}],
                         "files": [{"repo": "owner/repo", "ref": "main", "path": "SKILL.md", "kind": "skill",
                                    "output_path": "library/imported/skill.md", "bytes_saved": 14}]}
        self.report = "## owner/repo\n- Ref: main\n- Selected Markdown files: 1\n- Imported skill: `SKILL.md`  `library/imported/skill.md`\n"

    def check(self):
        (self.root / "config/sources.json").write_text(json.dumps(self.config), encoding="utf-8")
        (self.root / "library/manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        (self.root / "reports/latest-report.md").write_text(self.report, encoding="utf-8")
        validator.validate(self.root)

    def test_complete_and_license_warning(self):
        self.report += "- REVIEW REQUIRED: GitHub did not detect a repository license.\n"
        self.check()

    def test_incomplete_report(self):
        for warning in ("WARNING: the GitHub tree response was truncated.", "ERROR downloading `SKILL.md`: failed",
                        "ERROR: discovery capped at 1 of 2 blob entries.", "ERROR: selection capped at 80 of 81 Markdown files."):
            with self.subTest(warning=warning):
                original = self.report
                self.report += f"- {warning}\n"
                with self.assertRaises(ValueError):
                    self.check()
                self.report = original

    def test_missing_download(self):
        self.manifest["files"] = []
        with self.assertRaises(ValueError):
            self.check()

    def test_report_mismatch(self):
        self.report = self.report.replace("SKILL.md", "OTHER.md")
        with self.assertRaises(ValueError):
            self.check()

    def test_source_mismatch(self):
        self.manifest["sources"] = []
        with self.assertRaises(ValueError):
            self.check()

    def test_missing_or_short_file(self):
        self.output.write_bytes(b"short")
        with self.assertRaises(ValueError):
            self.check()
        self.output.unlink()
        with self.assertRaises(ValueError):
            self.check()

    def test_duplicate_output(self):
        self.manifest["files"].append(dict(self.manifest["files"][0]))
        with self.assertRaises(ValueError):
            self.check()

    def test_path_escape(self):
        self.manifest["files"][0]["output_path"] = "library/imported/../../outside.md"
        self.report = self.report.replace("library/imported/skill.md", "library/imported/../../outside.md")
        with self.assertRaises(ValueError):
            self.check()

    def run_sync(self, tree, download=None, **limits):
        self.config.update(limits)
        (self.root / "config/sources.json").write_text(json.dumps(self.config), encoding="utf-8")
        with patch.multiple(sync, ROOT=self.root, CONFIG=self.root / "config/sources.json",
                            IMPORTED=self.root / "library/imported", DRAFTS=self.root / "library/drafts",
                            REPORTS=self.root / "reports", MANIFEST=self.root / "library/manifest.json"), \
             patch.object(sync, "get_json", side_effect=[{"license": None}, tree]), \
             patch.object(sync, "get_text", side_effect=download or (lambda *args: (b"source\n", "https://example.com"))):
            self.assertEqual(sync.main(), 0)

    def test_sync_complete_with_license_warning(self):
        self.run_sync({"tree": [{"type": "blob", "path": "SKILL.md"}]})
        validator.validate(self.root)

    def test_sync_failures_block_validation(self):
        cases = [({"tree": [], "truncated": True}, None, {}),
                 ({"tree": [{"type": "blob", "path": "SKILL.md"}]}, sync.requests.RequestException("failed"), {}),
                 ({"tree": [{"type": "blob", "path": "SKILL.md"}]}, None, {"max_files_per_repo": 0}),
                 ({"tree": [{"type": "blob", "path": f"skills/{i}.md"} for i in range(81)]}, None, {"max_files_per_repo": 250})]
        for tree, download, limits in cases:
            with self.subTest(tree=tree):
                self.run_sync(tree, download, **limits)
                with self.assertRaises(ValueError):
                    validator.validate(self.root)

    def test_oversized_download_is_rejected(self):
        with patch.object(sync.SESSION, "get") as get:
            get.return_value.content = b"too large"
            with self.assertRaises(sync.requests.RequestException):
                sync.get_text("https://example.com", 3)


if __name__ == "__main__":
    unittest.main()
