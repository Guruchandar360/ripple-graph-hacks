"""Mux the latest actual UI recording with locally generated narration and subtitles."""

import hashlib
import json
import math
import re
import shutil
import subprocess
import wave
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
    duration = timing[-1]["start"] + timing[-1]["speech_seconds"] + 1.3 - trim
    if duration >= 180:
        raise SystemExit(f"Film is {duration:.2f}s; shorten before publishing the three-minute edit.")
    with wave.open(str(ROOT / "artifacts/film-audio/opening.wav"), "rb") as first:
        params = first.getparams()
        rate, width, channels = params.framerate, params.sampwidth, params.nchannels
    mixed = bytearray(math.ceil(duration * rate) * width * channels)
    subtitles, metadata = (
        [],
        [
            ";FFMETADATA1",
            "title=Ripple — evidence-driven incident recovery",
            "comment=Actual native Gemini replays in the latest UI. Synthetic incidents. Locally synthesized narration. AI-assisted implementation.",
        ],
    )
    for item in timing:
        start = item["start"] - trim
        with wave.open(str(ROOT / f"artifacts/film-audio/{item['id']}.wav"), "rb") as wav:
            assert (
                wav.getframerate() == rate and wav.getsampwidth() == width and wav.getnchannels() == channels
            )
            frames = wav.readframes(wav.getnframes())
        offset = round(start * rate) * width * channels
        mixed[offset : offset + len(frames)] = frames
        sentences = re.split(r"(?<=[.!?])\s+", item["text"])
        words = sum(len(s.split()) for s in sentences)
        cursor = start
        for sentence in sentences:
            length = item["speech_seconds"] * len(sentence.split()) / words
            subtitles.append(
                f"{len(subtitles) + 1}\n{stamp(cursor)} --> {stamp(cursor + length)}\n{sentence}\n"
            )
            cursor += length
        metadata.extend(
            [
                "[CHAPTER]",
                "TIMEBASE=1/1000",
                f"START={round(start * 1000)}",
                f"END={round((start + item['speech_seconds'] + 1.3) * 1000)}",
                f"title={chapters[item['id']]['title']}",
            ]
        )
    with wave.open(str(FILM / "narration.wav"), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(width)
        wav.setframerate(rate)
        wav.writeframes(mixed)
    srt = ROOT / "demo/ripple-demo.srt"
    srt.write_text("\n".join(subtitles), encoding="utf-8")
    (FILM / "chapters.txt").write_text("\n".join(metadata), encoding="utf-8")
    archive = ROOT / "demo/development/cpu-video-v1"
    archive.mkdir(parents=True, exist_ok=True)
    for name in ["ripple-demo.mp4", "ripple-demo.webm", "video.json"]:
        if not (archive / name).exists():
            shutil.copyfile(ROOT / "demo" / name, archive / name)
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
            str(FILM / "narration.wav"),
            "-i",
            str(srt),
            "-i",
            str(FILM / "chapters.txt"),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-map",
            "2:s:0",
            "-map_metadata",
            "3",
            "-map_chapters",
            "3",
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
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-ar",
            "48000",
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
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
    # The source WebM is retained as a separate silent capture, with trim provenance.
    shutil.copyfile(FILM / "latest-ui.webm", ROOT / "demo/ripple-demo.webm")
    records = []
    native_source = json.loads((ROOT / "demo/live/sequence/repeatability.json").read_text())["source_commit"]
    for path in sorted((ROOT / "demo/live/sequence/replays").glob("*.json")):
        record = json.loads(path.read_text())
        records.append(
            {
                "phase": record["demonstration_phase"],
                "run_id": record["id"],
                "source_commit": native_source,
                "path": path.relative_to(ROOT).as_posix(),
            }
        )
    report = {
        "kind": "actual_agent_replay",
        "record_source": "native_cloud_sequence",
        "selection": "Latest UI recorded at source 36fc05c. Actual three-scenario native Gemini/Cloud sample; one complete sequence passed, not the native three-consecutive gate. Includes separate hosted HTTP receipt and separate CPU benchmark views.",
        "synthetic": True,
        "resolution": [1920, 1080],
        "captioned": True,
        "audio": True,
        "narration": script["narration_disclosure"],
        "voice": script["voice"],
        "records": records,
        "duration_seconds": round(duration, 3),
        "ui_base_commit": "36fc05cc92ba8df52ce77b94dea035074c276d4b",
        "configuration": {
            "demo_max_model_turns": 8,
            "timeout_seconds": 120,
            "benchmark_provider": "Separate Qwen/Ollama CPU comparison; eight turns / 300s",
        },
        "memory_origin": "Actual prior model-selected, probe-verified recovery from the same Cloud workspace, retrieved AND explicitly cited in a fresh Gemini conversation. Citation alone does not establish causal dependence.",
        "full_decode_verified": True,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "recorder_path": "frontend/scripts/record-submission.mjs",
        "recorder_sha256": hashlib.sha256(
            (ROOT / "frontend/scripts/record-submission.mjs").read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
        "silent_source_trim_start_seconds": trim,
        "chapters": [
            {"id": i["id"], "start_seconds": round(i["start"] - trim, 3), "title": chapters[i["id"]]["title"]}
            for i in timing
        ],
        "subtitle_path": "demo/ripple-demo.srt",
        "prior_video": "demo/development/cpu-video-v1/video.json",
        "recording_scope": "Actual current application interactions; editorial captions/title cards added by recorder. Model output is replayed, never presented as a new live execution. Narration and caption track are editorial, not model output. No new model calls for filming.",
    }
    (ROOT / "demo/video.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Full-decode-verified {duration:.3f}s narrated 1920x1080 MP4; {target.stat().st_size:,} bytes.")


if __name__ == "__main__":
    main()
