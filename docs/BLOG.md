# Yesterday’s fix can break today’s system

An incident runbook is useful until the system changes underneath it. A rollback
that recovered checkout last month can be incompatible with the database schema
running today. An incident assistant needs more than the ability to retrieve the
old runbook: it needs current relationships, provenance and a way to test whether
its proposed action actually helped.

Ripple explores this problem in an executable synthetic environment. It is a
hackathon prototype, not a production incident-response system.

## A small company, a changing decision

The fictional company has six services. Storefront calls checkout; checkout
depends on payments and inventory; payments uses ledger; inventory depends on
notifications. Three teams own these services. Source records describe a release,
a historical recovery and the latest received compatibility advisory.

The first advisory permits a payments rollback. A later ledger migration record
establishes that the old payments version cannot read the current schema. That
new evidence changes what is allowed: block rollback and permit a scoped feature
flag mitigation while keeping the compatible deployment.

The simulator's runtime and the evidence collection are separate. A late source
can be stale even when it is the newest received document. The physical runtime
also checks its own preconditions before changing state. Neither an agent's
confidence nor an outdated advisory can authorize an incompatible transition.

## Why a graph is part of the behavior

FalkorDB is the context and persistence layer. Incoming dependency traversal
finds the services affected by a failing dependency. Ownership edges identify
the responsible team. Source-backed `BLOCKS` and `PERMITS` relationships determine
whether an action can proceed. Incident nodes preserve measured outcomes across
fresh model conversations.

For example, the impact query returns the actual supporting path identifiers:

```cypher
MATCH p=(s:Service)-[:DEPENDS_ON*0..5]->(t:Service {id:$target})
RETURN s.id, [n IN nodes(p) | n.id], [r IN relationships(p) | r.id]
```

Connectivity establishes potential impact, not causation. The agent also needs
source evidence and request probes. The UI highlights returned paths rather
than drawing an invented explanation after the fact.

Every fact has a stable ID, effective time and ingestion time. Related versions
are resolved by effective time. Superseded records remain inspectable; their
policies cannot authorize current actions. Graph revision changes invalidate
outstanding approvals. The application rechecks the revision and constraints
immediately before execution.

## The model investigates; code validates and measures

One bounded agent can read evidence, traverse impact paths, retrieve incident
memory, inspect a source, run probes and submit a structured proposal or diagnosis.
It cannot execute arbitrary commands or write arbitrary Cypher. Citations must
refer to active evidence retrieved in that run, and action targets need a probe.

The supported simulator actions are rollback, disable a feature flag and restart
a service. Execution is a pure state transition followed by one optimistic graph
commit containing the runtime, action audit and probes. Repeating an action ID
returns the recorded outcome instead of executing it twice.

Recovery requires a previously failing check and all required post-action checks
passing. Failed attempts stay in memory as failures. A subsequent conversation
can retrieve those outcomes, but must still inspect current applicability.

The console shows completed operational events labeled observation, hypothesis
or verified outcome. It does not animate fabricated private model reasoning.
Its amber “Evidence changed” event connects the prior investigation to the new
constraint and subsequent investigation.

## What testing can and cannot establish

The project separates behavioral tests using an explicit test-only repository
double, real FalkorDB integration tests, browser tests and actual model runs.
Passing the first three does not establish that a model will consistently choose
the right action.

The first real development smoke test demonstrated this distinction. With
Qwen3 1.7B, both workflows exhausted their eight-turn budgets. The graph workflow
proposed an incompatible rollback; the independent policy guard blocked it.
Zero recoveries out of two measured runs is a limitation to report, not hide.
The raw result is committed in `demo/development/initial-qwen3-1.7b.json`.

That result motivated a stronger explicitly selected local model and generic
instruction improvements: avoid rereading full documents, batch independent
tools, account for the turn budget and respect current constraints. The system
prompt does not identify a scenario's expected recovery action.

The 12-case evaluation compares graph and full-document workflows using the same
model, documents, probes and turn budget. Graph mode additionally has traversal
and incident-memory retrieval. This measures those configured workflows; it
does not isolate the database's causal contribution or prove general superiority.
Actual exported measurements and failures are published with their model and
provider identity. The benchmark uses only synthetic cases.

One complete development sample (`demo/development/memory-cache-suite.json`)
reached 16 of 24 expected terminal states: graph mode reached 6/12 and the
full-document baseline 10/12. No executed policy violations occurred, but this
does not establish graph superiority. The sample also exposed CPU timeouts and
incomplete impact reports. Later adapter work keeps its tool catalog stable
while passing current authorization constraints separately; subsequent measured
results are reported in [MEASUREMENTS.md](MEASUREMENTS.md), without deleting the
earlier failures.

The later evidence-first revision constrains citation choices to retrieved IDs
and collects actual request probes for every service before the first model
call in both workflows. Graph mode also collects incoming paths for failing
services. These are application operations, visibly attributed as such.
Its complete 24-run sample reached 12/12 expected states in graph mode and
11/12 in the document baseline. Graph mode verified eight recoveries and the
baseline seven. The graph workflow was slower (206.0s median versus 94.0s) and
still omitted part of the impact set in two cases. This supports a narrower
claim of improved observed reliability on these fixtures; it does not show
universal superiority. Budgets remained equal at eight turns / 300 seconds
per conversation, above the application's normal 120-second window.

## Reproduce and inspect

[Source and local setup](https://github.com/Guruchandar360/ripple-graph-hacks) ·
[Recorded showcase](https://guruchandar360.github.io/ripple-graph-hacks/) ·
[Verification and measurements](VERIFICATION.md) · [Essential queries](GRAPH.md)

The public showcase contains recorded output and disables execution. Live local
investigation requires FalkorDB plus Gemini access or an explicitly configured
Ollama server. There is no hidden paid fallback or in-memory production graph.
The prototype uses one backend worker and rebuilds a small graph projection on
mutation; these are limits to redesign before production use.

**AI assistance disclosure:** Codex generated and revised implementation code,
tests, styling and documentation. Participant review, meaningful contribution
and technical understanding must be established by the participant, not inferred
from this article or automated checks.
