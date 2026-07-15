# Video module

Use this module for video analysis, screen recording, creation, and processing.

## Actions

- `analyze`: inspect streams, duration, codecs, dimensions, sampled frames, and content evidence.
- `record`: capture a real application or workflow demonstration.
- `create`: assemble approved images, narration, audio, and transitions into a video.
- `process`: trim, transcode, compress, merge, or extract evidence.

Use `video_process.py` for analysis and screen recording. Use the available FFmpeg/video skills for more complex production. Record the exact command, input paths, output path, duration, dimensions, codec, and verification result.

Do not fabricate a demonstration when the request requires real operation evidence. Inspect the final video with `ffprobe` or an equivalent backend and sample frames before registering it as an artifact.
