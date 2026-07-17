from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_diagram_assets.py"
SPEC = importlib.util.spec_from_file_location("generate_diagram_assets", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class DiagramAssetTests(unittest.TestCase):
    def test_direct_mode_defaults_to_one_png_without_source_svg_or_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "output"
            plan_path = root / "diagram-plan.json"
            plan_path.write_text(
                json.dumps(
                    {
                        "enabled": True,
                        "diagrams": [
                            {
                                "name": "simple_er",
                                "kind": "er_diagram",
                                "entities": [
                                    {
                                        "name": "STUDENT",
                                        "attributes": [
                                            {"type": "int", "name": "id", "key": "PK"},
                                            {"type": "string", "name": "name"},
                                        ],
                                    },
                                    {
                                        "name": "COURSE",
                                        "attributes": [
                                            {"type": "int", "name": "id", "key": "PK"},
                                            {"type": "string", "name": "title"},
                                        ],
                                    },
                                ],
                                "relations": [
                                    {"from": "STUDENT", "to": "COURSE", "label": "selects", "type": "}o--o{"}
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            def fake_render(_renderer, _source, svg_path, png_path):
                self.assertIsNone(svg_path)
                self.assertIsNotNone(png_path)
                png_path.write_bytes(b"png")

            args = SimpleNamespace(
                check=False,
                config=str(plan_path),
                output_dir=str(output),
                direct=True,
                format=None,
                keep_report=False,
            )
            with patch.object(MODULE, "parse_args", return_value=args), patch.object(
                MODULE, "render_source", side_effect=fake_render
            ):
                MODULE.main()

            self.assertEqual([path.name for path in output.iterdir()], ["simple_er.png"])

    def test_all_declared_diagram_types_build_editable_sources(self):
        plan = json.loads((ROOT / "examples" / "diagram_plan.all-types.json").read_text(encoding="utf-8"))
        builtins = [item for item in plan["diagrams"] if item["kind"] in MODULE.RENDERER_MAP]
        custom = [item for item in plan["diagrams"] if item["kind"] not in MODULE.RENDERER_MAP]
        self.assertEqual({item["kind"] for item in builtins}, set(MODULE.RENDERER_MAP))
        self.assertEqual({item["renderer"] for item in custom}, {"mermaid", "d2", "plantuml"})
        for item in plan["diagrams"]:
            source, extension, renderer = MODULE.build_source(item)
            self.assertTrue(source.strip(), item["name"])
            self.assertEqual(extension, MODULE.SOURCE_EXTENSIONS[renderer], item["name"])

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

    def test_deployment_diagram_uses_portable_node_containers(self):
        source, extension, renderer = MODULE.build_source(
            {
                "name": "deployment",
                "kind": "deployment_diagram",
                "nodes": [
                    {"id": "client", "name": "Browser", "type": "device"},
                    {"id": "db", "name": "Database", "type": "database"},
                ],
                "connections": [{"from": "Browser", "to": "Database", "label": "SQL"}],
            }
        )
        self.assertEqual((extension, renderer), (".puml", "plantuml"))
        self.assertIn('node "Browser" as client <<device>> {', source)
        self.assertIn('node "Database" as db <<database>> {', source)
        self.assertNotIn('device "Browser"', source)


if __name__ == "__main__":
    unittest.main()
