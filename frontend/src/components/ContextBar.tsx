import {
  Activity,
  ArrowRight,
  Check,
  Database,
  FileText,
  GitBranch,
  History,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
export function ContextBar({
  services,
  sources,
  revision,
  memory,
  preview,
  stage,
}: {
  services: number;
  sources: number;
  revision: number;
  memory: number;
  preview: boolean;
  stage: number;
}) {
  const metrics = [
    {
      label: "Mapped services",
      value: services,
      icon: GitBranch,
      detail: preview ? "Synthetic topology" : "Graph entities",
    },
    {
      label: "Source records",
      value: sources,
      icon: FileText,
      detail: preview ? "Fixture evidence" : "Retrieved context",
    },
    {
      label: "Evidence revision",
      value: preview ? "—" : String(revision),
      icon: Database,
      detail: preview
        ? "Connect to version facts"
        : "Approvals track this version",
    },
    {
      label: "Saved outcomes",
      value: memory,
      icon: History,
      detail: "Successes and failures",
    },
  ];
  return (
    <>
      <div className="context-metrics">
        {metrics.map((m) => (
          <div className="context-metric" key={m.label}>
            <span className="metric-icon">
              <m.icon size={17} />
            </span>
            <span>
              <small>{m.label}</small>
              <strong>{m.value}</strong>
              <em>{m.detail}</em>
            </span>
          </div>
        ))}
      </div>
      <div className="decision-journey">
        <span className="journey-label">
          <Activity size={13} />
          DECISION PATH
        </span>
        {[
          { name: "Observe", icon: FileText },
          { name: "Connect", icon: GitBranch },
          { name: "Validate", icon: ShieldCheck },
          { name: "Verify", icon: Sparkles },
        ].map((s, i) => (
          <span className="journey-group" key={s.name}>
            <span className={`journey-step ${i < stage ? "done" : ""}`}>
              {i < stage ? <Check size={12} /> : <s.icon size={12} />}
              {s.name}
            </span>
            {i < 3 && <ArrowRight size={11} className="journey-arrow" />}
          </span>
        ))}
        <span className="journey-note">
          {preview
            ? "Preview · no agent run"
            : stage === 4
              ? "Recovery proven by probes"
              : "Completed tool events only"}
        </span>
      </div>
    </>
  );
}
