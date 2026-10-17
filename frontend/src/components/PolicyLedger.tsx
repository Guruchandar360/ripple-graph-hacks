import { ArrowRight, FileText, ShieldCheck } from "lucide-react";
import type { GraphData } from "../types";

export function PolicyLedger({ graph, preview, onInspect }: { graph: GraphData; preview: boolean; onInspect: (ids: string[]) => void }) {
  const rules = graph.edges.filter(e => ["BLOCKS", "PERMITS"].includes(e.kind)).flatMap(edge => {
    const constraint = graph.nodes.find(n => n.id === edge.source);
    if (!constraint || constraint.data.active !== true) return [];
    const source = graph.edges.find(e => e.source === constraint.id && e.kind === "SUPPORTED_BY");
    return [{ edge, constraint, source }];
  });
  if (!rules.length) return null;
  return <section className="panel policy-ledger">
    <div className="panel-heading"><div><ShieldCheck size={15}/><h3>Current action constraints</h3></div><span className="panel-caption">{preview ? "FIXTURE POLICIES" : "GRAPH RELATIONSHIPS"}</span></div>
    <div className="policy-list">{rules.map(({ edge, constraint, source }) => <button className={edge.kind === "PERMITS" ? "policy-permit" : "policy-block"} key={edge.id} onClick={() => source && onInspect([source.target])}>
      <span className={`policy-badge ${edge.kind === "PERMITS" ? "permit" : "block"}`}>{edge.kind === "PERMITS" ? "PERMITS" : "BLOCKS"}</span>
      <span><strong>{String(constraint.data.action).replaceAll("_", " ")}</strong><small>{String(constraint.data.reason)}</small></span>
      <span className="policy-source"><FileText size={12}/>{source?.target}<ArrowRight size={12}/></span>
    </button>)}</div>
  </section>;
}
