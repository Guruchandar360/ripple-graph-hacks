"""Package the actual UI capture as a silent, self-explanatory captioned MP4."""

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent.parent
FILM = ROOT / "artifacts/submission-film"


def stamp(seconds):
    milliseconds = round(seconds * 1000)
    seconds, ms = divmod(milliseconds, 1000)
    minutes, sec = divmod(seconds, 60)
    hours, minute = divmod(minutes, 60)
    return f"{hours:02}:{minute:02}:{sec:02},{ms:03}"


def main():
    timing = json.loads((FILM / "timing.json").read_text())["timing"]
    script = json.loads((ROOT / "demo/film-script.json").read_text(encoding="utf-8"))
    chapters = {c["id"]: c for c in script["chapters"]}
    trim = timing[0]["start"]
    duration = timing[-1]["start"] + timing[-1]["display_seconds"] - 0.2 - trim
    if duration >= 180:
        raise SystemExit(f"Film is {duration:.2f}s; shorten before publishing.")
    subtitles = []
    metadata = [
        ";FFMETADATA1",
        "title=Ripple — evidence-driven incident recovery",
        "comment=Silent explanatory captions. Actual Gemini replays; synthetic incidents; AI-assisted implementation.",
    ]
    for item in timing:
        start = item["start"] - trim
        sentences = re.split(r"(?<=[.!?])\s+", item["text"])
        words = sum(len(s.split()) for s in sentences)
        cursor = start
        for sentence in sentences:
            length = (item["display_seconds"] - 0.2) * len(sentence.split()) / words
            subtitles.append(
                f"{len(subtitles) + 1}\n{stamp(cursor)} --> {stamp(cursor + length)}\n{sentence}\n"
            )
            cursor += length
        metadata.extend(
            [
                "[CHAPTER]",
                "TIMEBASE=1/1000",
                f"START={round(start * 1000)}",
                f"END={round((start + item['display_seconds'] - 0.2) * 1000)}",
                f"title={chapters[item['id']]['title']}",
            ]
        )
    srt = ROOT / "demo/ripple-demo.srt"
    srt.write_text("\n".join(subtitles), encoding="utf-8")
    (FILM / "chapters.txt").write_text("\n".join(metadata), encoding="utf-8")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    target = ROOT / "demo/ripple-demo.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-ss",
            str(trim),
            "-i",
            str(FILM / "latest-ui.webm"),
            "-i",
            str(srt),
            "-i",
            str(FILM / "chapters.txt"),
            "-map",
            "0:v:0",
            "-map",
            "1:s:0",
            "-map_metadata",
            "2",
            "-map_chapters",
            "2",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "19",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-c:s",
            "mov_text",
            "-metadata:s:s:0",
            "language=eng",
            "-t",
            str(duration),
            "-movflags",
            "+faststart",
            str(target),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=(FILM / "encode.log").open("w"),
    )
    subprocess.run([ffmpeg, "-v", "error", "-xerror", "-i", str(target), "-f", "null", "-"], check=True)
    probe = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(target)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stderr
    assert "Audio:" not in probe and "Subtitle: mov_text" in probe and "1920x1080" in probe
    assert probe.count("Chapter #") == 12
    shutil.copyfile(FILM / "latest-ui.webm", ROOT / "demo/ripple-demo.webm")
    report = json.loads((ROOT / "demo/video.json").read_text(encoding="utf-8"))
    for key in ("narration", "voice"):
        report.pop(key, None)
    report.update(
        audio=False,
        captioned=True,
        burned_in_captions=True,
        caption_mode=script["caption_mode"],
        duration_seconds=round(duration, 3),
        full_decode_verified=True,
        sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        recorder_sha256=hashlib.sha256(
            (ROOT / "frontend/scripts/record-submission.mjs").read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
        silent_source_trim_start_seconds=trim,
        previous_video_commit="f44e5cfd192bbef8642955efb4f34f23f3d2d421",
        recording_scope="Actual application interactions with full explanatory captions/title cards. No audio track. Model output is explicitly replayed; no new model calls for filming.",
    )
    report["chapters"] = [
        {"id": i["id"], "start_seconds": round(i["start"] - trim, 3), "title": chapters[i["id"]]["title"]}
        for i in timing
    ]
    (ROOT / "demo/video.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Full-decode-verified {duration:.3f}s silent captioned 1920x1080 MP4; no audio stream.")


if __name__ == "__main__":
    main()
