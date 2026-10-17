import { useEffect, useRef, useState } from "react";
import {
  ArrowUpRight,
  Command,
  FileCheck2,
  History,
  Network,
  Search,
  Sparkles,
  X,
} from "lucide-react";
type Item = {
  label: string;
  detail: string;
  action: () => void;
  icon: typeof Search;
};
export function CommandMenu({
  onClose,
  onNavigate,
  onInvestigate,
  onSetup,
}: {
  onClose: () => void;
  onNavigate: (
    view: "investigate" | "memory" | "results" | "readiness",
  ) => void;
  onInvestigate: () => void;
  onSetup: () => void;
}) {
  const [query, setQuery] = useState("");
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const old = document.activeElement as HTMLElement | null;
    ref.current?.focus();
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("keydown", key);
      old?.focus();
    };
  }, [onClose]);
  const items: Item[] = [
    {
      label: "Open investigation",
      detail: "Graph, evidence and recovery",
      action: () => onNavigate("investigate"),
      icon: Network,
    },
    {
      label: "Start a new investigation",
      detail: "Uses configured live model and graph",
      action: onInvestigate,
      icon: Sparkles,
    },
    {
      label: "Incident memory",
      detail: "Outcomes that survive the session",
      action: () => onNavigate("memory"),
      icon: History,
    },
    {
      label: "Evaluation results",
      detail: "Measured graph / document comparisons",
      action: () => onNavigate("results"),
      icon: Search,
    },
    {
      label: "Launch checklist",
      detail: "Requirements and submission materials",
      action: () => onNavigate("readiness"),
      icon: FileCheck2,
    },
    {
      label: "Configure connections",
      detail: "Server-side graph and model access",
      action: onSetup,
      icon: Command,
    },
  ];
  return (
    <div className="modal-backdrop command-backdrop" onClick={onClose}>
      <section
        className="command-menu"
        role="dialog"
        aria-modal="true"
        aria-label="Command menu"
        onClick={(e) => e.stopPropagation()}
      >
        <label>
          <Search size={19} />
          <input
            ref={ref}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Where do you want to go?"
          />
          <button onClick={onClose} aria-label="Close command menu">
            <X size={17} />
          </button>
        </label>
        <div className="command-items">
          {items
            .filter((i) =>
              `${i.label} ${i.detail}`
                .toLowerCase()
                .includes(query.toLowerCase()),
            )
            .map((item) => (
              <button
                key={item.label}
                onClick={() => {
                  onClose();
                  item.action();
                }}
              >
                <item.icon size={18} />
                <span>
                  <strong>{item.label}</strong>
                  <small>{item.detail}</small>
                </span>
                <ArrowUpRight size={14} />
              </button>
            ))}
        </div>
        <footer>
          <span>
            <Command size={11} /> K to open
          </span>
          <span>Escape to dismiss</span>
        </footer>
      </section>
    </div>
  );
}
