import type { EvaluationRow } from "../types";

export function Comparison({rows}:{rows:EvaluationRow[]}) {
  return <section className="panel comparison-panel">
    <div className="panel-heading"><div><h3>Graph and document workflows</h3></div><span className="panel-caption">ACTUAL MEASUREMENTS</span></div>
    <div className="comparison-scroll"><table><thead><tr><th>Workflow</th><th>Expected status</th><th>Complete impact</th><th>Valid citations</th><th>Execution violations</th><th>Median time</th></tr></thead><tbody>{["graph","baseline"].map(mode=>{
      const selected=rows.filter(r=>r.mode===mode);
      if (!selected.length) return null;
      const times=selected.map(r=>r.elapsed_ms).sort((a,b)=>a-b);
      const mid=Math.floor(times.length/2);
      const median=times.length%2 ? times[mid] : (times[mid-1]+times[mid])/2;
      return <tr key={mode}><td><strong>{mode==="graph" ? "Graph-backed" : "Full documents"}</strong><small>{selected.length} measured runs</small></td><td>{selected.filter(r=>r.expected_met).length}/{selected.length}</td><td>{selected.filter(r=>r.correct_impact).length}/{selected.length}</td><td>{selected.filter(r=>r.valid_citations).length}/{selected.length}</td><td>{selected.reduce((n,r)=>n+r.executed_violations,0)}</td><td>{(median/1000).toFixed(1)}s</td></tr>;
    })}</tbody></table></div>
    <p className="comparison-note">Recovery status and impact accuracy are separate. Zero executed violations also reflects the shared deterministic guard. These development cases are not held-out data.</p>
  </section>;
}
