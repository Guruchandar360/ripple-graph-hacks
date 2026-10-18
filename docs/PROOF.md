# Proof for judges

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

The auditor reads 24 benchmark records and nine sequence recordings. It
cross-checks **442 recorded path instances** (including repeated retrievals across
calls and runs) against their exported graph
nodes/edges, recomputes reported impact accuracy from actual preflight probe
receipts, checks conclusion citations against retrieved evidence, checks recovery
probes, and traces each cited memory back to its earlier execution result.

[The index](../demo/proof-index.json) fingerprints 45 artifacts, including the
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

## Remaining verification

- **Integrated Gemini + Cloud/Render execution:** the direct Google SDK native
  function-call probe passed ([receipt](../demo/provider-checks/gemini-3.8.json)).
  The selected Free database exposes plaintext Redis. The deployment's TLS
  exception still awaits explicit approval; a hosted incident recovery has not
  been verified.
- **Normal application time limit:** CPU proof uses 300 seconds per conversation.
  Reliability within the default 120-second application window is unmeasured.
- **Participant requirements:** registration, eligibility, meaningful contribution,
  technical understanding and final submission require the participant. See the
  [technical review guide](CONTRIBUTOR_GUIDE.md). AI assistance is disclosed in the README.
