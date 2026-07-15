import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def find_tool(name: str):
    local_install = Path.home() / "Tools" / "ffmpeg" / "bin" / f"{name}.exe"
    if local_install.exists():
        return str(local_install)
    local = shutil.which(name)
    if local:
        return local
    vendor = skill_root() / "vendor" / "ffmpeg" / "bin" / f"{name}.exe"
    if vendor.exists():
        return str(vendor)
    return None


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze videos and record screen evidence for AutoFlow.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--input", required=True, help="Video file to analyze.")
    analyze.add_argument("--output", required=True, help="JSON analysis output path.")
    analyze.add_argument("--sample-frames-dir", help="Optional directory for sampled frames.")
    analyze.add_argument("--max-frames", type=int, default=5)

    record = subparsers.add_parser("record-screen")
    record.add_argument("--output", required=True, help="Output .mp4/.avi path.")
    record.add_argument("--seconds", type=float, default=10)
    record.add_argument("--fps", type=float, default=15)
    record.add_argument("--monitor", type=int, default=1, help="mss monitor index. 1 is primary in most setups.")

    return parser.parse_args()


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ffprobe_analyze(input_path: Path):
    ffprobe = find_tool("ffprobe")
    if not ffprobe:
        return None
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-print_format",
        "json",
        str(input_path),
    ]
    completed = subprocess.run(cmd, text=True, capture_output=True, check=True)
    return json.loads(completed.stdout)


def pyav_analyze(input_path: Path, sample_dir: Path | None, max_frames: int):
    import av

    result = {
        "backend": "pyav",
        "file": str(input_path),
        "streams": [],
        "sample_frames": [],
    }
    with av.open(str(input_path)) as container:
        result["duration_seconds"] = float(container.duration / av.time_base) if container.duration else None
        for stream in container.streams:
            stream_info = {
                "type": stream.type,
                "index": stream.index,
                "codec": stream.codec_context.name if stream.codec_context else None,
                "duration": stream.duration,
                "time_base": str(stream.time_base),
            }
            if stream.type == "video":
                stream_info.update(
                    {
                        "width": stream.codec_context.width,
                        "height": stream.codec_context.height,
                        "average_rate": str(stream.average_rate) if stream.average_rate else None,
                        "frames": stream.frames,
                    }
                )
            if stream.type == "audio":
                stream_info.update(
                    {
                        "sample_rate": stream.codec_context.sample_rate,
                        "channels": stream.codec_context.channels,
                    }
                )
            result["streams"].append(stream_info)

        video_stream = next((s for s in container.streams if s.type == "video"), None)
        if sample_dir and video_stream:
            sample_dir.mkdir(parents=True, exist_ok=True)
            captured = 0
            for frame in container.decode(video=video_stream.index):
                if captured >= max_frames:
                    break
                target = sample_dir / f"frame_{captured + 1:03d}.png"
                frame.to_image().save(target)
                result["sample_frames"].append(str(target.resolve()))
                captured += 1
    return result


def opencv_analyze(input_path: Path, sample_dir: Path | None, max_frames: int):
    import cv2

    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV could not open video: {input_path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps else None
    result = {
        "backend": "opencv",
        "file": str(input_path),
        "duration_seconds": duration,
        "streams": [
            {
                "type": "video",
                "width": width,
                "height": height,
                "average_rate": fps,
                "frames": frame_count,
            }
        ],
        "sample_frames": [],
    }
    if sample_dir:
        sample_dir.mkdir(parents=True, exist_ok=True)
        step = max(frame_count // max(max_frames, 1), 1)
        captured = 0
        current = 0
        while captured < max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            if current % step == 0:
                target = sample_dir / f"frame_{captured + 1:03d}.png"
                cv2.imwrite(str(target), frame)
                result["sample_frames"].append(str(target.resolve()))
                captured += 1
            current += 1
    cap.release()
    return result


def analyze_video(input_path: Path, output_path: Path, sample_dir: Path | None, max_frames: int):
    errors = []
    try:
        result = pyav_analyze(input_path, sample_dir, max_frames)
    except Exception as exc:
        errors.append(f"pyav failed: {exc}")
        try:
            result = opencv_analyze(input_path, sample_dir, max_frames)
        except Exception as cv_exc:
            errors.append(f"opencv failed: {cv_exc}")
            probe = ffprobe_analyze(input_path)
            if probe is None:
                raise SystemExit("No video analyzer succeeded:\n" + "\n".join(errors))
            result = {"backend": "ffprobe", "file": str(input_path), "probe": probe}
    result["errors"] = errors
    write_json(output_path, result)
    print(f"Video analysis written: {output_path}")


def record_screen(output_path: Path, seconds: float, fps: float, monitor_index: int):
    try:
        import cv2
        import mss
        import numpy as np
    except Exception as exc:
        raise SystemExit(
            "Screen recording needs mss, opencv-python, and numpy. "
            "Install them or use OBS/ffmpeg as the external recording fallback. "
            f"Import error: {exc}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with mss.MSS() as sct:
        if monitor_index >= len(sct.monitors):
            raise SystemExit(f"Monitor index {monitor_index} not available. Found {len(sct.monitors) - 1} monitor(s).")
        monitor = sct.monitors[monitor_index]
        width = monitor["width"]
        height = monitor["height"]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        if not writer.isOpened():
            raise SystemExit(f"OpenCV VideoWriter could not open output: {output_path}")
        deadline = time.time() + seconds
        frame_delay = 1.0 / fps if fps else 0
        while time.time() < deadline:
            frame = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            writer.write(frame)
            if frame_delay:
                time.sleep(frame_delay)
        writer.release()
    print(f"Screen recording written: {output_path}")


def main():
    args = parse_args()
    if args.command == "analyze":
        input_path = Path(args.input).expanduser().resolve()
        output_path = Path(args.output).expanduser().resolve()
        sample_dir = Path(args.sample_frames_dir).expanduser().resolve() if args.sample_frames_dir else None
        analyze_video(input_path, output_path, sample_dir, args.max_frames)
    elif args.command == "record-screen":
        record_screen(Path(args.output).expanduser().resolve(), args.seconds, args.fps, args.monitor)


if __name__ == "__main__":
    main()
