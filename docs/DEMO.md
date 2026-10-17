# Demonstration

The captioned recording uses the first complete passing development sequence:
recovery, fresh-conversation memory and insufficient evidence in one workspace.
It is a replay and does not represent the benchmark's success rate or a guarantee
of repeatability. `demo/video.json` identifies each run, source commit and workflow.
Memory is the actual earlier model-selected, probe-verified outcome. Retrieval
and explicit citation are separate measures; the later model did not cite it. All failed
measurements remain available separately. The outline below is also suitable for
a three-minute live presentation once provider access is configured.

1. **0:00–0:20 — The problem.** Checkout is failing. Explain that everything on
   screen is a synthetic environment and that the investigation is an actual model
   run using FalkorDB. Never label fixture preview as a live agent.
2. **0:20–0:55 — Follow the graph.** Start the investigation. Select the dependency
   finding; show the returned paths, ownership, and cited release/runbook sources.
3. **0:55–1:30 — Change the evidence.** Inject the migration after the run pauses.
   Show the amber event and stale approval. Explain how schema 2 invalidates the
   historical rollback. The model can choose the correct flag action initially;
   do not edit or script its answer to manufacture a bad recommendation.
4. **1:30–2:05 — Verify a recovery.** Investigate the new revision, approve a justified
   action, and show before/after affected-service probes and the verified outcome.
5. **2:05–2:35 — Remember, with checks.** Load the memory scenario. A new conversation
   retrieves persisted outcome and current constraints. Show it is not old chat.
6. **2:35–3:00 — Evidence and limits.** Show the actual evaluation artifact if run,
   then the missing-evidence scenario. Explain rejection/verification boundaries.

Record a working run only after configuring real services. Keep an unedited local
recording as a fallback for free-host cold starts. No recording is included merely
because this script exists. Finish with public repo/setup links and AI disclosure.

## Reproduce the captioned recording

Run the built local application with exported actual replays available. From
`frontend`, run `node scripts/record-demo.mjs`; it refuses missing or unsuccessful
required scenarios and refuses a memory claim without recorded retrieval IDs.
Set `DEMO_REPETITION` to a recorded sequential demonstration number to select the
same repetition's recovery, memory and insufficient-evidence phases. Without it,
the script selects graph-mode benchmark replays.

The recorder adds explanatory captions over actual application state. It does
not manufacture events, actions or probe outcomes. The original WebM is retained;
`scripts/transcode_demo.py` packages an H.264 MP4 with fast start after installing
the optional `imageio-ffmpeg==0.6.0` dependency. Inspect decoded frames as well as
duration and dimensions before publishing. The public URL and repository both
identify recordings as replays of a synthetic simulator.
