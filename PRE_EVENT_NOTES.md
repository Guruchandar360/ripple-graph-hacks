# Ripple: pre-event engineering notes

Prepared October 13, 2026 (IST). These are planning notes, not an implementation.
Main coding and finished visual design are scheduled for October 15, 2026,
12:01 AM IST under https://www.wemakedevs.org/hackathons/falkordb/rules.

## Locked decisions

- Solo, React/TypeScript/Vite frontend and Python 3.12/FastAPI backend.
- Direct FalkorDB tools using the official Python client.
- Gemini 2.5 Flash via the official Google GenAI SDK; free services only.
- Executable Python simulator, six services, three scenarios, one investigator.
- One Render service serves API and built frontend; FalkorDB persists state.
- No arbitrary shell commands, production integrations, or invented live results.
- Investigation, Memory, and Results views; evidence-driven graph highlighting.

## Preflight facts and kickoff checks

- Workspace has no existing application or repository instructions.
- Python 3.12.3, Node 22.14.0, npm, and Git were detected in the previous check.
- Docker was not detected on PATH.
- No Gemini or FalkorDB connection variables were detected in the process environment.
- At kickoff verify Gemini model access, quota, function calls, and FalkorDB TLS access.
- Free cloud availability is not account-verified. Do not enable paid fallback.
- Local Docker FalkorDB plus a working demo video is the hosting contingency.

## Graph model sketch

Service DEPENDS_ON Service; Service OWNED_BY Team.
Deployment CHANGES Service; Incident AFFECTS Service.
Constraint BLOCKS Action; evidentiary entities SUPPORTED_BY Source.
Run PROPOSED Action; Run EXECUTED Action; Action VERIFIED_BY ProbeResult.
Run LEARNED_FROM Incident.

Evidence has stable IDs, source references, effective and ingestion timestamps,
and supersession metadata. Current decisions exclude superseded evidence.
Historical evidence remains inspectable. Workspace revision changes whenever
decision-relevant evidence changes. Simulator state is persisted separately
from agent-visible evidence; evaluator fault labels are never exposed as tools.

Each visitor receives a server-generated isolated graph and HttpOnly workspace
cookie. New investigation context is empty except for graph-retrieved memory.

## Scenario notes

A: payments deployment enables strict currency validation; checkout fails.
An older incident suggests rollback. A newly ingested migration record blocks
rollback because the previous deployment does not support the current schema.
Disabling the flag can restore health. The recommendation must be revalidated
after evidence ingestion, and execution must reject a stale proposal.

B: a related new incident can retrieve A's verified outcome. It must still
check current compatibility and probes instead of treating memory as authority.

C: missing diagnostic information prevents a justified remediation. Report
known impact and ownership, identify missing evidence, and execute no action.

## Twelve evaluation cases to implement after kickoff

1. A with migration already known: reject incompatible rollback.
2. A with migration arriving after proposal: invalidate old approval.
3. A with shuffled ingestion order: respect effective-time/supersession rules.
4. A with an extra downstream dependency: include the added affected service.
5. A with an unrelated unhealthy service: do not include it without evidence.
6. A with a failed restart attempt: store failure; never claim recovery.
7. B with verified A memory: retrieve it and verify applicability.
8. B in a fresh conversation: succeed without old chat context.
9. B with incompatible current constraints: decline the remembered procedure.
10. C with insufficient evidence: no justified action proposal.
11. C with a misleading runbook excerpt: do not turn suggestion into proof.
12. C with superseded ownership: use current owner and retain old provenance.

Use identical source records, model, turn budget, and simulator tools for a
full-document-context baseline. Keep evaluator answers separate. Record both
invalid proposals and executed constraint violations: a shared action guard
may prevent execution even when a model proposes the wrong action. Report
measured case outcomes, calls, latency, citations, impact, and recovery results.
Do not publish invented scores or claim general superiority from these cases.

## API and execution notes

Scenario listing/loading, run creation/status, allowlisted evidence injection,
action approval/execution, graph, memory, and recorded evaluations follow the
accepted plan. Poll active runs every second using incremental event cursors.

Use parameterized Cypher, bounded tools, citation validation, eight model
turns, and a two-minute run limit. Recheck revision and preconditions at commit
time. Action IDs are idempotent. Evidence changes invalidate pending approvals.
Scenario reloads invalidate outstanding runs/proposals from the earlier load.
Serialize mutations per workspace and model calls globally. Database outages
stop investigations/actions rather than substituting an in-memory graph.

Persist events before displaying them. On restart mark unfinished runs
interrupted; never silently repeat an action. Maintain action outcome and
simulator state consistently so retries cannot duplicate effects.

Free public live quotas: three runs/workspace/day and ten globally/day, stored
in a control graph. Replays are visibly labeled and do not call the model.

## Build gates

- October 15: graph, simulator, bounded agent, one end-to-end API workflow.
- October 16: revisions, constraints, memory, all scenarios and meaningful tests.
- October 17: UI, deployment, evaluator, three repeatable demonstrations.
- October 18: noon feature freeze; documentation/video; submit by 8 PM IST.

Acceptance includes isolation, stale proposal rejection, idempotent actions,
fresh-session memory, honest failures, probes backing recovery, and successful
README setup. Submission includes public source, model diagram, actual queries,
AI-use disclosure, measured results, setup instructions, and working demo video.
