export type Scenario = {
  id: string;
  number: string;
  name: string;
  tag: string;
  description: string;
  incident: string;
  symptom: string;
};
export type Source = {
  id: string;
  title?: string;
  name?: string;
  text?: string;
  effective_at?: string;
  ingested_at?: string;
  active?: boolean;
  [key: string]: unknown;
};
export type GraphNode = { id: string; label: string; data: Source };
export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  kind: string;
  evidence_ids: string[];
};
export type GraphData = { nodes: GraphNode[]; edges: GraphEdge[] };
export type Probe = {
  service: string;
  healthy: boolean;
  detail: string;
  status_code: number;
};
export type ActionResult = {
  verified: boolean;
  before: Probe[];
  after: Probe[];
  executed_at: string;
};
export type Proposal = {
  id: string;
  action: string;
  target: string;
  summary: string;
  evidence_ids: string[];
  revision: number;
  stale: boolean;
  blocked_reason: string | null;
  result: ActionResult | null;
};
export type RunEvent = {
  id: number;
  kind: string;
  title: string;
  detail: string;
  evidence_ids: string[];
  at: string;
  paths?: { nodes: string[]; edges: string[] }[];
};
export type Run = {
  id: string;
  status: string;
  incident: string;
  mode: string;
  model?: string;
  model_provider?: string;
  tool_protocol?: string;
  revalidates_run_id?: string;
  previous_recommendation?: {action:string;target:string;revision:number};
  created_at: string;
  events: RunEvent[];
  proposals: Proposal[];
  model_calls: number;
  elapsed_ms: number;
  error: string | null;
  cursor?: number;
  current_revision?: number;
  graph_snapshot?: GraphData;
  diagnosis: {
    summary: string;
    affected_services: string[];
    missing_evidence: string[];
    evidence_ids: string[];
  } | null;
  replay: boolean;
};
export type Replay = Run & {
  evaluation_case?: string;
  evaluation_name?: string;
  label?: string;
  graph: GraphData;
  scenario: Scenario;
};
export type Memory = {
  id: string;
  incident: string;
  action: string;
  target: string;
  verified: boolean;
  summary: string;
  applicability: string;
  result: ActionResult;
  created_at: string;
};
export type Health = {
  model_provider?: string;
  database: string;
  model: string;
  model_configured: boolean;
  limits: { workspace_daily: number; global_daily: number };
};
export type Workspace = {
  scenario: Scenario | null;
  revision: number;
  history: {
    id: string;
    incident: string;
    status: string;
    mode: string;
    created_at: string;
  }[];
  memory_count: number;
};
export type EvaluationRow = {
  case: string;
  name: string;
  mode: string;
  status: string;
  verified: boolean;
  expected_met: boolean;
  valid_citations: boolean;
  model_calls: number;
  elapsed_ms: number;
  invalid_proposals: number;
  executed_violations: number;
  correct_impact: boolean;
};
export type Evaluations = {
  measured: boolean;
  model?: string;
  model_provider?: string;
  tool_protocol?: string;
  limitations?: string;
  complete?: boolean;
  expected_runs?: number;
  cases: EvaluationRow[];
  message?: string;
  created_at?: string;
  summary: {
    runs: number;
    expected_met: number;
    verified_recoveries: number;
  } | null;
};
