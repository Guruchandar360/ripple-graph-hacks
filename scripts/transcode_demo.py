"""Optional media packaging: pip install imageio-ffmpeg==0.6.0 first."""

import subprocess
from pathlib import Path

import imageio_ffmpeg

root = Path(__file__).resolve().parent.parent
subprocess.run(
    [
        imageio_ffmpeg.get_ffmpeg_exe(),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(root / "demo/ripple-demo.webm"),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-an",
        str(root / "demo/ripple-demo.mp4"),
    ],
    check=True,
)
