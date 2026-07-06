import argparse
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Build a supplement prompt config for only the images that still need regeneration.")
    parser.add_argument("--config", required=True, help="Path to the base prompt_config.json")
    parser.add_argument("--output", default=None, help="Output path. Default: prompt_config.supplement.json next to the base config.")
    parser.add_argument("--names", nargs="*", default=[], help="Explicit image names to keep in the supplement config.")
    parser.add_argument("--missing-only", action="store_true", help="Keep only images whose output PNG does not exist yet.")
    parser.add_argument("--report", default=None, help="Optional image_generation_report.json path. Failed images from the report will be included.")
    return parser.parse_args()


def main():
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    images = config.get("images", [])
    output_dir = Path(config.get("output_dir") or (config_path.parent / "generated_images")).expanduser().resolve()
    selected = set(args.names)

    if args.report:
        report_path = Path(args.report).expanduser().resolve()
        if not report_path.exists():
            raise SystemExit(f"Report not found: {report_path}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        selected.update(report.get("failed_image_names", []))

    if args.missing_only:
        for image in images:
            name = image.get("name")
            if name and not (output_dir / f"{name}.png").exists():
                selected.add(name)

    if not selected:
        raise SystemExit("No image names selected. Use --names, --missing-only, or --report.")

    filtered = [image for image in images if image.get("name") in selected]
    if not filtered:
        raise SystemExit("Selected image names did not match any entries in the base config.")

    supplement = dict(config)
    supplement["images"] = filtered
    supplement["total_count"] = len(filtered)
    supplement["source_config"] = str(config_path)
    supplement["supplement_reason"] = "manual_or_partial_regeneration"
    supplement["supplement_image_names"] = [image.get("name") for image in filtered]

    output_path = Path(args.output).expanduser().resolve() if args.output else (config_path.parent / "prompt_config.supplement.json")
    output_path.write_text(json.dumps(supplement, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Supplement config written: {output_path}")
    print(f"Image count: {len(filtered)}")


if __name__ == "__main__":
    main()
