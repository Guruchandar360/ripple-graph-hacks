# Proof for judges

[Read the standalone proof page](https://guruchandar360.github.io/ripple-graph-hacks/proof/).
The public page and its raw records are hosted alongside Ripple so the evidence
can be inspected without relying on GitHub's document viewer.

Ripple's claim is specific: connected evidence changes which recovery action is
allowed, measured outcomes persist into a fresh conversation, and recovery must
be supported by executable simulator probes. All incidents are synthetic.

Start with the [79-second captioned demo](https://guruchandar360.github.io/ripple-graph-hacks/showcase/ripple-demo.mp4?v=43e8d93),
then inspect the records below. The public website is a labeled, read-only replay.

| Claim | Recorded evidence | Scope and source |
|---|---|---|
| Three complete sequences passed | [3/3 report](../demo/repeatability.json), [actual workflow](https://github.com/Guruchandar360/ripple-graph-hacks/actions/runs/39129743227) | Qwen3 4B through Ollama, five turns / 300 seconds per conversation, source `66eeedc`. Every fresh conversation retrieves **and cites** its actual prior recovery. The stricter `evidence-first-v2` gate also requires stale rejection and no insufficient-evidence execution. |
| Graph mode reached every expected terminal state | [All 24 rows](../demo/evaluations.json), [comparison and limitations](MEASUREMENTS.md), [actual workflow](https://github.com/Guruchandar360/ripple-graph-hacks/actions/runs/39130562373) | Graph 12/12; full-document baseline 11/12. Same model, documents, probes and eight-turn / 300-second budget. Graph impact was complete in 10/12 cases, baseline 11/12. Graph median elapsed was 206.0s versus 94.0s. Known synthetic development cases do not establish general superiority. |
| Recovery matches before/after probes | [Actual recovery record](../demo/replays/48089bad9b284c8b963bd6a6ec837d10.json) | Checkout, payments and storefront change from failing 503 to healthy 200. The audit rejects missing services, unhealthy results and contradictory status codes. |
| Memory is the actual earlier outcome | [Fresh conversation](../demo/replays/d586d4e52a514b67b554d1a53c548133.json) | Its cited `memory-1ac3b169cda848dbb7243abe16cdc20e` refers to the previous action's identical measured result. Its archived FalkorDB graph contains the `LEARNED_FROM` relationship. Citation establishes observed reference, not causal dependence. |
| Missing evidence prevents a recovery claim | [Actual diagnosis](../demo/replays/4412620932e54c48aeadbaf399e705c6.json) | Status `needs_evidence`, missing diagnostics listed, no executed proposal. Passing this gate does not establish perfect impact reporting. |
| Real graph queries and application checks ran | [Historical clean CI](https://github.com/Guruchandar360/ripple-graph-hacks/actions/runs/39133494191), [original JUnit receipt](../demo/verification/backend-tests.xml), [browser receipts](../demo/verification/ci-results.txt), [essential queries](GRAPH.md) | Source `43e8d93`: 46 backend tests including two actual FalkorDB container tests, eight application browser tests, and one separately recorded static-site test. Repository doubles and scripted providers are explicitly separate from native database and real-model measurements. |
| HTTP boundaries were exercised | [Historical HTTP report](../demo/http-proof.json), [actual workflow](https://github.com/Guruchandar360/ripple-graph-hacks/actions/runs/39033501898) | Source `2c8aaaa`, five turns / 300 seconds: recovery, identical duplicate result, memory after scenario reload and database restart, and foreign-visitor HTTP 404. These are earlier driver assertions, not a new test of current Gemini deployment. |

## Follow one evidence chain

1. The recovery recording preserves the initial rollback proposal at revision 1,
   the newer migration record, and the old proposal's stale status.
2. Its new model conversation proposes the permitted feature-flag change at
   revision 2. Execution stores actual failing and passing request probes.
3. The next incident uses a different run ID and scenario generation. Its
   `memory_ids`, proposal citation, stored outcome and `LEARNED_FROM` edge point
   to that earlier action. The agent starts with fresh conversation contents;
   [agent-loop tests](../tests/test_agent.py) verify the context boundary.
4. The missing-evidence recording requests diagnostics and contains no executed
   proposal. Every sequence preserves these three phase records.

The sequence driver attempted each stale action and recorded rejection in all
three attempts. The archive preserves the revision change and stale proposal;
the offline audit does not repeat those requests. Native database tests and the
linked driver/source provide the complementary execution evidence.

## Check the proof yourself

After installing the README dependencies, run:

```powershell
python -m ripple.proof
python -m pytest tests/test_proof.py -q
```

The auditor reads 24 CPU benchmark records, nine CPU sequence recordings and
four separate native recordings. It cross-checks **476 recorded path instances** (including repeated retrievals across
calls and runs) against their exported graph
nodes/edges, recomputes reported impact accuracy from actual preflight probe
receipts, checks conclusion citations against retrieved evidence, checks recovery
probes, and traces each cited memory back to its earlier execution result.

[The index](../demo/proof-index.json) fingerprints the retained artifacts, including the
video, raw reports, selected replays and historical CI receipts. Binary media
checksums are byte-exact; text hashes normalize CRLF to LF for portable Git
checkouts. [The saved audit](../demo/proof-audit.json) records the result.
These checks establish consistency relative to the committed index. They are
not independent certification or protection against deliberate edits to both an
artifact and its index.

With GitHub CLI available, also run:

```powershell
python -m ripple.proof --online
```

This additionally checks that all five cited public GitHub workflows completed
successfully at their stated source commits. It makes no model calls or database
writes. CI runs the offline audit on each subsequent change. Fresh model reruns
are separate commands documented in [the evaluation guide](EVALUATION.md).

Earlier failures remain available in [the provenance index](../demo/PROVENANCE.md)
and `demo/development/`; they are not added to the new sample's success count.

## Native Cloud verification

The [hosted HTTP receipt](../demo/live/http-proof.json) and
[persisted native run](../demo/live/0bdffbe3ef444ee4bdc66e54bc9638fb.json)
record an actual Render → Gemini / FalkorDB Cloud recovery at `c02004d`:
one model call, 7.014 seconds of persisted investigation time, all three affected
services changing from 503 to 200, identical duplicate result, scenario-reload
memory and foreign-visitor HTTP 404. Action approval/execution time is excluded.
Cloud database restart was not tested.

The separate [native sequence](../demo/live/sequence/repeatability.json) at
`e06d39f` passed one complete three-scenario sample: actual stale approval
rejection, recovery, fresh memory retrieval **and citation**, and no unsupported
action. Its combined initial/revised recovery took 63.672 seconds, memory
63.297 seconds and insufficient-evidence diagnosis 90.344 seconds. Each
conversation had eight turns / 120 seconds configured. This is one requested
sequence, not three consecutive passes; the JSON keeps the release-gate
`passed` field false while `sample_passed` is true. All records are fingerprinted
and checked separately from the CPU comparison. See [native evidence](../demo/live/README.md).

The [initial slow native trial](../demo/development/gemini-pre-tuning/trial.json)
is retained: first proposal 128.375 seconds; second investigation timed out.
Subsequent native configuration changes are a separate sample.

## Remaining verification and limits

- **Native repetition:** three consecutive Gemini sequences remain unverified.
  The existing three-pass result uses the documented CPU configuration.
- **Free model quota:** on October 18 Google AI Studio displayed a reached rate
  limit, with peak 21/20 daily requests. Further live calls may be blocked until
  reset. No billing upgrade or alternate key was used.
- **Database transport:** the participant explicitly approved plaintext Redis
  for this synthetic demo only. Its password and synthetic records travel
  without TLS between app and FalkorDB; browser and Gemini traffic use HTTPS.
  The deployment template retains TLS by default.
- **Participant requirements:** registration, eligibility, meaningful contribution,
  technical understanding and final submission require the participant. See the
  [technical review guide](CONTRIBUTOR_GUIDE.md). AI assistance is disclosed.
