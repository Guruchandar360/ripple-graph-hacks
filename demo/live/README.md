# Actual native Gemini / FalkorDB Cloud evidence

This supplements the CPU comparison; the providers and samples are not pooled.
All data is fictional and all recovery actions execute only in Ripple's simulator.

| Sample | Source | Actual result |
|---|---|---|
| `http-proof.json` and its named persisted run | `c02004d` on free Render | One model call, 7.014s persisted investigation, 503 → 200 for checkout/payments/storefront, identical duplicate result, memory after scenario reload, foreign visitor 404. No Cloud restart test. |
| `sequence/repeatability.json` and three `sequence/replays/` records | `e06d39f`, local Python + actual Cloud + Google native calling | 1/1 requested complete sequence passed: stale approval rejected, recovery, a fresh conversation citing the actual prior outcome, no insufficient-evidence execution. |

The sequence's three-consecutive `passed` gate is **false**, deliberately;
`sample_passed` is true for the smaller completed sample. CPU `demo/repeatability.json`
remains the separate three-consecutive result. Native sequence timings are 63.672s
for the initial plus revised recovery conversations together, 63.297s for fresh
memory and 90.344s for missing evidence. Each conversation had eight turns / 120s.
Timing excludes human approval and action execution.

The hosted HTTP driver's first terminal poll preceded final timing persistence
and contained 0ms. The published receipt explicitly retains that original value
in `initial_poll_elapsed_ms` and uses the final Cloud-persisted run's 7014ms.
The driver now refreshes final timing and saves the raw run for future checks.
The audit verifies equality with the retained persisted record; it does not
repeat model or HTTP requests.

Google AI Studio showed a reached free rate limit on October 18, with 21/20
peak daily requests. Further live calls may be blocked until reset. No billing
upgrade or alternate key was used. The initial slower, incomplete native trial
remains in `demo/development/gemini-pre-tuning/` and is not counted as a pass.

The participant approved the selected Free instance's plaintext Redis
connection only for synthetic demo data. Database credentials and synthetic
records travel without TLS. Browser and Gemini traffic use HTTPS. Provider
credentials remain in ignored local configuration and Render's server settings.

Run `python -m ripple.proof` to validate hashes, graph paths, execution probes,
native result/timing consistency and the sample-size boundary offline.
