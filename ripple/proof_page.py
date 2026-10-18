"""Generate the public, read-only proof guide from an audited local bundle."""

import argparse
from html import escape
from pathlib import Path

from ripple.proof import ROOT, audit, read


def render(root=ROOT):
    result = audit(root)
    index = read(root, "demo/proof-index.json")
    benchmark = read(root, "demo/evaluations.json")
    repeated = read(root, "demo/repeatability.json")
    video = read(root, "demo/video.json")
    records = [read(root, p) for p in index["sequence_replays"]]
    phases = {r["demonstration_phase"]: r for r in records if r["repetition"] == 1}
    workflows = {r["kind"]: r for r in index["workflows"]}

    def link(url, label):
        return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'

    def raw(phase):
        return link(f'../showcase/proof-records/{phases[phase]["id"]}.json', "Read actual record ↗")

    rows = ""
    for mode, title in (("graph", "Graph-backed"), ("baseline", "Full documents")):
        values = result["benchmark"][mode]
        rows += (
            f'<tr><th scope="row">{title}</th><td>{values["expected_met"]}/12</td>'
            f'<td>{values["correct_impact"]}/12</td><td>{values["valid_citations"]}/12</td>'
            f'<td>{values["median_seconds"]:.1f}s</td></tr>'
        )
    cards = ""
    for item in result["sequences"]:
        action_id = item["prior_action_ids_retrieved_and_cited"][0]
        cards += (
            f'<article><span class="eyebrow">SEQUENCE {item["repetition"]}</span>'
            '<h3><span class="positive">✓</span> All declared checks passed</h3>'
            '<p>Recovery, a fresh conversation citing the actual prior outcome, '
            'stale approval rejection and no insufficient-evidence execution.</p>'
            f'<code>memory-{escape(action_id)}</code></article>'
        )
    source = workflows["benchmark"]["source_commit"][:7]
    model = escape(benchmark["model"])
    memory_reference = escape(result["sequences"][0]["prior_action_ids_retrieved_and_cited"][0])
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Ripple's recorded incident recovery proof, raw evidence, source versions and explicit limits.">
<title>Ripple — Proof for judges</title><style>
:root{color-scheme:dark;--bg:#0a100d;--surface:#111e17;--line:#ffffff14;--text:#e5efe9;--muted:#abc0b3;--accent:#63e7bd}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 80% 0,#15463255,transparent 45%),var(--bg);color:var(--text);font:16px/1.65 system-ui,sans-serif}
main{max-width:1120px;margin:auto;padding:32px 28px 72px}nav{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:72px;flex-wrap:wrap}
a{color:var(--accent);text-underline-offset:5px}a:hover{color:#b1ffe5}a:focus-visible{outline:2px solid var(--accent);outline-offset:5px;border-radius:3px}
.brand{font-size:28px;letter-spacing:-1.3px;font-weight:750;text-decoration:none}.pill{font-size:12px;letter-spacing:.08em;border:1px solid var(--line);padding:7px 12px;border-radius:99px;color:var(--muted)}
.eyebrow{font-size:12px;letter-spacing:.1em;color:var(--accent)}h1{font-size:clamp(38px,6vw,62px);line-height:1.08;letter-spacing:-2px;margin:18px 0 24px;max-width:850px}
h2{font-size:28px;line-height:1.3;letter-spacing:-.7px;margin:0 0 20px}h3{font-size:19px;line-height:1.4;letter-spacing:-.25px;margin:12px 0}p{color:var(--muted);margin:12px 0 20px}
.lead{font-size:19px;max-width:800px}.actions{display:flex;gap:14px;flex-wrap:wrap;margin:28px 0 40px}.button{display:inline-flex;align-items:center;min-height:46px;padding:10px 18px;border:1px solid var(--line);border-radius:11px;text-decoration:none;font-weight:600}
.primary{background:var(--accent);color:#07291e;border-color:transparent}.primary:hover{background:#a7f8da;color:#07291e}.metrics,.sequence-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}
article,.panel{background:linear-gradient(130deg,#17291e99,#111b1580);border:1px solid var(--line);border-radius:18px;padding:28px;box-shadow:inset 0 1px #ffffff05,0 12px 36px #00000015}
.metric strong{display:block;font-size:38px;letter-spacing:-1px;color:var(--accent)}.metric span{font-size:14px;color:var(--muted)}section{margin-top:64px}.panel{margin-top:24px}.positive{color:var(--accent)}
.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:630px}th,td{text-align:left;padding:18px 16px;border-bottom:1px solid var(--line);font-size:15px}thead th{font-size:13px;color:var(--muted);font-weight:500}
tbody th{font-weight:600}.note{font-size:14px;margin-top:24px}.trace{display:grid;grid-template-columns:36px minmax(0,1fr);gap:20px;margin:28px 0}.step{display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:#2dd4a714;color:var(--accent);font-size:14px}
code,pre{font-family:ui-monospace,monospace;font-size:13px}code{overflow-wrap:anywhere}pre{padding:20px;border:1px solid var(--line);border-radius:12px;background:#07100b;overflow-x:auto;line-height:1.8}ul{padding-left:22px;color:var(--muted)}li{margin:14px 0}
.pending{border-color:#f1bf5833;background:#30271033}.pending .eyebrow{color:#f0cc80}footer{border-top:1px solid var(--line);margin-top:64px;padding-top:28px;font-size:14px;color:var(--muted)}
@media(max-width:760px){main{padding:24px 20px 56px}nav{margin-bottom:48px}.sequence-grid{grid-template-columns:1fr}.metrics{gap:12px}.metric{padding:18px}.metric strong{font-size:30px}article,.panel{padding:24px}section{margin-top:48px}}
@media(max-width:420px){.metrics{grid-template-columns:1fr}.lead{font-size:17px}.actions .button{width:100%;justify-content:center}}
</style></head><body><main>
<nav><a class="brand" href="../">ripple<span class="positive">.</span></a><span class="pill">RECORDED PROOF · SYNTHETIC DATA</span></nav>
<header><span class="eyebrow">PROOF FOR JUDGES</span><h1>Every claim has an evidence trail.</h1>
<p class="lead">A changing migration record invalidates yesterday's fix. Ripple proposes a safer simulator action, verifies recovery and remembers the measured outcome in a fresh conversation.</p>
<div class="actions"><a class="button primary" href="../showcase/ripple-demo.mp4">Watch the recorded demo ↗</a><a class="button" href="../showcase/proof-audit.json">Inspect the audit JSON ↗</a><a class="button" href="../">Open the console ↗</a></div></header>
""" + f"""
<div class="metrics"><article class="metric"><strong>3/3</strong><span>Consecutive complete sequences</span></article><article class="metric"><strong>24</strong><span>Paired benchmark runs retained</span></article><article class="metric"><strong>{result['checksummed_files']}</strong><span>Fingerprinted evidence artifacts</span></article></div>
<section><span class="eyebrow">MEASURED OUTCOMES</span><h2>A comparison you can inspect.</h2>
<p><code>{model}</code> via Ollama. Both modes receive the same documents, request probes and eight-turn / 300-second budget. Graph mode additionally receives native paths and incident memory.</p>
<div class="panel table-wrap"><table><thead><tr><th scope="col">Workflow</th><th scope="col">Expected state</th><th scope="col">Complete impact</th><th scope="col">Valid citations</th><th scope="col">Median time</th></tr></thead><tbody>{rows}</tbody></table>
<p class="note">Graph mode verified eight recoveries, the baseline seven. Four cases require missing-evidence diagnoses. Graph mode was slower and missed complete impact in two cases. Known synthetic development cases do not establish general superiority.</p>
<div class="actions">{link('../showcase/evaluations.json', 'All rows, including failures ↗')}{link(workflows['benchmark']['url'], 'Actual workflow ↗')}</div><p class="note">Measured source: <code>{source}</code>. Normal application limit: 120 seconds; reliability within that limit is unmeasured.</p></div></section>
<section><span class="eyebrow">EVIDENCE-FIRST-V2</span><h2>Three complete sequences. Actual prior memory.</h2>
<p>Five turns / {repeated['timeout_seconds']} seconds per conversation. This stricter gate requires prior-outcome retrieval <strong>and citation</strong>; it does not assert perfect impact reporting.</p><div class="sequence-grid">{cards}</div>
<div class="actions">{link('../showcase/repeatability.json', 'Read every acceptance result ↗')}{link(workflows['sequences']['url'], 'Actual sequence workflow ↗')}</div></section>
<section><span class="eyebrow">FOLLOW REPETITION 1</span><h2>From a stale fix to a measured outcome.</h2>
<div class="trace"><span class="step">1</span><div><h3>New evidence invalidates the old approval.</h3><p>The record retains the revision-1 rollback proposal, migration event and stale status. The driver reports rejection of the stale action. The offline audit checks those retained facts; it does not repeat the request.</p>{raw('recovery')}</div></div>
<div class="trace"><span class="step">2</span><div><h3>Recovery needs passing probes.</h3><p>Checkout, payments and storefront change from failing HTTP 503 to healthy HTTP 200. The auditor checks identical before/after service coverage, status codes and executed action IDs.</p>{raw('recovery')}</div></div>
<div class="trace"><span class="step">3</span><div><h3>A fresh run cites the actual prior action.</h3><p>The next run retrieves and cites <code>memory-{memory_reference}</code>. Its archived <code>LEARNED_FROM</code> edge and stored probe result match the earlier recovery. Citation is observed reference, not proof of causal dependence.</p>{raw('memory')}</div></div>
<div class="trace"><span class="step">4</span><div><h3>Missing diagnostics means no executed action.</h3><p>The third scenario ends in <code>needs_evidence</code>, lists missing diagnostics and contains no executed proposal.</p>{raw('insufficient')}</div></div></section>
<section><span class="eyebrow">REPRODUCIBLE AUDIT</span><h2>Verify the package without model credentials.</h2>
<p>The auditor checks 33 selected recordings and {result['supporting_paths_cross_checked']} returned path instances, including repeated retrievals across calls and runs. It recomputes impact accuracy from archived probe observations, validates citations and memory links, and checks the video fingerprint.</p>
<pre>python -m ripple.proof\npython -m pytest tests/test_proof.py -q\npython -m ripple.proof --online</pre>
<p>The optional online check verifies five cited GitHub workflow results and their source commits. These checks establish artifact consistency; they are not independent certification, a fresh model run or live deployment verification. Text fingerprints normalize CRLF to LF; binary media hashes are byte-exact.</p>
<div class="actions">{link('../showcase/proof-index.json', 'Fingerprint index ↗')}{link('../showcase/ci-results.txt', 'Historical CI receipts ↗')}{link('https://github.com/Guruchandar360/ripple-graph-hacks', 'Source and setup ↗')}</div>
<p class="note">Historical application CI at <code>43e8d93</code>: 46 backend tests including two actual FalkorDB container tests, eight application browser tests and one separate static-site test. The earlier HTTP proof at <code>2c8aaaa</code> records duplicate execution, database-restart persistence and foreign-visitor HTTP 404; it is separate from current Gemini verification.</p>
<p class="note">Video: {video['duration_seconds']} seconds at 1440×1000. Earlier failures remain in the public repository's provenance and development records.</p></section>
<section class="panel pending"><span class="eyebrow">REMAINING VERIFICATION</span><h2>The boundaries stay visible.</h2><ul><li>Integrated Gemini + Cloud/Render recovery remains unverified. The direct Google SDK native function-call probe passed; the participant approved the Free database's plaintext connection for synthetic data only. Database credentials and synthetic records travel without TLS; browser and Gemini traffic use HTTPS. Two actual Cloud integration tests passed.</li><li>The recorded CPU windows are 300 seconds. Production-default 120-second reliability remains unmeasured.</li><li>Registration, eligibility, meaningful participant contribution, technical understanding and final submission require the participant. AI assistance is disclosed.</li></ul></section>
<footer>Ripple · Fictional company and executable simulator · Recorded output, not production infrastructure. {link('https://github.com/Guruchandar360/ripple-graph-hacks/blob/main/docs/PROOF.md', 'Repository evidence guide ↗')}</footer>
</main></body></html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "frontend/public/proof/index.html")
    args = parser.parse_args()
    page = render()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page, encoding="utf-8", newline="\n")
    print(f"Wrote audited proof guide to {args.output}")


if __name__ == "__main__":
    main()
