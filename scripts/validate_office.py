from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


SCHEMA = "autoflow/office-validation/1.0"
OFFICE_FORMATS = {"word", "ppt", "excel"}
FORMAT_SUFFIX = {"word": ".docx", "ppt": ".pptx", "excel": ".xlsx"}
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
DRAWINGML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
PRESENTATION_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
W = f"{{{WORD_NS}}}"
A = f"{{{DRAWINGML_NS}}}"
S = f"{{{SPREADSHEET_NS}}}"
P = f"{{{PRESENTATION_NS}}}"
REL = f"{{{REL_NS}}}"
PLACEHOLDER_PATTERNS = (
    re.compile(r"\{\{[^{}]+\}\}"),
    re.compile(r"\[(?:TODO|TBD)\]", re.IGNORECASE),
    re.compile(r"(?:请在此处填写|此处替换|示例内容|样例内容|占位符)"),
)
FORMAT_INSTRUCTION_PATTERNS = (
    re.compile(r"(?:字号要求|字体要求|行距要求|格式要求|页边距要求)"),
    re.compile(r"(?:请使用|请设置).{0,12}(?:字号|字体|行距|页边距)"),
)
AGENT_VOICE_PATTERNS = (
    re.compile(r"\b(?:agent|assistant|claude|chatgpt)\b", re.IGNORECASE),
    re.compile(r"(?:我已经为你|根据你的要求生成|作为AI|作为人工智能)"),
)
CAPTION_RE = re.compile(r"^\s*图\s*([0-9]+(?:[-.]\d+)*)\s+\S+")


class ValidationFailure(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_plan(path: Path | None) -> dict:
    if path is None:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"Cannot read office plan: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationFailure("Office plan must be a JSON object")
    schema = data.get("$schema")
    if schema and schema != "autoflow/office-plan/1.0":
        raise ValidationFailure("Office plan must use autoflow/office-plan/1.0")
    return data


def load_engine_report(path: Path | None, document: Path) -> tuple[bool, str, dict | None]:
    """Validate the engine (officecli) report supplied by office_engine.py."""
    if path is None:
        return False, "No officecli engine report supplied", None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"Cannot read officecli engine report: {exc}", None
    recorded = data.get("document") or {}
    passed = (
        data.get("$schema") == "autoflow/office-engine-validation/1.0"
        and data.get("overall_pass") is True
        and Path(str(recorded.get("path", ""))).expanduser().resolve() == document.resolve()
        and recorded.get("sha256") == sha256(document)
    )
    mode = str(data.get("engine", {}).get("name", "officecli"))
    evidence = (
        f"officecli validation passed (engine={mode})" if passed else "officecli engine report is failed, stale, or for a different document"
    )
    return passed, evidence, data


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.iter(f"{W}t")).strip()


def paragraph_style(paragraph: ET.Element) -> str:
    style = paragraph.find(f"{W}pPr/{W}pStyle")
    return style.get(f"{W}val", "") if style is not None else ""


def table_shapes(root: ET.Element) -> list[tuple[int, tuple[int, ...]]]:
    shapes: list[tuple[int, tuple[int, ...]]] = []
    for table in root.iter(f"{W}tbl"):
        rows = list(table.findall(f"{W}tr"))
        shapes.append((len(rows), tuple(len(row.findall(f"{W}tc")) for row in rows)))
    return shapes


def section_settings(root: ET.Element) -> list[dict[str, dict[str, str]]]:
    result: list[dict[str, dict[str, str]]] = []
    for section in root.iter(f"{W}sectPr"):
        record: dict[str, dict[str, str]] = {}
        for name in ("pgSz", "pgMar", "cols", "docGrid"):
            node = section.find(f"{W}{name}")
            if node is not None:
                record[name] = {key.split("}")[-1]: value for key, value in sorted(node.attrib.items())}
        result.append(record)
    return result


def relationship_errors(archive: zipfile.ZipFile) -> list[str]:
    names = set(archive.namelist())
    errors: list[str] = []
    for rel_name in sorted(name for name in names if name.endswith(".rels")):
        try:
            root = ET.fromstring(archive.read(rel_name))
        except ET.ParseError as exc:
            errors.append(f"Invalid relationships XML {rel_name}: {exc}")
            continue
        rel_path = Path(rel_name)
        if rel_name == "_rels/.rels":
            source_dir = ""
        else:
            source_name = rel_path.name[:-5]
            source_dir = str(rel_path.parent.parent).replace("\\", "/")
            if source_name and source_name not in {".rels", ""}:
                source_part = posixpath.join(source_dir, source_name)
                source_dir = posixpath.dirname(source_part)
        for relationship in root.findall(f"{REL}Relationship"):
            if relationship.get("TargetMode") == "External":
                continue
            target = relationship.get("Target", "")
            if target.startswith("/"):
                # Package-absolute target (e.g. "/word/settings.xml"): resolve from the archive root.
                resolved = posixpath.normpath(target.lstrip("/"))
            else:
                resolved = posixpath.normpath(posixpath.join(source_dir, target))
            if resolved not in names:
                errors.append(f"Broken relationship {rel_name} -> {target}")
    return errors


def _open_archive(path: Path, suffix: str) -> zipfile.ZipFile:
    if not path.is_file() or path.suffix.lower() != suffix:
        raise ValidationFailure(f"Not an existing {suffix} file: {path}")
    archive = zipfile.ZipFile(path)
    bad_member = archive.testzip()
    if bad_member:
        archive.close()
        raise ValidationFailure(f"Corrupt {suffix} member: {bad_member}")
    return archive


def inspect_docx(path: Path) -> dict:
    try:
        with _open_archive(path, ".docx") as archive:
            names = set(archive.namelist())
            required = {"[Content_Types].xml", "word/document.xml"}
            missing = required - names
            if missing:
                raise ValidationFailure("DOCX is missing required parts: " + ", ".join(sorted(missing)))
            root = ET.fromstring(archive.read("word/document.xml"))
            paragraphs = list(root.iter(f"{W}p"))
            records = []
            for paragraph in paragraphs:
                drawing_count = len(list(paragraph.iter(f"{W}drawing"))) + len(list(paragraph.iter(f"{W}pict")))
                records.append(
                    {
                        "text": paragraph_text(paragraph),
                        "style": paragraph_style(paragraph),
                        "drawing_count": drawing_count,
                    }
                )
            full_text = "\n".join(item["text"] for item in records if item["text"])
            instructions = " ".join(node.text or "" for node in root.iter(f"{W}instrText"))
            return {
                "paragraphs": records,
                "full_text": full_text,
                "has_toc": "TOC" in instructions.upper() or any(item["text"] == "目录" for item in records),
                "tables": table_shapes(root),
                "sections": section_settings(root),
                "headers": sorted(name for name in names if re.fullmatch(r"word/header\d+\.xml", name)),
                "footers": sorted(name for name in names if re.fullmatch(r"word/footer\d+\.xml", name)),
                "relationship_errors": relationship_errors(archive),
            }
    except (zipfile.BadZipFile, ET.ParseError) as exc:
        raise ValidationFailure(f"Invalid DOCX package: {exc}") from exc


def inspect_pptx(path: Path) -> dict:
    try:
        with _open_archive(path, ".pptx") as archive:
            names = set(archive.namelist())
            required = {"[Content_Types].xml", "ppt/presentation.xml"}
            missing = required - names
            if missing:
                raise ValidationFailure("PPTX is missing required parts: " + ", ".join(sorted(missing)))
            presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
            slide_ids = presentation.findall(f".//{P}sldId")
            slide_names = sorted(name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name))
            slide_texts: list[str] = []
            slide_titles: list[str] = []
            for slide_name in slide_names:
                try:
                    root = ET.fromstring(archive.read(slide_name))
                except ET.ParseError as exc:
                    raise ValidationFailure(f"Invalid slide XML {slide_name}: {exc}") from exc
                texts = [node.text or "" for node in root.iter(f"{A}t")]
                slide_texts.append(" ".join(text.strip() for text in texts if text.strip()))
                title_nodes: list[ET.Element] = []
                for sp in root.iter(f"{P}sp"):
                    nv_pr = sp.find(f"{P}nvSpPr")
                    if nv_pr is None:
                        continue
                    c_pr = nv_pr.find(f"{P}cNvPr")
                    shape_name = (c_pr.get("name") or "") if c_pr is not None else ""
                    # Accept standard "Title 1" placeholders and officecli's "Title" shape.
                    if shape_name == "Title" or shape_name.startswith("Title "):
                        title_nodes.append(sp)
                title_texts = [" ".join(node.text or "" for node in sp.iter(f"{A}t")).strip() for sp in title_nodes]
                slide_titles.append(next((t for t in title_texts if t), ""))
            return {
                "slide_count_declared": len(slide_ids),
                "slide_parts": slide_names,
                "slide_texts": slide_texts,
                "slide_titles": slide_titles,
                "relationship_errors": relationship_errors(archive),
            }
    except (zipfile.BadZipFile, ET.ParseError) as exc:
        raise ValidationFailure(f"Invalid PPTX package: {exc}") from exc


def inspect_xlsx(path: Path) -> dict:
    try:
        with _open_archive(path, ".xlsx") as archive:
            names = set(archive.namelist())
            required = {"[Content_Types].xml", "xl/workbook.xml"}
            missing = required - names
            if missing:
                raise ValidationFailure("XLSX is missing required parts: " + ", ".join(sorted(missing)))
            workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            sheets = workbook.findall(f"{S}sheets/{S}sheet")
            sheet_names = [sheet.get("name", "") for sheet in sheets]
            sheet_parts = sorted(name for name in names if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name))
            cell_texts: list[str] = []
            for sheet_part in sheet_parts:
                try:
                    root = ET.fromstring(archive.read(sheet_part))
                except ET.ParseError as exc:
                    raise ValidationFailure(f"Invalid worksheet XML {sheet_part}: {exc}") from exc
                for cell in root.iter(f"{S}c"):
                    value = cell.find(f"{S}v")
                    text = value.text if value is not None and value.text else ""
                    if text:
                        cell_texts.append(text)
            return {
                "sheets": sheet_names,
                "worksheet_parts": sheet_parts,
                "cell_texts": cell_texts,
                "relationship_errors": relationship_errors(archive),
            }
    except (zipfile.BadZipFile, ET.ParseError) as exc:
        raise ValidationFailure(f"Invalid XLSX package: {exc}") from exc


def inspect(path: Path, format_name: str) -> dict:
    if format_name == "word":
        return inspect_docx(path)
    if format_name == "ppt":
        return inspect_pptx(path)
    return inspect_xlsx(path)


def check(name: str, passed: bool, evidence: str) -> dict:
    return {"name": name, "status": "passed" if passed else "failed", "evidence": evidence}


def review_passed(plan: dict, key: str) -> tuple[bool, str]:
    review = plan.get(key) or {}
    evidence = str(review.get("evidence", "")).strip()
    return review.get("status") == "passed" and bool(evidence), evidence or "No review evidence recorded"


def validate(
    document: Path,
    format_name: str,
    template: Path | None,
    plan: dict,
    engine_report_path: Path | None = None,
) -> dict:
    if format_name not in OFFICE_FORMATS:
        raise ValidationFailure(f"Unsupported office format: {format_name}")
    document_info = inspect(document, format_name)
    template_info = inspect(template, format_name) if template is not None else None
    checks: list[dict] = []

    if format_name == "word":
        full_text = document_info["full_text"]
        placeholder_hits = [pattern.pattern for pattern in PLACEHOLDER_PATTERNS if pattern.search(full_text)]
        checks.append(check("no_unresolved_placeholders", not placeholder_hits, f"matched={placeholder_hits or 'none'}"))
        instruction_hits = [
            pattern.pattern
            for pattern in FORMAT_INSTRUCTION_PATTERNS
            if pattern.search(full_text)
            and (template_info is None or not pattern.search(template_info["full_text"]))
        ]
        checks.append(check("no_template_instructions_in_body", not instruction_hits, f"matched={instruction_hits or 'none'}"))
        voice_hits = [pattern.pattern for pattern in AGENT_VOICE_PATTERNS if pattern.search(full_text)]
        checks.append(check("no_agent_voice", not voice_hits, f"matched={voice_hits or 'none'}"))
    else:
        texts = (
            document_info["slide_texts"] if format_name == "ppt" else document_info["cell_texts"]
        )
        full_text = "\n".join(texts)
        placeholder_hits = [pattern.pattern for pattern in PLACEHOLDER_PATTERNS if pattern.search(full_text)]
        checks.append(check("no_unresolved_placeholders", not placeholder_hits, f"matched={placeholder_hits or 'none'}"))
        voice_hits = [pattern.pattern for pattern in AGENT_VOICE_PATTERNS if pattern.search(full_text)]
        checks.append(check("no_agent_voice", not voice_hits, f"matched={voice_hits or 'none'}"))

    checks.append(
        check(
            "relationships_resolve",
            not document_info["relationship_errors"],
            "; ".join(document_info["relationship_errors"]) or "All internal relationships resolve",
        )
    )

    engine_passed, engine_evidence, engine_report = load_engine_report(engine_report_path, document)
    if plan.get("require_engine_validation", False) or engine_report_path is not None:
        checks.append(check("officecli_engine", engine_passed, engine_evidence))

    metrics: dict = {}
    if format_name == "word":
        paragraphs = document_info["paragraphs"]
        image_indices: list[int] = []
        for index, item in enumerate(paragraphs):
            image_indices.extend([index] * item["drawing_count"])
        captions = [(index, CAPTION_RE.match(item["text"])) for index, item in enumerate(paragraphs)]
        captions = [(index, match.group(1)) for index, match in captions if match]
        minimum_images = int(plan.get("minimum_image_count", 0) or 0)
        checks.append(
            check(
                "minimum_image_count",
                len(image_indices) >= minimum_images,
                f"document_images={len(image_indices)}, required={minimum_images}",
            )
        )

        if plan.get("require_caption_pairing", False):
            paired: list[tuple[int, int]] = []
            for image_index in image_indices:
                next_nonempty = [
                    index
                    for index in range(image_index + 1, min(len(paragraphs), image_index + 4))
                    if paragraphs[index]["text"]
                ][:2]
                caption_index = next((index for index in next_nonempty if CAPTION_RE.match(paragraphs[index]["text"])), None)
                if caption_index is not None:
                    paired.append((image_index, caption_index))
            checks.append(
                check(
                    "figure_caption_pairing",
                    len(paired) == len(image_indices) == len(captions),
                    f"images={len(image_indices)}, paired={len(paired)}, captions={len(captions)}",
                )
            )
            if plan.get("require_lead_in", True):
                lead_ins = sum(
                    1 for image_index, _ in paired if any(paragraphs[i]["text"] for i in range(max(0, image_index - 2), image_index))
                )
                checks.append(check("figure_lead_in", lead_ins == len(paired), f"paired={len(paired)}, lead_ins={lead_ins}"))
            if plan.get("require_analysis_after_caption", True):
                analyses = sum(
                    1
                    for _, caption_index in paired
                    if any(
                        paragraphs[i]["text"] and not CAPTION_RE.match(paragraphs[i]["text"])
                        for i in range(caption_index + 1, min(len(paragraphs), caption_index + 3))
                    )
                )
                checks.append(
                    check("figure_analysis_paragraph", analyses == len(paired), f"paired={len(paired)}, analyses={analyses}")
                )
            if plan.get("require_sequential_captions", True):
                labels = [label for _, label in captions]
                checks.append(check("caption_numbers_unique", len(labels) == len(set(labels)), f"labels={labels}"))

        if template is not None:
            assert template_info is not None
            checks.append(check("output_does_not_overwrite_template", document.resolve() != template.resolve(), str(template.resolve())))
            if plan.get("preserve_section_settings", True):
                checks.append(
                    check(
                        "section_settings_preserved",
                        document_info["sections"] == template_info["sections"],
                        f"template_sections={len(template_info['sections'])}, output_sections={len(document_info['sections'])}",
                    )
                )
            if plan.get("preserve_table_structure", True):
                checks.append(
                    check(
                        "table_structure_preserved",
                        document_info["tables"] == template_info["tables"],
                        f"template_tables={template_info['tables']}, output_tables={document_info['tables']}",
                    )
                )
            checks.append(
                check(
                    "header_footer_parts_preserved",
                    document_info["headers"] == template_info["headers"]
                    and document_info["footers"] == template_info["footers"],
                    f"headers={document_info['headers']}, footers={document_info['footers']}",
                )
            )
            if plan.get("require_toc_if_template_has_toc", True) and template_info["has_toc"]:
                checks.append(check("toc_preserved", document_info["has_toc"], "Template contains a TOC"))

        metrics = {
            "paragraphs": len(paragraphs),
            "document_images": len(image_indices),
            "captions": len(captions),
            "tables": len(document_info["tables"]),
            "has_toc": document_info["has_toc"],
        }
    elif format_name == "ppt":
        declared = int(document_info["slide_count_declared"])
        parts = len(document_info["slide_parts"])
        checks.append(check("slide_parts_match_declared", declared == parts, f"declared={declared}, parts={parts}"))
        empty_titles = [i + 1 for i, title in enumerate(document_info["slide_titles"]) if not title]
        checks.append(check("slide_titles_present", not empty_titles, f"missing_titles={empty_titles or 'none'}"))
        duplicate_titles = [
            title
            for title in {t for t in document_info["slide_titles"] if t}
            if document_info["slide_titles"].count(title) > 1
        ]
        checks.append(check("slide_titles_unique", not duplicate_titles, f"duplicates={duplicate_titles or 'none'}"))
        metrics = {
            "slides": declared,
            "slide_parts": parts,
            "slides_with_text": sum(1 for text in document_info["slide_texts"] if text.strip()),
        }
    else:
        checks.append(
            check(
                "sheets_resolve",
                len(document_info["sheets"]) > 0 and len(document_info["sheets"]) == len(document_info["worksheet_parts"]),
                f"sheets={document_info['sheets']}, worksheet_parts={len(document_info['worksheet_parts'])}",
            )
        )
        metrics = {
            "sheets": len(document_info["sheets"]),
            "worksheet_parts": len(document_info["worksheet_parts"]),
            "non_empty_cells": len(document_info["cell_texts"]),
        }

    if plan.get("require_student_voice", False):
        passed, evidence = review_passed(plan, "student_voice_review")
        checks.append(check("student_voice_review", passed, evidence))
    if plan.get("require_visual_review", True):
        passed, evidence = review_passed(plan, "visual_review")
        checks.append(check("rendered_document_review", passed, evidence))

    overall_pass = all(item["status"] == "passed" for item in checks)
    return {
        "$schema": SCHEMA,
        "format": format_name,
        "document": {
            "path": str(document.resolve()),
            "sha256": sha256(document),
            "size": document.stat().st_size,
        },
        "template": str(template.resolve()) if template else "",
        "metrics": metrics,
        "engine_validation": {
            "required": bool(plan.get("require_engine_validation", False)),
            "report": str(engine_report_path.resolve()) if engine_report_path else "",
            "engine": (engine_report or {}).get("engine", {}).get("name", ""),
        },
        "checks": checks,
        "overall_pass": overall_pass,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an AutoFlow office artifact (.docx/.pptx/.xlsx) against its template and plan.")
    parser.add_argument("--document", required=True)
    parser.add_argument("--format", required=True, choices=sorted(OFFICE_FORMATS))
    parser.add_argument("--template")
    parser.add_argument("--plan")
    parser.add_argument("--engine-report", help="Report produced by office_engine.py validate.")
    parser.add_argument("--report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_path = Path(args.report).expanduser().resolve()
    try:
        report = validate(
            Path(args.document).expanduser().resolve(),
            args.format,
            Path(args.template).expanduser().resolve() if args.template else None,
            load_plan(Path(args.plan).expanduser().resolve() if args.plan else None),
            Path(args.engine_report).expanduser().resolve() if args.engine_report else None,
        )
    except ValidationFailure as exc:
        report = {
            "$schema": SCHEMA,
            "format": args.format,
            "document": {"path": str(Path(args.document).expanduser().resolve()), "sha256": "", "size": 0},
            "checks": [{"name": "office_package", "status": "failed", "evidence": str(exc)}],
            "overall_pass": False,
        }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("overall_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
