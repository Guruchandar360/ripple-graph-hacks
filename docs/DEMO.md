# Silent submission demonstration

The current film records the latest Ripple interface at 1920x1080. It has no
audio track. Full explanatory text is burned into every scene, with embedded
English subtitles and chapter navigation. Each scene remains visible long enough
to read its complete explanation. No subtitle toggle or sound is needed.

All model output is labeled REPLAY and all operational data is synthetic.
Filming makes no new model calls. The story covers connected dependencies,
the initial rollback, changed migration evidence, stale approval rejection,
verified recovery probes, fresh-session memory, and insufficient evidence with no
execution. It then shows the separate hosted HTTP receipt and CPU comparison,
including their limitations. One native sequence is not three consecutive passes.

## Reproduce the silent film

1. Export actual recordings with python -m ripple.export_showcase and generate
   the proof page with python -m ripple.proof_page.
2. Build the frontend with VITE_STATIC_SHOWCASE=true. Serve the compiled frontend
   with Vite preview, using the same base path chosen for the build.
3. From frontend, set DEMO_URL to that local application URL and run
   node scripts/record-submission.mjs. Exact native IDs and outcomes are validated;
   chapter display_seconds in demo/film-script.json controls reading time.
4. From the root, run python scripts/compose-demo.py with optional
   imageio-ffmpeg==0.6.0 installed. It packages a silent H.264 MP4 with captions,
   subtitles, chapters and fast start. It checks that no audio stream exists,
   fully decodes the file, and refuses an edit over 180 seconds.
5. Inspect captioned frames, update artifact fingerprints and run
   python -m ripple.proof. From frontend, set FILM_URL to the delivered MP4 and
   run node scripts/verify-film.mjs to check real playback, zero decoded audio,
   resolution, duration and seeking.

Caption text and reading times: demo/film-script.json. Accessible subtitles:
demo/ripple-demo.srt. Exact duration, sources, scope and fingerprints:
demo/video.json. The WebM is the silent source capture with documented pre-roll.

The earlier narrated film is recoverable from Git commit f44e5cf. The older
79.48-second CPU-only video remains under demo/development/cpu-video-v1/.
Historical footage is not new execution proof. AI assistance is disclosed.
