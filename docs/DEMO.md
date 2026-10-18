# Submission demonstration

The current film records the latest Ripple interface at 1920x1080, with captions,
embedded English subtitles, chapters and locally synthesized narration. All model
output is labeled REPLAY and all operational data is synthetic. Filming makes no
new model calls.

It follows the actual native Gemini/FalkorDB Cloud sequence from source e06d39f:
initial rollback, migration evidence, stale approval rejection, verified flag
recovery, fresh-conversation retrieval AND citation of that actual recovery,
then insufficient evidence with no execution. That is one complete native
sequence, not three consecutive native passes.

The film then shows the separate actual Render HTTP receipt: one Gemini call,
7.014-second persisted investigation, 503-to-200 probes, duplicate execution
idempotency, scenario-reload memory and visitor isolation. It does not claim a
Cloud database restart test. The separate CPU benchmark is explicitly identified:
graph expected outcomes 12/12 versus baseline 11/12; graph impact 10/12 versus
baseline 11/12; graph was slower. Known synthetic cases establish no general
superiority. Three consecutive CPU sequences are separate from the native sample.

The film states the exhausted free quota and unmet native three-consecutive gate.
The approved plaintext database exception is limited to synthetic demo data.
AI assistance and synthesized narration are disclosed. No voice is imitated.

## Reproduce the film

1. Export committed actual recordings: python -m ripple.export_showcase.
2. Generate the audited proof page: python -m ripple.proof_page.
3. Build frontend with VITE_STATIC_SHOWCASE=true and VITE_BASE_PATH=/.
4. Serve frontend/dist on 127.0.0.1:8104.
5. On Windows, run powershell -NoProfile -File scripts/narrate-demo.ps1 from the
   root. This uses the installed Microsoft Zira Desktop voice locally.
6. From frontend, run node scripts/record-submission.mjs. It selects exact actual
   native IDs, validates outcomes, selects a real supporting path, and records
   application interactions. Captions are editorial overlays; underlying findings,
   graphs, actions and probes are never changed.
7. From the root, run python scripts/compose-demo.py with optional
   imageio-ffmpeg==0.6.0 installed. It adds narration, subtitles and chapters,
   normalizes audio to -16 LUFS, packages H.264/AAC with fast start, and fully
   decodes the result with -xerror. It refuses an edit over 180 seconds.
8. Inspect decoded frames and check audio, dimensions and duration before
   publishing. Update artifact fingerprints and run python -m ripple.proof.

Narration text: demo/film-script.json. Accessible subtitles: demo/ripple-demo.srt.
Exact duration, source IDs, UI source, recording scope, hash and recorder
fingerprint: demo/video.json. The WebM is the silent source with pre-roll; its trim
offset is documented.

The earlier 79.48-second CPU-only film, metadata and silent WebM remain under
demo/development/cpu-video-v1/. Its recorder remains unchanged at
frontend/scripts/record-demo.mjs. Historical footage is not new execution proof.
