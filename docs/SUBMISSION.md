# Submission packet

**Project:** Ripple — evidence-driven incident recovery

**Public repository:** https://github.com/gayathribuilds/ripple-graph-hacks

**Primary track:** Agents That Act on Connected Data

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
- Actual model results/replays: attach exported artifacts only after their workflows finish.
- Working video: attach the actual recording, clearly identifying provider, replay status,
  synthetic data and what was executed.
- Full application deployment: configure Render and FalkorDB, or use complete local setup.
  A static replay showcase is not described as a hosted live backend.

## Participant-owned checks

The participant must sign in and register with WeMakeDevs, verify age/consent and
team eligibility, choose the final track(s), review and understand the submission,
and complete the organizer's final submission form. These are not inferred from
the existence of source files or a local checklist.

Deadline: October 18, 2026, 11:59 PM IST. Aim to submit earlier with time to check
that repository/video links and setup instructions are accessible to judges.
