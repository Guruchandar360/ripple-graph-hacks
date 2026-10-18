# Yesterday’s fix can break today’s system

*Building Ripple: evidence-driven incident recovery with FalkorDB.*

A checkout outage follows a payments release. An earlier recovery record suggests a familiar response: roll back. Then a migration advisory arrives. The older deployment cannot read the database schema now running in production.

The remembered fix has become the dangerous option.

That is the problem Ripple explores: how should an incident agent change its recommendation when the evidence changes? We built an executable, synthetic environment to make the answer observable. Ripple is a hackathon prototype; no production systems are connected.

## Make the changing decision visible

Our fictional company has six services and three owning teams. The investigation starts with failing requests, dependency relationships, deployment records, and an initially applicable rollback advisory.

When newer migration evidence is ingested, the workspace revision changes. Ripple invalidates the old approval, retrieves the new constraint, and investigates a replacement. Disabling the incompatible feature flag preserves the compatible deployment. The simulator checks the affected services: checkout, payments, and storefront must all move from failing probes to healthy responses before recovery is verified.

The interface makes that transition the centerpiece: an amber **Evidence changed** event connects the previous recommendation to the constraint that invalidated it. Users can inspect the source and supporting paths themselves.

## Why FalkorDB is central

FalkorDB connects services, dependencies, ownership, deployments, source records, action constraints, incidents, and measured outcomes. Parameterized Cypher tools retrieve incoming dependency paths, current policies, and related incident memory.

For example, this traversal returns services potentially affected by a failing dependency, together with their supporting node and relationship IDs:

```cypher
MATCH p=(s:Service)-[:DEPENDS_ON*0..5]->(t:Service {id:$target})
RETURN s.id, [n IN nodes(p) | n.id], [r IN relationships(p) | r.id]
```

Those returned paths drive the visualization. Connectivity identifies possible impact; it does not prove causation. Source records and executable probes provide additional evidence.

Facts retain stable identifiers, effective times, and ingestion times. Superseded evidence stays inspectable but cannot authorize current actions. FalkorDB also persists investigation state and outcomes across conversations. If the graph is unavailable, investigation and execution stop.

## Let the agent investigate; make execution deterministic

One bounded agent can inspect sources, retrieve paths and memory, run probes, and submit a structured conclusion. It cannot execute arbitrary shell commands or generate unrestricted database writes.

Application code validates citations and rechecks the current revision and constraints before execution. Supported actions are rollback, feature-flag disablement, and restart. Repeating an action identifier returns its recorded result rather than executing twice. Failed attempts are stored as failures.

A second scenario starts a fresh conversation, retrieves an actual earlier verified outcome, and checks current applicability. A third deliberately lacks enough evidence: the correct result is a request for diagnostics, with no action executed.

## What the measurements actually showed

Early experiments failed, including exhausted model budgets and incomplete investigations. We retained those records. They led to clearer tool contracts, evidence-first context collection, and stricter verification.

Our later 12-case synthetic comparison used the same Qwen/Ollama model, documents, probes, and eight-turn/300-second conversation budget in both workflows. Graph mode additionally received dependency traversal and incident-memory retrieval.

| Measurement | Graph workflow | Full-document baseline |
|---|---:|---:|
| Expected terminal outcomes | 12/12 | 11/12 |
| Verified recoveries | 8 | 7 |
| Complete affected-service reports | 10/12 | 11/12 |
| Median investigation time | 206.0 seconds | 94.0 seconds |

Graph mode reached more expected outcomes in this sample, but was slower and missed part of the impact set twice. These known development fixtures do not establish general superiority or isolate the database’s causal contribution.

Separately, actual Gemini/FalkorDB Cloud verification completed one full three-scenario sequence, including stale-approval rejection and fresh-conversation memory. Three consecutive native sequences remain unverified. A separate hosted Render recovery receipt records all three affected services changing from 503 to 200. These native results are distinct from the CPU comparison.

## What we learned

Memory needs applicability checks: a previous success is evidence to examine, not permission to repeat an action. Recovery needs measurements: a convincing explanation is insufficient. Reliability needs honest accounting: browser tests, database integration tests, and real-model runs establish different things.

Free-service limits shaped delivery too. The public showcase clearly labels recorded runs; the live backend can cold-start and new investigations depend on available model quota. The approved plaintext Redis connection is limited to synthetic data and would need a secure replacement before production use.

Ripple’s strongest demonstration is a decision that changes for an inspectable reason—and a recovery claim backed by probes.

## Watch and inspect

- [Silent, captioned YouTube demo](https://youtu.be/ZO9PGXFtRJk)
- [Interactive recorded showcase](https://guruchandar360.github.io/ripple-graph-hacks/)
- [Evidence, raw records, and limitations](https://guruchandar360.github.io/ripple-graph-hacks/proof/)
- [Public source and local setup](https://github.com/Guruchandar360/ripple-graph-hacks)
- [Graph model and essential queries](GRAPH.md)

**AI assistance disclosure:** Codex generated and revised code, tests, styling, documentation, and demo materials. Participant contribution, review, and technical understanding must be described and established by the participant; automated checks do not establish them.
