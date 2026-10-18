# Submission packet

**Project:** Ripple — evidence-driven incident recovery

**Public repository:** https://github.com/Guruchandar360/ripple-graph-hacks

**Recorded showcase:** https://guruchandar360.github.io/ripple-graph-hacks/

**Captioned working demo:** https://guruchandar360.github.io/ripple-graph-hacks/showcase/ripple-demo.mp4

The video is an explicitly labeled selection of actual development model output;
`demo/video.json` identifies the passing sequence and its measured memory origin. The
public site is read-only; use the README to run the full backend locally.

**Primary track:** Agents That Act on Connected Data

**Evidence guide for judges:** [Public proof page](https://guruchandar360.github.io/ripple-graph-hacks/proof/)
and [repository guide](PROOF.md).
The offline artifact audit and optional online workflow verification are separate
from fresh model execution and live deployment readiness.

Optional additional tracks should be declared only if the final demonstrated
features support the claim: Agent Memory and Coordination; Company Brain.

## Project description

Ripple is an incident investigation console for a fictional commerce company.
FalkorDB stores the service dependencies, ownership, source provenance, current
action constraints, investigation history and incident memory. A bounded agent
uses graph tools to investigate a checkout failure and propose a recovery action.

The signature scenario introduces a newer ledger migration advisory. It changes
which recovery action the graph permits, invalidates old approvals and preserves
the evidence trail. Human-approved simulator actions are followed by actual
request probes; a successful-looking action is not automatically called recovery.

The application deliberately exposes uncertainty and can request missing evidence.
All operational data is synthetic. No production systems are connected.

## Materials

- Setup instructions: repository README.
- Graph model and essential Cypher: `docs/GRAPH.md`.
- Evaluation methodology: `docs/EVALUATION.md`.
- Participant technical guide: `docs/CONTRIBUTOR_GUIDE.md`.
- AI assistance disclosure: README.
- Actual model results/replays: `demo/evaluations.json` and `demo/replays/`.
  The complete 24-run comparison and every failure are published. See
  `docs/MEASUREMENTS.md` and `demo/release.json` for measurements and source versions.
  Additional targeted replays are separate samples and do not enter the score.
  Earlier development failures remain inspectable under `demo/development/`.
- Working video: `demo/ripple-demo.mp4`, identifying the provider, replay status,
  synthetic data and actual measured behavior. It shows one of three consecutive
  passing evidence-first-v2 sequences; source records and limits are disclosed.
  The complete comparison still contains two incomplete graph impact reports.
- Technical blog: `docs/BLOG.md` (public repository article; no external post claimed).
- Full application deployment: configure Render and FalkorDB, or use complete local setup.
  A static replay showcase is not described as a hosted live backend.

## Participant-owned checks

The participant must sign in and register with WeMakeDevs, verify the organizer's
eligibility/consent requirements and team membership, choose the final track(s), review and understand the submission,
and complete the organizer's final submission form. These are not inferred from
the existence of source files or a local checklist.

Deadline: October 18, 2026, 11:59 PM IST. Aim to submit earlier with time to check
that repository/video links and setup instructions are accessible to judges.
