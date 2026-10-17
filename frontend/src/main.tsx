import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { createRoot } from "react-dom/client";
import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  Position,
  ReactFlow,
  type ReactFlowInstance,
  type NodeProps,
  type Node,
  type Edge,
} from "@xyflow/react";
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Check,
  ChevronDown,
  ChevronRight,
  CircleCheck,
  CircleDot,
  Clock3,
  Command,
  Rocket,
  Code2,
  Database,
  ExternalLink,
  FileText,
  Fingerprint,
  GitBranch,
  History,
  Layers3,
  LoaderCircle,
  LockKeyhole,
  Network,
  Play,
  Plus,
  Radio,
  RefreshCw,
  Search,
  Server,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  Workflow,
  X,
  XCircle,
  Zap,
} from "lucide-react";
import type {
  GraphData,
  GraphNode,
  Health,
  Workspace,
  Scenario,
  Run,
  RunEvent,
  Proposal,
  Memory,
  Evaluations,
  Replay,
} from "./types";
import { api, post, isShowcase } from "./api";
import "@xyflow/react/dist/style.css";
import "./styles.css";
import "./polish.css";
import { ContextBar } from "./components/ContextBar";
import { LaunchReadiness } from "./components/LaunchReadiness";
import { CommandMenu } from "./components/CommandMenu";
import { PolicyLedger } from "./components/PolicyLedger";

const fallbackScenarios: Scenario[] = [
  {
    id: "outdated-fix",
    number: "01",
    name: "Yesterday’s fix",
    tag: "CHANGING EVIDENCE",
    description:
      "Checkout is failing after a payments release. A familiar rollback may no longer be safe.",
    incident: "INC-2041",
    symptom: "Checkout requests return HTTP 500 after payments v2.4.",
  },
  {
    id: "memory",
    number: "02",
    name: "A familiar failure",
    tag: "PERSISTENT MEMORY",
    description:
      "A new incident. An empty conversation. Can a verified past outcome help?",
    incident: "INC-2042",
    symptom:
      "Checkout requests fail with currency validation errors after a new release.",
  },
  {
    id: "insufficient",
    number: "03",
    name: "Know what you don’t know",
    tag: "INSUFFICIENT EVIDENCE",
    description:
      "Checkout is failing, but telemetry is incomplete. An honest agent should ask for evidence.",
    incident: "INC-2043",
    symptom:
      "Checkout requests return HTTP 503. Origin telemetry is unavailable.",
  },
];
const emptyGraph: GraphData = { nodes: [], edges: [] };
const human = (text: string) => text.replaceAll("_", " ");
const time = (text: string) =>
  new Date(text).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
const formatAction = (action: string) =>
  ({
    rollback_deployment: "Roll back deployment",
    disable_feature_flag: "Disable feature flag",
    restart_service: "Restart service",
  })[action] ?? human(action);

type ServiceNodeData = {
  name: string;
  owner: string;
  kind: string;
  selected?: boolean;
  healthy?: boolean;
  implicated?: boolean;
};
function ServiceNode({ data }: NodeProps<Node<ServiceNodeData>>) {
  const Icon =
    data.kind === "database"
      ? Database
      : data.kind === "edge"
        ? Radio
        : data.kind === "worker"
          ? Workflow
          : Server;
  return (
    <div
      className={`service-node ${data.selected ? "focused" : ""} ${data.implicated ? "implicated" : ""}`}
    >
      <Handle type="target" position={Position.Left} />
      <div className="node-top">
        <span className="node-icon">
          <Icon size={16} />
        </span>
        <span className="node-kind">{data.kind}</span>
        <span
          className={`node-dot ${data.healthy === true ? "ok" : data.healthy === false ? "bad" : ""}`}
        />
      </div>
      <strong>{data.name}</strong>
      <span className="node-owner">
        {data.owner}
        <span>
          {data.healthy === undefined
            ? "Service"
            : data.healthy
              ? "Healthy"
              : "Degraded"}
        </span>
      </span>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
const nodeTypes = { service: ServiceNode };

function App() {
  const [view, setView] = useState<
    "investigate" | "memory" | "results" | "readiness"
  >("investigate");
  const [scenarios, setScenarios] = useState(fallbackScenarios);
  const [scenario, setScenario] = useState(fallbackScenarios[0]);
  const [health, setHealth] = useState<Health | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [graph, setGraph] = useState<GraphData>(emptyGraph);
  const [preview, setPreview] = useState(true);
  const [run, setRun] = useState<Run | null>(null);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<string[]>([]);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [memory, setMemory] = useState<Memory[]>([]);
  const [evaluations, setEvaluations] = useState<Evaluations | null>(null);
  const [replays, setReplays] = useState<Replay[]>([]);
  const [showSetup, setShowSetup] = useState(false);
  const [showCommands, setShowCommands] = useState(false);
  const closeCommands = useCallback(() => setShowCommands(false), []);
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setShowCommands((v) => !v);
      }
    };
    document.addEventListener("keydown", key);
    return () => document.removeEventListener("keydown", key);
  }, []);
  const [showSources, setShowSources] = useState(false);
  const [mode, setMode] = useState<"graph" | "baseline">("graph");
  const [search, setSearch] = useState("");
  const generation = useRef(0);
  const runRef = useRef<Run | null>(null);
  const connected = health?.database === "connected";
  const flowRef = useRef<ReactFlowInstance<Node<ServiceNodeData>, Edge> | null>(
    null,
  );
  const [compact, setCompact] = useState(window.innerWidth <= 680);
  useEffect(() => {
    const resize = () => {
      setCompact(window.innerWidth <= 680);
      window.requestAnimationFrame(() =>
        flowRef.current?.fitView({ padding: 0.12 }),
      );
    };
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);
  const active = run?.status === "investigating";
  useEffect(() => {
    runRef.current = run;
  }, [run]);

  useEffect(() => {
    if (!showSetup && !showSources) return;
    const previous = document.activeElement as HTMLElement | null;
    const dialog = document.querySelector<HTMLElement>("[role=dialog]");
    const focusable = () =>
      Array.from(
        dialog?.querySelectorAll<HTMLElement>(
          "button:not([disabled]),a[href],input,select",
        ) ?? [],
      );
    focusable()[0]?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setShowSetup(false);
        setShowSources(false);
      }
      if (event.key === "Tab") {
        const elements = focusable();
        const first = elements[0],
          last = elements.at(-1);
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", keydown);
    return () => {
      document.removeEventListener("keydown", keydown);
      previous?.focus();
    };
  }, [showSetup, showSources]);

  const refreshHealth = useCallback(async () => {
    const result = await api<Health>("/health");
    setHealth(result);
    return result;
  }, []);

  const refreshGraph = useCallback(async () => {
    const data = await api<GraphData>("/graph");
    setGraph(data);
    setPreview(false);
    setSelected((current) =>
      current ? (data.nodes.find((n) => n.id === current.id) ?? null) : null,
    );
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await api<Scenario[]>("/scenarios");
        if (cancelled) return;
        setScenarios(list);
        const healthState = await refreshHealth();
        if (cancelled) return;
        if (healthState.database === "connected") {
          const ws = await api<Workspace>("/workspace");
          if (cancelled) return;
          setWorkspace(ws);
          if (ws.scenario) {
            setScenario(ws.scenario);
            await refreshGraph();
            return;
          }
        }
        const data = await api<{ graph: GraphData }>("/preview/outdated-fix");
        if (!cancelled) {
          setGraph(data.graph);
          setPreview(true);
        }
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshGraph, refreshHealth]);

  useEffect(() => {
    let cancelled = false;
    if (view === "memory" && connected)
      api<Memory[]>("/memory")
        .then((v) => {
          if (!cancelled) setMemory(v);
        })
        .catch((e) => setError(e.message));
    if (view === "results")
      api<Evaluations>("/evaluations")
        .then((v) => {
          if (!cancelled) setEvaluations(v);
        })
        .catch((e) => setError(e.message));
    api<Replay[]>("/replays")
      .then((v) => {
        if (!cancelled) setReplays(v);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [view, connected]);

  useEffect(() => {
    if (!run || run.status !== "investigating" || run.replay) return;
    let cancelled = false,
      pending = false;
    const id = run.id;
    const tick = async () => {
      if (pending) return;
      pending = true;
      try {
        const previous = runRef.current;
        const next = await api<Run>(
          `/runs/${id}?cursor=${previous?.cursor ?? 0}`,
        );
        if (cancelled) return;
        setRun((current) =>
          current?.id === id
            ? {
                ...next,
                events: [
                  ...current.events,
                  ...next.events.filter(
                    (e) => !current.events.some((old) => old.id === e.id),
                  ),
                ],
              }
            : current,
        );
        await refreshGraph();
        if (next.status !== "investigating")
          setWorkspace(await api<Workspace>("/workspace"));
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        pending = false;
      }
    };
    const interval = window.setInterval(tick, 1000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [run?.id, run?.status, run?.replay, refreshGraph]);

  async function selectScenario(next: Scenario) {
    const request = ++generation.current;
    setScenario(next);
    setView("investigate");
    setSelected(null);
    setSelectedEvidence([]);
    setRun(null);
    setError(null);
    setBusy(true);
    try {
      if (connected) {
        const ws = await post<Workspace>(`/scenarios/${next.id}/load`);
        if (request !== generation.current) return;
        setWorkspace(ws);
        await refreshGraph();
      } else {
        const data = await api<{ graph: GraphData }>(`/preview/${next.id}`);
        if (request !== generation.current) return;
        setGraph(data.graph);
        setPreview(true);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      if (request === generation.current) setBusy(false);
    }
  }

  async function startInvestigation() {
    setBusy(true);
    setError(null);
    setSelectedEvidence([]);
    try {
      const h = await refreshHealth();
      if (h.database !== "connected" || !h.model_configured) {
        setShowSetup(true);
        return;
      }
      if (preview || workspace?.scenario?.id !== scenario.id) {
        setWorkspace(await post<Workspace>(`/scenarios/${scenario.id}/load`));
        await refreshGraph();
      }
      const next = await post<Run>("/runs", { mode });
      setRun({ ...next, cursor: next.events.length });
      setWorkspace(await api<Workspace>("/workspace"));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function inject() {
    if (!run) return;
    setBusy(true);
    setError(null);
    try {
      setRun(
        await post<Run>(`/runs/${run.id}/evidence`, { event: "migration" }),
      );
      await refreshGraph();
      setSelectedEvidence(["migration"]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function execute(proposal: Proposal) {
    if (!run) return;
    setBusy(true);
    setError(null);
    try {
      await post(`/runs/${run.id}/actions/${proposal.id}/execute`);
      setRun(await api<Run>(`/runs/${run.id}`));
      await refreshGraph();
      setWorkspace(await api<Workspace>("/workspace"));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function openHistory(id: string) {
    setBusy(true);
    setError(null);
    setView("investigate");
    try {
      const record = await api<Run>(`/runs/${id}`);
      setRun(record);
      if (record.graph_snapshot) {
        setGraph(record.graph_snapshot);
        setPreview(false);
      }
      const original = scenarios.find((s) => s.incident === record.incident);
      if (original) setScenario(original);
      setSelected(null);
      setSelectedEvidence([]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function inspectEvidence(ids: string[]) {
    setSelectedEvidence(ids);
    const source = graph.nodes.find((n) => ids.includes(n.id));
    if (source) setSelected(source);
  }

  const affected = useMemo(() => {
    const event = run
      ? [...run.events].reverse().find((e) => e.paths?.length)
      : undefined;
    return new Set(
      event?.paths?.flatMap((p) => p.nodes) ??
        run?.diagnosis?.affected_services ??
        [],
    );
  }, [run]);
  const probes = useMemo(() => {
    const output: Record<string, boolean> = {};
    for (const n of graph.nodes)
      if (
        n.label === "Source" &&
        n.data.active !== false &&
        typeof n.data.healthy === "boolean"
      )
        output[String(n.data.service)] = n.data.healthy;
    for (const p of run?.proposals ?? [])
      for (const probe of p.result?.after ?? [])
        output[probe.service] = probe.healthy;
    return output;
  }, [graph, run]);
  const highlighted = useMemo(
    () =>
      new Set(
        run?.events
          .filter((e) =>
            e.evidence_ids.some((id) => selectedEvidence.includes(id)),
          )
          .flatMap((e) => e.paths?.flatMap((p) => p.edges) ?? []) ?? [],
      ),
    [run, selectedEvidence],
  );
  const flowNodes: Node<ServiceNodeData>[] = useMemo(
    () =>
      graph.nodes
        .filter((n) => n.label === "Service")
        .map((n) => ({
          id: n.id,
          type: "service",
          position: compact
            ? ({
                storefront: { x: 0, y: 0 },
                checkout: { x: 0, y: 140 },
                payments: { x: 0, y: 280 },
                inventory: { x: 225, y: 140 },
                ledger: { x: 225, y: 280 },
                notifications: { x: 225, y: 0 },
              }[n.id] ?? { x: 0, y: 0 })
            : { x: Number(n.data.x), y: Number(n.data.y) },
          draggable: false,
          data: {
            name: String(n.data.name),
            owner: String(n.data.owner),
            kind: String(n.data.kind),
            selected: selected?.id === n.id,
            healthy: probes[n.id],
            implicated: affected.has(n.id),
          },
        })),
    [graph, selected, probes, affected, compact],
  );
  const flowEdges: Edge[] = useMemo(
    () =>
      graph.edges
        .filter((e) => e.kind === "DEPENDS_ON")
        .map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          type: "smoothstep",
          animated: active && affected.has(e.source),
          style: {
            stroke: highlighted.has(e.id)
              ? "#5ce0c4"
              : affected.has(e.source)
                ? "#d5a05b"
                : "#34424e",
            strokeWidth: highlighted.has(e.id) ? 2.5 : 1.5,
          },
          label: highlighted.has(e.id) ? "depends on" : undefined,
          labelStyle: { fill: "#85a49e", fontSize: 10 },
          labelBgStyle: { fill: "#101920" },
          markerEnd: {
            type: "arrowclosed" as const,
            color: highlighted.has(e.id) ? "#5ce0c4" : "#52616f",
          },
        })),
    [graph, highlighted, active, affected],
  );
  const services = graph.nodes.filter((n) => n.label === "Service");
  const sources = graph.nodes.filter((n) => n.label === "Source");
  const latestProposal = run?.proposals.at(-1);
  const status = run?.status ?? (preview ? "fixture_preview" : "ready");

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setView("investigate");
          }}
          aria-label="Ripple home"
        >
          <span className="brand-mark">
            <Radio size={25} />
          </span>
          ripple<span className="brand-dot">.</span>
        </a>
        <div className="workspace-picker">
          <span className="workspace-avatar">N</span>
          <div>
            <strong>Northstar Commerce</strong>
            <span>Synthetic organization</span>
          </div>
          <ChevronDown size={14} />
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          <button
            className={
              view === "investigate" ? "nav-item selected" : "nav-item"
            }
            onClick={() => setView("investigate")}
          >
            <Network size={17} />
            Investigate<span className="key-hint">01</span>
          </button>
          <button
            className={view === "memory" ? "nav-item selected" : "nav-item"}
            onClick={() => setView("memory")}
          >
            <History size={17} />
            Incident memory
            <span className="nav-count">{workspace?.memory_count ?? 0}</span>
          </button>
          <button
            className={view === "results" ? "nav-item selected" : "nav-item"}
            onClick={() => setView("results")}
          >
            <Activity size={17} />
            Evaluation results
          </button>
          <button
            className={view === "readiness" ? "nav-item selected" : "nav-item"}
            onClick={() => setView("readiness")}
          >
            <Rocket size={17} />
            Launch checklist
            <ArrowUpRight className="nav-extra" size={12} />
          </button>
        </nav>
        <div className="nav-label scenario-label">
          SCENARIOS<span>03</span>
        </div>
        <div className="scenario-list">
          {scenarios.map((s) => (
            <button
              disabled={busy || active}
              key={s.id}
              onClick={() => selectScenario(s)}
              className={`scenario-item ${scenario.id === s.id ? "current" : ""}`}
            >
              <span className="scenario-number">{s.number}</span>
              <span>
                <strong>{s.name}</strong>
                <small>{s.tag}</small>
              </span>
              {scenario.id === s.id && <span className="scenario-current" />}
            </button>
          ))}
        </div>
        <div className="nav-label history-label">
          RECENT INVESTIGATIONS
          <button
            title="New investigation"
            onClick={() => {
              setRun(null);
              setView("investigate");
            }}
            disabled={active}
          >
            <Plus size={14} />
          </button>
        </div>
        <div className="history-list">
          {workspace?.history.length ? (
            workspace.history.slice(0, 5).map((h) => (
              <button key={h.id} onClick={() => openHistory(h.id)}>
                <CircleDot size={13} />
                <span>
                  {h.incident}
                  <small>{human(h.status)}</small>
                </span>
                <ChevronRight size={12} />
              </button>
            ))
          ) : (
            <div className="history-empty">
              Your investigations will
              <br />
              appear here.
            </div>
          )}
        </div>
        <div className="sidebar-bottom">
          <div className="graph-powered">
            <GitBranch size={18} />
            <div>
              Connected by design<span>Powered by FalkorDB</span>
            </div>
            <ArrowUpRight size={14} />
          </div>
          <div className="profile">
            <span className="profile-avatar">
              <Fingerprint size={18} />
            </span>
            <div>
              {isShowcase ? "Public showcase" : "Guest workspace"}<span>{isShowcase ? "Synthetic recordings only" : "Private browser session"}</span>
            </div>
            <LockKeyhole size={13} />
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <ChevronRight size={13} />
            <strong>
              {view === "investigate"
                ? "Investigate"
                : view === "memory"
                  ? "Incident memory"
                  : view === "readiness"
                    ? "Launch checklist"
                    : "Evaluation results"}
            </strong>
          </div>
          <div className="topbar-right">
            <button
              className="command-trigger"
              onClick={() => setShowCommands(true)}
              aria-label="Open command menu"
            >
              <Search size={13} />
              <span>Quick actions</span>
              <kbd>
                <Command size={10} /> K
              </kbd>
            </button>
            <span className="simulation-label">
              <Layers3 size={12} />
              SIMULATOR
            </span>
            <span className={`connection ${connected ? "connected" : ""}`}>
              <i />
              {isShowcase ? "Recorded graphs" : connected ? "Graph connected" : "Graph offline"}
            </span>
            <button
              className="icon-button"
              title="Connection and setup"
              onClick={() => setShowSetup(true)}
            >
              <Code2 size={17} />
            </button>
          </div>
        </header>
        {isShowcase && (
          <div className="showcase-notice">
            <Play size={14} />
            <span><strong>Recorded showcase</strong> · Synthetic incidents. Explore actual exported runs in Results. Live investigations require the local backend.</span>
            <a href="https://github.com/Guruchandar360/ripple-graph-hacks#run-locally" target="_blank" rel="noreferrer">Run locally <ArrowUpRight size={12} /></a>
          </div>
        )}
        <main>
          {error && (
            <div role="alert" className="error-banner">
              <TriangleAlert size={17} />
              <span>{error}</span>
              <button aria-label="Dismiss error" onClick={() => setError(null)}>
                <X size={15} />
              </button>
            </div>
          )}
          {view === "investigate" && (
            <>
              <section className="page-intro">
                <div>
                  <div className="eyebrow">
                    <span className="eyebrow-line" />
                    CONTEXT BEFORE ACTION
                  </div>
                  <h1>Follow the evidence.</h1>
                  <p>
                    Trace the impact. Challenge the obvious fix. Verify what
                    works.
                  </p>
                </div>
                <button
                  className="secondary small"
                  onClick={() => setShowSources(true)}
                >
                  <BookOpen size={15} />
                  Explore evidence
                  <ArrowUpRight size={13} />
                </button>
              </section>
              <div className={`mode-banner ${preview ? "preview" : ""}`}>
                <span>
                  <span className="mini-pill">
                    {run?.replay
                      ? "REPLAY"
                      : preview
                        ? "FIXTURE PREVIEW"
                        : "LIVE WORKSPACE"}
                  </span>
                  {run?.replay
                    ? `Recorded ${run.model ?? "model"} investigation · ${run.mode} mode. Actions are disabled.`
                    : preview
                      ? "Explore the synthetic scenario. Connect your graph and model to investigate."
                      : "Synthetic infrastructure. Real graph queries, state changes, and probe results."}
                </span>
                <button onClick={() => setShowSetup(true)}>
                  {preview ? "Connect workspace" : "Connection details"}
                  <ArrowRight size={13} />
                </button>
              </div>
              <ContextBar
                services={services.length}
                sources={sources.filter((s) => s.data.active !== false).length}
                revision={workspace?.revision ?? run?.current_revision ?? 0}
                memory={workspace?.memory_count ?? 0}
                preview={preview}
                stage={
                  run?.status === "recovered"
                    ? 4
                    : run?.proposals.length
                      ? 3
                      : affected.size
                        ? 2
                        : run?.events.length && run.events.length > 1
                          ? 1
                          : 0
                }
              />
              <label className="mobile-scenario-picker">
                <span>SCENARIO</span>
                <select
                  aria-label="Scenario"
                  value={scenario.id}
                  disabled={active || busy}
                  onChange={(e) => {
                    const next = scenarios.find((s) => s.id === e.target.value);
                    if (next) selectScenario(next);
                  }}
                >
                  {scenarios.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.number} · {s.name}
                    </option>
                  ))}
                </select>
                <ChevronDown size={13} />
              </label>
              <section className="incident-card">
                <div className="incident-main">
                  <div className="incident-title-row">
                    <span className="incident-code">
                      {run?.incident ?? scenario.incident}
                    </span>
                    <span
                      className={`status-pill ${status === "recovered" ? "green" : status === "investigating" ? "teal" : "amber"}`}
                    >
                      <span className="status-dot" />
                      {human(status)}
                    </span>
                  </div>
                  <h2>
                    {scenario.id === "insufficient"
                      ? "Checkout is failing. The cause is unclear."
                      : "Checkout is failing after a payments release."}
                  </h2>
                  <p>{scenario.description}</p>
                  <div className="incident-meta">
                    <span>
                      <Server size={13} />
                      checkout
                    </span>
                    <span>
                      <UsersIcon />
                      Commerce team
                    </span>
                    <span>
                      <Clock3 size={13} />
                      {run ? time(run.created_at) : "Awaiting investigation"}
                    </span>
                  </div>
                </div>
                <div className="incident-action">
                  <button
                    className="primary"
                    onClick={startInvestigation}
                    disabled={busy || active || !!run?.replay}
                  >
                    {busy || active ? (
                      <LoaderCircle size={16} className="spin" />
                    ) : (
                      <Sparkles size={16} />
                    )}
                    {active
                      ? "Investigating…"
                      : run
                        ? "Investigate again"
                        : "Start investigation"}
                    <ArrowRight size={15} />
                  </button>
                  <label className="mode-select">
                    <select
                      aria-label="Investigation mode"
                      value={mode}
                      onChange={(e) =>
                        setMode(e.target.value as "graph" | "baseline")
                      }
                      disabled={active}
                    >
                      <option value="graph">Graph-backed agent</option>
                      <option value="baseline">Full-document baseline</option>
                    </select>
                    <ChevronDown size={12} />
                  </label>
                </div>
              </section>
              <div className="investigation-grid">
                <div className="center-column">
                  <section className="panel graph-panel">
                    <div className="panel-heading">
                      <div>
                        <Network size={15} />
                        <h3>Service dependency map</h3>
                        <span className="count-tag">
                          {services.length} services
                        </span>
                      </div>
                      <span className="panel-caption">
                        {run?.replay
                          ? "RECORDED GRAPH"
                          : preview
                            ? "FIXTURE TOPOLOGY"
                            : "FALKORDB GRAPH"}
                      </span>
                    </div>
                    <div className="graph-context">
                      <span>
                        <i className="legend-dot" />
                        Service
                      </span>
                      <span>
                        <i className="legend-line" />
                        Depends on
                      </span>
                      {affected.size > 0 && (
                        <span className="amber-text">
                          {affected.size} services in retrieved impact paths
                        </span>
                      )}
                      <span className="graph-hint">
                        Select a node to inspect
                      </span>
                    </div>
                    <div className="flow-wrapper">
                      <ReactFlow
                        key={compact ? "compact" : "wide"}
                        onInit={(instance) => {
                          flowRef.current = instance;
                        }}
                        nodes={flowNodes}
                        edges={flowEdges}
                        nodeTypes={nodeTypes}
                        fitView
                        fitViewOptions={{ padding: 0.16 }}
                        minZoom={0.15}
                        maxZoom={1.3}
                        nodesConnectable={false}
                        nodesDraggable={false}
                        onNodeClick={(_, node) => {
                          setSelected(
                            graph.nodes.find((n) => n.id === node.id) ?? null,
                          );
                          setSelectedEvidence([]);
                        }}
                        proOptions={{ hideAttribution: true }}
                      >
                        <Background
                          variant={BackgroundVariant.Dots}
                          gap={20}
                          size={1}
                          color="#27333d"
                        />
                        <Controls showInteractive={false} />
                      </ReactFlow>
                      {!services.length && (
                        <div className="graph-empty">
                          <Network size={30} />
                          <p>Loading service topology…</p>
                        </div>
                      )}
                    </div>
                    <div className="graph-footer">
                      <span>
                        <GitBranch size={12} />
                        {
                          graph.edges.filter((e) => e.kind === "DEPENDS_ON")
                            .length
                        }{" "}
                        dependency relationships
                      </span>
                      <span>
                        {preview
                          ? "Read-only preview"
                          : `Evidence revision ${workspace?.revision ?? run?.current_revision ?? "—"}`}
                        <LockKeyhole size={11} />
                      </span>
                    </div>
                  </section>
                  <PolicyLedger graph={graph} preview={preview} onInspect={inspectEvidence} />
                  <section className="panel timeline-panel">
                    <div className="panel-heading">
                      <div>
                        <Activity size={15} />
                        <h3>Investigation timeline</h3>
                        {run && (
                          <span className="count-tag">{run.events.length}</span>
                        )}
                      </div>
                      <span className="panel-caption">
                        {active ? (
                          <>
                            <span className="live-dot" />
                            LIVE
                          </>
                        ) : (
                          "EVIDENCE, NOT GUESSWORK"
                        )}
                      </span>
                    </div>
                    {!run ? (
                      <div className="timeline-empty">
                        <div className="empty-orbit">
                          <Search size={22} />
                        </div>
                        <h4>Every decision starts with context.</h4>
                        <p>
                          Start an investigation to see graph queries, evidence,
                          <br />
                          and recovery decisions unfold here.
                        </p>
                        <div className="process-steps">
                          <span>
                            <Search size={13} />
                            Investigate
                          </span>
                          <ChevronRight size={12} />
                          <span>
                            <ShieldCheck size={13} />
                            Validate
                          </span>
                          <ChevronRight size={12} />
                          <span>
                            <CircleCheck size={13} />
                            Verify
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="timeline">
                        {run.events.map((e) => (
                          <TimelineEvent
                            key={e.id}
                            event={e}
                            onInspect={inspectEvidence}
                            selected={e.evidence_ids.some((id) =>
                              selectedEvidence.includes(id),
                            )}
                          />
                        ))}
                        {active && (
                          <div className="thinking">
                            <LoaderCircle size={15} className="spin" />
                            Waiting for the next completed tool call…
                          </div>
                        )}
                        {run.error && (
                          <div className="inline-warning">
                            <TriangleAlert size={15} />
                            {run.error}
                          </div>
                        )}
                        {run.diagnosis?.missing_evidence.length ? (
                          <div className="missing-evidence">
                            <strong>Evidence needed to continue</strong>
                            {run.diagnosis.missing_evidence.map((m) => (
                              <p key={m}>
                                <Plus size={12} />
                                {m}
                              </p>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    )}
                    {run && (
                      <div className="timeline-footer">
                        {run.model && <span>{run.model}</span>}
                        <span>{run.model_calls} model calls</span>
                        <span>
                          {(run.elapsed_ms / 1000).toFixed(1)}s elapsed
                        </span>
                        <span>
                          {run.mode === "baseline"
                            ? "Document baseline"
                            : "Graph-backed run"}
                        </span>
                      </div>
                    )}
                  </section>
                </div>
                <aside className="detail-column">
                  <section className="panel recommendation">
                    <div className="panel-heading">
                      <div>
                        <ShieldCheck size={15} />
                        <h3>Recovery decision</h3>
                      </div>
                      <span className="subtle-circle">
                        <LockKeyhole size={11} />
                      </span>
                    </div>
                    {latestProposal ? (
                      <div className="decision-body">
                        <span
                          className={`eyebrow ${latestProposal.result?.verified ? "teal-text" : "amber-text"}`}
                        >
                          {latestProposal.stale
                            ? "APPROVAL INVALIDATED"
                            : latestProposal.result?.verified
                              ? "VERIFIED OUTCOME"
                              : latestProposal.blocked_reason
                                ? "ACTION BLOCKED"
                                : "AWAITING YOUR APPROVAL"}
                        </span>
                        <h3>{formatAction(latestProposal.action)}</h3>
                        <div className="code-chip">{latestProposal.target}</div>
                        <p>{latestProposal.summary}</p>
                        {latestProposal.blocked_reason && (
                          <div className="inline-warning">
                            <TriangleAlert size={15} />
                            {latestProposal.blocked_reason}
                          </div>
                        )}
                        {latestProposal.stale && (
                          <div className="inline-warning">
                            <RefreshCw size={15} />
                            New evidence requires a fresh investigation.
                          </div>
                        )}
                        <div className="citation-row">
                          {latestProposal.evidence_ids.map((id) => (
                            <button
                              key={id}
                              onClick={() => inspectEvidence([id])}
                            >
                              <FileText size={11} />
                              {id}
                            </button>
                          ))}
                        </div>
                        {latestProposal.result ? (
                          <div className="probe-results">
                            <strong>
                              {latestProposal.result.verified
                                ? "Recovery confirmed by probes"
                                : "Recovery failed verification"}
                            </strong>
                            {latestProposal.result.after.map((p) => (
                              <div key={p.service}>
                                {p.healthy ? (
                                  <CircleCheck size={13} />
                                ) : (
                                  <XCircle size={13} />
                                )}
                                <span>{p.service}</span>
                                <b><span className="before-probe">{latestProposal.result?.before.find(b => b.service === p.service)?.status_code ?? "—"}</span> → {p.status_code}</b>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <button
                            className="primary full"
                            disabled={
                              busy ||
                              latestProposal.stale ||
                              !!latestProposal.blocked_reason ||
                              run?.status !== "awaiting_approval" ||
                              run?.replay
                            }
                            onClick={() => execute(latestProposal)}
                          >
                            <Play size={14} />
                            Approve & execute
                          </button>
                        )}
                      </div>
                    ) : (
                      <div className="decision-empty">
                        <span className="shield-illustration">
                          <ShieldCheck size={26} />
                        </span>
                        <h4>Evidence first. Action second.</h4>
                        <p>
                          {active
                            ? "Ripple is gathering evidence. A proposal will appear when an action is justified."
                            : "No recovery action has been proposed. Recommendations must be supported by retrieved evidence."}
                        </p>
                        <div className="guardrail">
                          <LockKeyhole size={12} />
                          Execution requires your approval
                        </div>
                      </div>
                    )}
                  </section>
                  {scenario.id === "outdated-fix" && (
                    <section className="evidence-change-card">
                      <div className="evidence-change-icon">
                        <Zap size={17} />
                      </div>
                      <div className="eyebrow amber-text">
                        THE CONTEXT CAN CHANGE
                      </div>
                      <h3>
                        A familiar fix.
                        <br />A new constraint.
                      </h3>
                      <p>
                        A late migration record can invalidate an earlier
                        recovery decision.
                      </p>
                      <button
                        onClick={inject}
                        disabled={
                          !run ||
                          active ||
                          busy ||
                          preview ||
                          run.replay ||
                          sources.some((s) => s.id === "migration")
                        }
                      >
                        {sources.some((s) => s.id === "migration") ? (
                          <>
                            <Check size={13} />
                            Migration evidence present
                          </>
                        ) : (
                          <>
                            <Plus size={13} />
                            Inject migration evidence
                          </>
                        )}
                      </button>
                      <small>
                        {preview
                          ? "Available during a live investigation"
                          : "All earlier approvals are revalidated."}
                      </small>
                    </section>
                  )}
                  <section className="panel inspector">
                    <div className="panel-heading">
                      <div>
                        <FileText size={15} />
                        <h3>
                          {selected ? "Selected context" : "Evidence library"}
                        </h3>
                      </div>
                      {selected && (
                        <button
                          className="icon-button"
                          aria-label="Clear selected context"
                          onClick={() => setSelected(null)}
                        >
                          <X size={13} />
                        </button>
                      )}
                    </div>
                    {selected ? (
                      <div className="inspector-body">
                        <span className="eyebrow">{selected.label}</span>
                        <h4>
                          {String(
                            selected.data.title ??
                              selected.data.name ??
                              selected.id,
                          )}
                        </h4>
                        {selected.data.text ? (
                          <p>{String(selected.data.text)}</p>
                        ) : (
                          <>
                            <p>
                              Owner:{" "}
                              {String(
                                selected.data.owner ??
                                  "See graph relationships",
                              )}
                            </p>
                            <p>
                              {String(
                                selected.data.summary ??
                                  "Select a linked source to inspect supporting evidence.",
                              )}
                            </p>
                          </>
                        )}
                        {selected.data.effective_at && (
                          <div className="source-time">
                            <Clock3 size={12} />
                            Effective{" "}
                            {String(selected.data.effective_at)
                              .replace("T", " ")
                              .slice(0, 16)}{" "}
                            UTC
                          </div>
                        )}
                        <span className="source-id">{selected.id}</span>
                      </div>
                    ) : (
                      <div className="source-list">
                        {sources
                          .filter((s) => !s.id.startsWith("probe-"))
                          .slice(0, 5)
                          .map((s) => (
                            <button
                              key={s.id}
                              onClick={() => {
                                setSelected(s);
                                setSelectedEvidence([s.id]);
                              }}
                            >
                              <FileText size={14} />
                              <span>{String(s.data.title)}</span>
                              <ChevronRight size={12} />
                            </button>
                          ))}
                        {!sources.length && (
                          <p className="muted">No evidence loaded.</p>
                        )}
                      </div>
                    )}
                  </section>
                </aside>
              </div>
              <footer className="page-footer">
                <span>
                  <ShieldCheck size={13} />
                  Synthetic environment · No production systems connected
                </span>
                <span>
                  Built on connected evidence
                  <span className="footer-dot">·</span>FalkorDB
                </span>
              </footer>
            </>
          )}
          {view === "memory" && (
            <>
              <section className="page-intro">
                <div>
                  <div className="eyebrow">
                    <span className="eyebrow-line" />
                    KNOWLEDGE THAT PERSISTS
                  </div>
                  <h1>Remember what worked.</h1>
                  <p>
                    Verified outcomes survive the conversation. Applicability
                    still needs checking.
                  </p>
                </div>
                <History size={36} className="teal-text" />
              </section>
              <div className="section-summary">
                <div>
                  <span className="eyebrow">PERSISTED OUTCOMES</span>
                  <strong>{memory.length}</strong>
                </div>
                <p>
                  {isShowcase ? "Recorded outcomes exported from FalkorDB." : "Saved in your isolated FalkorDB graph."}
                  <br />
                  Failed actions stay visible as failed outcomes.
                </p>
              </div>
              {memory.length ? (
                <div className="memory-grid">
                  {memory.map((m) => (
                    <article key={m.id} className="panel memory-card">
                      <div className="memory-top">
                        <span className="incident-code">{m.incident}</span>
                        <span
                          className={`status-pill ${m.verified ? "green" : "amber"}`}
                        >
                          {m.verified ? (
                            <CircleCheck size={12} />
                          ) : (
                            <TriangleAlert size={12} />
                          )}
                          {m.verified ? "Verified" : "Failed recovery"}
                        </span>
                      </div>
                      <h2>{formatAction(m.action)}</h2>
                      <span className="code-chip">{m.target}</span>
                      <p>{m.summary}</p>
                      <div className="memory-applicability">
                        <ShieldCheck size={15} />
                        {m.applicability}
                      </div>
                      <span className="muted text-xs">
                        {new Date(m.created_at).toLocaleString()}
                      </span>
                    </article>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={<History size={30} />}
                  title="No incident memory yet"
                  detail={
                    connected
                      ? "Execute a recovery action to persist its measured outcome. A fresh investigation can retrieve it."
                      : "Connect FalkorDB and complete an investigation to start building persistent incident memory."
                  }
                  action={() => setView("investigate")}
                  actionLabel="Return to investigation"
                />
              )}
            </>
          )}
          {view === "results" && (
            <>
              <section className="page-intro">
                <div>
                  <div className="eyebrow">
                    <span className="eyebrow-line" />
                    MEASURED, NOT ASSUMED
                  </div>
                  <h1>Show the evidence.</h1>
                  <p>
                    A controlled comparison against a full-document-context
                    baseline.
                  </p>
                </div>
                <Activity size={36} className="teal-text" />
              </section>
              <div className="evaluation-info">
                <ShieldCheck size={19} />
                <p>
                  Both modes use the same model, source records, simulator and
                  turn budget. The baseline receives full documents; graph
                  traversal and incident-memory retrieval are disabled.
                  Synthetic results do not establish general superiority.
                </p>
              </div>
              {evaluations?.measured ? (
                <>
                  <p className="evaluation-info">Measured with {evaluations.model} via {evaluations.model_provider}. {evaluations.limitations}</p>
                  <div className="metrics-grid">
                    <Metric
                      label="Measured runs"
                      value={evaluations.cases.length}
                    />
                    <Metric
                      label="Expected outcomes met"
                      value={evaluations.summary?.expected_met ?? 0}
                    />
                    <Metric
                      label="Verified recoveries"
                      value={evaluations.summary?.verified_recoveries ?? 0}
                    />
                  </div>
                  <div className="panel table-panel">
                    <table>
                      <thead>
                        <tr>
                          <th>Case / mode</th>
                          <th>Outcome</th>
                          <th>Citations</th>
                          <th>Calls</th>
                          <th>Time</th>
                        </tr>
                      </thead>
                      <tbody>
                        {evaluations.cases.map((c, i) => (
                          <tr key={i}>
                            <td>
                              {c.name}
                              <small>{c.mode}</small>
                            </td>
                            <td>
                              <span
                                className={
                                  c.expected_met ? "teal-text" : "amber-text"
                                }
                              >
                                {c.expected_met ? "Passed" : "Review"}
                              </span>
                            </td>
                            <td>{c.valid_citations ? "Valid" : "Invalid"}</td>
                            <td>{c.model_calls}</td>
                            <td>{(c.elapsed_ms / 1000).toFixed(1)}s</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <EmptyState
                  icon={<Activity size={30} />}
                  title="No benchmark scores claimed"
                  detail="The 12-case evaluator is ready to run when the model and graph are configured. Results appear here only after actual execution."
                />
              )}
              <section className="panel replay-panel">
                <div className="panel-heading">
                  <div>
                    <Play size={15} />
                    <h3>Recorded investigations</h3>
                  </div>
                  <span className="count-tag">{replays.length}</span>
                </div>
                {replays.length ? (
                  replays.map((r) => (
                    <button
                      key={r.id}
                      data-replay-id={r.id}
                      data-replay-status={r.status}
                      data-replay-mode={r.mode}
                      data-replay-case={r.evaluation_case}
                      className="replay-row"
                      onClick={() => {
                        setRun({ ...r, replay: true });
                        setGraph(r.graph);
                        setScenario(r.scenario);
                        setSelected(null);
                        setSelectedEvidence([]);
                        setPreview(false);
                        setView("investigate");
                      }}
                    >
                      <Play size={15} />
                      <span>
                        {r.incident} · {human(r.status)} · {r.mode} {r.evaluation_case ? `· ${r.evaluation_case}` : ""}
                      </span>
                      <span className="mini-pill">REPLAY</span>
                      <ArrowRight size={14} />
                    </button>
                  ))
                ) : (
                  <p className="empty-recordings">
                    No live runs have been exported yet. Fixture previews are
                    never presented as recordings.
                  </p>
                )}
              </section>
            </>
          )}
          {view === "readiness" && (
            <LaunchReadiness onConfigure={() => setShowSetup(true)} />
          )}
        </main>
      </div>
      {showCommands && (
        <CommandMenu
          onClose={closeCommands}
          onNavigate={setView}
          onInvestigate={() => {
            setView("investigate");
            startInvestigation();
          }}
          onSetup={() => setShowSetup(true)}
        />
      )}
      {showSetup && (
        <div className="modal-backdrop" onClick={() => setShowSetup(false)}>
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="setup-title"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="modal-close icon-button"
              aria-label="Close setup"
              onClick={() => setShowSetup(false)}
            >
              <X size={20} />
            </button>
            <span className="setup-icon">
              <GitBranch size={26} />
            </span>
            <div className="eyebrow">LIVE CONNECTIONS</div>
            <h2 id="setup-title">Connect your workspace.</h2>
            <p>
              Explore fixture data now. Live investigation requires a real graph
              and a configured model on the server.
            </p>
            <div className="setup-row">
              <Database size={19} />
              <div>
                <strong>FalkorDB</strong>
                <span>Durable evidence, dependencies and incident memory</span>
              </div>
              <span className={`status-pill ${connected ? "green" : "amber"}`}>
                {connected ? "Connected" : "Unavailable"}
              </span>
            </div>
            <div className="setup-row">
              <Sparkles size={19} />
              <div>
                <strong>{health?.model ?? "Gemini 2.5 Flash"}</strong>
                <span>Server-side API key · Free-tier quotas apply</span>
              </div>
              <span
                className={`status-pill ${health?.model_configured ? "green" : "amber"}`}
              >
                {health?.model_configured ? "Key configured" : "Key missing"}
              </span>
            </div>
            <div className="setup-code">
              <span>Server environment</span>
              <code>
                FALKORDB_HOST=your-host
                <br />
                FALKORDB_PORT=6379
                <br />
                FALKORDB_PASSWORD=…
                <br />
                FALKORDB_SSL=true
                <br />
                GEMINI_API_KEY=…
              </code>
            </div>
            <p className="text-xs">
              Keys stay on the server. Configure .env locally or environment
              variables in your host, then restart the backend. Local Docker
              uses FALKORDB_SSL=false. Key presence does not verify model
              access.
            </p>
            <button
              className="primary full"
              onClick={async () => {
                try {
                  await refreshHealth();
                  setError(null);
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            >
              <RefreshCw size={14} />
              Check connection
            </button>
            <div className="setup-links">
              <a
                href="https://www.falkordb.com/try-free/"
                target="_blank"
                rel="noreferrer"
              >
                FalkorDB setup
                <ExternalLink size={11} />
              </a>
              <a
                href="https://aistudio.google.com/apikey"
                target="_blank"
                rel="noreferrer"
              >
                Gemini API key
                <ExternalLink size={11} />
              </a>
            </div>
          </section>
        </div>
      )}
      {showSources && (
        <div className="modal-backdrop" onClick={() => setShowSources(false)}>
          <section
            className="modal sources-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="sources-title"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="modal-close icon-button"
              aria-label="Close evidence library"
              onClick={() => setShowSources(false)}
            >
              <X size={20} />
            </button>
            <div className="eyebrow">
              {preview ? "SYNTHETIC FIXTURE" : "WORKSPACE SOURCES"}
            </div>
            <h2 id="sources-title">Evidence library.</h2>
            <label className="search-box">
              <Search size={16} />
              <input
                placeholder="Search source records…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </label>
            {sources
              .filter((s) =>
                `${s.data.title} ${s.data.text}`
                  .toLowerCase()
                  .includes(search.toLowerCase()),
              )
              .map((s) => (
                <article className="source-document" key={s.id}>
                  <span className="source-id">{s.id}</span>
                  <h3>{String(s.data.title)}</h3>
                  <p>{String(s.data.text)}</p>
                  <small>
                    Effective {String(s.data.effective_at)} · Ingested{" "}
                    {String(s.data.ingested_at)}
                  </small>
                </article>
              ))}
          </section>
        </div>
      )}
    </div>
  );
}

function UsersIcon() {
  return <Fingerprint size={13} />;
}
function TimelineEvent({
  event,
  onInspect,
  selected,
}: {
  event: RunEvent;
  onInspect: (ids: string[]) => void;
  selected: boolean;
}) {
  const Icon =
    event.kind === "verified"
      ? CircleCheck
      : event.kind === "warning"
        ? TriangleAlert
        : event.kind === "hypothesis"
          ? Sparkles
          : GitBranch;
  return (
    <article
      className={`timeline-event ${event.kind} ${selected ? "event-selected" : ""}`}
    >
      <span className="event-icon">
        <Icon size={14} />
      </span>
      <div className="event-content">
        <div className="event-heading">
          <strong>{event.title}</strong>
          <time>{time(event.at)}</time>
        </div>
        <span className="event-kind">
          {event.kind === "verified"
            ? "VERIFIED OUTCOME"
            : event.kind.toUpperCase()}
        </span>
        <p>{event.detail}</p>
        {event.evidence_ids.length > 0 && (
          <div className="citation-row">
            {event.evidence_ids.map((id) => (
              <button onClick={() => onInspect([id])} key={id}>
                <FileText size={10} />
                {id}
              </button>
            ))}
          </div>
        )}
      </div>
    </article>
  );
}
function EmptyState({
  icon,
  title,
  detail,
  action,
  actionLabel,
}: {
  icon: React.ReactNode;
  title: string;
  detail: string;
  action?: () => void;
  actionLabel?: string;
}) {
  return (
    <div className="panel empty-state">
      <span className="empty-state-icon">{icon}</span>
      <h2>{title}</h2>
      <p>{detail}</p>
      {action && (
        <button className="secondary" onClick={action}>
          {actionLabel}
          <ArrowRight size={14} />
        </button>
      )}
    </div>
  );
}
function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="panel metric">
      <span className="eyebrow">{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
