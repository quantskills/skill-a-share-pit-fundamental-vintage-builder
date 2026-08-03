"""Regression checks for QuantSkills repository admission requirements."""

from __future__ import annotations

import unittest
from pathlib import Path



ROOT = Path(__file__).resolve().parents[1]


class CommunityComplianceTests(unittest.TestCase):
    def test_declares_gpl_v3_only_and_includes_full_license_text(self) -> None:
        metadata_text = (ROOT / "skill.yml").read_text(encoding="utf-8")
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

        self.assertEqual(metadata_text.count("license: GPL-3.0-only"), 2)
        self.assertIn("GNU GENERAL PUBLIC LICENSE", license_text)
        self.assertIn("Version 3, 29 June 2007", license_text)

    def test_provides_cursor_runtime_entrypoint(self) -> None:
        cursor_rule = (ROOT / "agents" / "cursor-rule.mdc").read_text(encoding="utf-8")

        self.assertIn("description:", cursor_rule)
        self.assertIn("SKILL.md", cursor_rule)

    def test_provides_portable_hermes_and_openclaw_entrypoint(self) -> None:
        loader = (ROOT / "agents" / "portable-loader.md").read_text(encoding="utf-8")

        self.assertIn("Hermes", loader)
        self.assertIn("OpenClaw", loader)
        self.assertIn("SKILL.md", loader)

    def test_provides_openai_runtime_metadata(self) -> None:
        adapter_text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("allow_implicit_invocation: true", adapter_text)
        self.assertIn("$skill-a-share-pit-fundamental-vintage-builder", adapter_text)


if __name__ == "__main__":
    unittest.main()
