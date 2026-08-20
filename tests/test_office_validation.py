from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_office.py"


def write_docx(path: Path, body_xml: str) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>{body_xml}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body>
</w:document>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("word/document.xml", document)


def paragraph(text: str, drawing: bool = False) -> str:
    visual = "<w:r><w:drawing/></w:r>" if drawing else ""
    return f"<w:p><w:r><w:t>{text}</w:t></w:r>{visual}</w:p>"


class OfficeValidationTests(unittest.TestCase):
    def run_validator(self, root: Path, document: Path, template: Path, plan: dict):
        plan_path = root / "office-plan.json"
        report_path = root / "office-validation.json"
        plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--document",
                str(document),
                "--format",
                "word",
                "--template",
                str(template),
                "--plan",
                str(plan_path),
                "--report",
                str(report_path),
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        return result, json.loads(report_path.read_text(encoding="utf-8"))

    def strict_plan(self):
        return {
            "$schema": "autoflow/office-plan/1.0",
            "minimum_image_count": 1,
            "require_caption_pairing": True,
            "require_lead_in": True,
            "require_analysis_after_caption": True,
            "require_sequential_captions": True,
            "preserve_section_settings": True,
            "preserve_table_structure": True,
            "require_toc_if_template_has_toc": True,
            "require_student_voice": True,
            "require_visual_review": True,
            "student_voice_review": {"status": "passed", "evidence": "Student narration sampled"},
            "visual_review": {"status": "passed", "evidence": "All rendered pages inspected"},
        }

    def test_strict_template_report_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            template = root / "template.docx"
            document = root / "result.docx"
            body = "".join(
                [
                    paragraph("下面展示系统运行结果。"),
                    paragraph("", drawing=True),
                    paragraph("图1 系统运行结果"),
                    paragraph("从图中可以看出系统功能运行正常。"),
                ]
            )
            write_docx(template, body)
            write_docx(document, body)
            result, report = self.run_validator(root, document, template, self.strict_plan())
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(report["overall_pass"])
            self.assertEqual(report["metrics"]["document_images"], 1)
            self.assertEqual(report["metrics"]["captions"], 1)

    def test_placeholder_and_missing_caption_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            template = root / "template.docx"
            document = root / "result.docx"
            template_body = paragraph("模板正文")
            output_body = paragraph("请在此处填写 {{student_name}}") + paragraph("", drawing=True)
            write_docx(template, template_body)
            write_docx(document, output_body)
            result, report = self.run_validator(root, document, template, self.strict_plan())
            self.assertNotEqual(result.returncode, 0)
            failed = {item["name"] for item in report["checks"] if item["status"] == "failed"}
            self.assertIn("no_unresolved_placeholders", failed)
            self.assertIn("figure_caption_pairing", failed)

    def test_format_instructions_inherited_from_template_do_not_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            template = root / "template.docx"
            document = root / "result.docx"
            inherited = paragraph("格式要求：正文使用宋体小四。")
            write_docx(template, inherited)
            write_docx(document, inherited + paragraph("这是学生填写的课程学习总结正文。"))
            plan = self.strict_plan()
            plan.update(
                {
                    "minimum_image_count": 0,
                    "require_caption_pairing": False,
                }
            )
            result, report = self.run_validator(root, document, template, plan)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            checks = {item["name"]: item for item in report["checks"]}
            self.assertEqual(checks["no_template_instructions_in_body"]["status"], "passed")

    def test_new_format_instructions_not_present_in_template_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            template = root / "template.docx"
            document = root / "result.docx"
            write_docx(template, paragraph("课程报告模板"))
            write_docx(document, paragraph("格式要求：正文使用宋体小四。"))
            plan = self.strict_plan()
            plan.update({"minimum_image_count": 0, "require_caption_pairing": False})
            result, report = self.run_validator(root, document, template, plan)
            self.assertNotEqual(result.returncode, 0)
            failed = {item["name"] for item in report["checks"] if item["status"] == "failed"}
            self.assertIn("no_template_instructions_in_body", failed)


if __name__ == "__main__":
    unittest.main()
