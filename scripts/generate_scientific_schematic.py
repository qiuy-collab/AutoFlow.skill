#!/usr/bin/env python3
"""Generate scientific schematic drafts through AutoFlow's configured image upstream."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


SIZE_BY_ASPECT = {
    "16:9": "2048x1152",
    "4:3": "1536x1152",
    "3:2": "1536x1024",
    "1:1": "2048x2048",
    "9:16": "1152x2048",
}


def read_optional_text(text: str | None, path: str | None) -> str:
    parts: list[str] = []
    if text:
        parts.append(text.strip())
    if path:
        parts.append(Path(path).read_text(encoding="utf-8").strip())
    return "\n\n".join(part for part in parts if part)


def build_prompt(args: argparse.Namespace) -> str:
    custom = read_optional_text(args.prompt, args.prompt_file)
    if custom and args.raw:
        return custom

    blocks: list[str] = []
    if args.title:
        blocks.append(f"Title or central claim: {args.title.strip()}")
    abstract = read_optional_text(args.abstract, args.abstract_file)
    if abstract:
        blocks.append(f"Article summary:\n{abstract}")
    if args.panel_map:
        blocks.append(f"Desired visual flow:\n{args.panel_map.strip()}")
    if custom:
        blocks.append(f"Additional instructions:\n{custom}")
    if not blocks:
        raise SystemExit(
            "Provide --prompt/--prompt-file or at least one of --title, "
            "--abstract/--abstract-file, or --panel-map."
        )

    role = args.style or (
        "Create a clean publication-grade scientific graphical abstract, mechanism "
        "schematic, or concept illustration. Use a flat vector-like visual language, "
        "restrained palette, clear hierarchy, simple arrows, minimal short labels, "
        "and an uncluttered background."
    )
    integrity = (
        "Scientific integrity: show only the supplied mechanisms and entities. Do not "
        "invent quantitative values, p-values, microscopy findings, institutional or "
        "journal logos, or unsupported experimental claims. Treat the result as a "
        "conceptual draft rather than experimental evidence. Keep text short because "
        "publication labels may need deterministic redrawing."
    )
    return "\n\n".join([role, integrity, *blocks])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate scientific schematics with AutoFlow BASEURL/APIKEY and gpt-image-2."
    )
    parser.add_argument("--title")
    parser.add_argument("--abstract")
    parser.add_argument("--abstract-file")
    parser.add_argument("--panel-map")
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument("--style")
    parser.add_argument("--raw", action="store_true")
    parser.add_argument("--reference-image", help="Optional local reference image for img2img.")
    parser.add_argument("--output-dir", default="scientific_schematic")
    parser.add_argument("--basename")
    parser.add_argument("--aspect-ratio", default="16:9")
    parser.add_argument("--size", help="Explicit upstream image size; overrides --aspect-ratio.")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prompt = build_prompt(args)
    size = args.size or SIZE_BY_ASPECT.get(args.aspect_ratio)
    if not size:
        raise SystemExit("Unknown aspect ratio; pass --size explicitly.")
    basename = args.basename or time.strftime("scientific_schematic_%Y%m%d_%H%M%S")
    payload = {
        "provider": "autoflow_env_upstream",
        "model": "gpt-image-2",
        "prompt": prompt,
        "size": size,
        "reference_image": args.reference_image,
    }
    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    from generate_images import generate_image_single

    output_dir = Path(args.output_dir).expanduser().resolve()
    result = generate_image_single(
        prompt=prompt,
        output_dir=str(output_dir),
        resolution=size,
        filename=basename,
        timeout=args.timeout,
        ref_image=args.reference_image,
    )
    if not result:
        raise SystemExit(
            "Scientific schematic generation failed. Verify AutoFlow .env BASEURL/APIKEY "
            "and the gpt-image-2 upstream; no fallback provider was used."
        )
    metadata = {
        "$schema": "autoflow/scientific-schematic/1.0",
        **payload,
        "output": str(Path(result).resolve()),
        "conceptual_draft": True,
    }
    metadata_path = output_dir / f"{basename}_request_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(result)
    print(metadata_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
