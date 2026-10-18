# Evidence-first agent revision

This revision is being measured against the previous recorded development runs.
Existing reports remain attributable to their original source commits; no new
success rate is implied until actual reruns finish.

The failed memory demonstrations included rejected citations followed by turn
exhaustion. Proposal and diagnosis schemas now enumerate the exact evidence IDs
retrieved in the current run. The independent service citation guard remains in
place, including when a provider ignores its schema.

Application preflight executes a request probe for every mapped simulator service
in both graph and full-document modes. Graph mode additionally retrieves native
incoming dependency paths for unhealthy services, and persistent incident memory.
These automatic calls are recorded with `origin=application_preflight`; they are
not attributed to the model. No hidden fault labels or evaluator expectations are
provided. The model still selects an action or requests missing evidence, and
only an explicit approval executes a simulator transition.

Both modes retain the same documents, model, probes and model-turn budget. The
extra graph paths and memory are explicit workflow capabilities, so a comparison
does not isolate database causality or establish general graph superiority.

The new sequential-demonstration gate is stricter: each sequence must recover,
recover in a fresh conversation while retrieving AND citing the actual prior
model-generated outcome, request evidence without executing an action in the
insufficient-evidence case, and reject an actual stale approval. Old reports that
only required memory retrieval remain unchanged and use the older acceptance
criteria. Budgets are unchanged: five turns / 300 seconds for the explicit CPU
demo, eight turns / 300 seconds for the CPU benchmark; production defaults remain
eight turns / 120 seconds.
