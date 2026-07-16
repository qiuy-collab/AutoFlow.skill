from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_diagram_assets.py"
SPEC = importlib.util.spec_from_file_location("generate_diagram_assets", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class DiagramAssetTests(unittest.TestCase):
    def test_arbitrary_mermaid_dsl_is_accepted(self):
        source, extension, renderer = MODULE.build_source(
            {
                "name": "state_machine",
                "kind": "state_machine",
                "renderer": "mermaid",
                "source": "stateDiagram-v2\n    [*] --> Draft\n    Draft --> Published",
            }
        )
        self.assertEqual(extension, ".mmd")
        self.assertEqual(renderer, "mermaid")
        self.assertIn("stateDiagram-v2", source)

    def test_unknown_kind_without_dsl_is_rejected_with_actionable_message(self):
        with self.assertRaises(SystemExit) as raised:
            MODULE.build_source({"name": "unknown", "kind": "new_diagram"})
        self.assertIn("requires renderer", str(raised.exception))

    def test_builtin_template_returns_renderer(self):
        source, extension, renderer = MODULE.build_source(
            {
                "name": "flow",
                "kind": "flowchart",
                "nodes": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
                "edges": [{"from": "a", "to": "b"}],
            }
        )
        self.assertEqual((extension, renderer), (".mmd", "mermaid"))
        self.assertIn("flowchart", source)


if __name__ == "__main__":
    unittest.main()
