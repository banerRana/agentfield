/**
 * TypeScript interfaces for dashboard API responses
 */

export interface DashboardSummary {
  agents: {
    running: number;
    total: number;
  };
  executions: {
    today: number;
    yesterday: number;
  };
  success_rate: number;
  packages: {
    available: number;
    installed: number;
  };
}

export interface DashboardError {
  message: string;
  code?: string;
  details?: any;
}

export interface DashboardState {
  data: DashboardSummary | null;
  loading: boolean;
  error: DashboardError | null;
  lastFetch: Date | null;
  isStale: boolean;
}

export interface EnhancedDashboardResponse {
  generated_at: string;
  overview: EnhancedDashboardOverview;
  execution_trends: ExecutionTrendSummary;
  agent_health: AgentHealthSummary;
  workflows: EnhancedWorkflowInsights;
  incidents: IncidentItem[];
}

export interface EnhancedDashboardOverview {
  total_agents: number;
  active_agents: number;
  degraded_agents: number;
  offline_agents: number;
  total_reasoners: number;
  total_skills: number;
  executions_last_24h: number;
  executions_last_7d: number;
  success_rate_24h: number;
  average_duration_ms_24h: number;
  median_duration_ms_24h: number;
}

export interface ExecutionTrendSummary {
  last_24h: ExecutionWindowMetrics;
  last_7_days: ExecutionTrendPoint[];
}

export interface ExecutionWindowMetrics {
  total: number;
  succeeded: number;
  failed: number;
  success_rate: number;
  average_duration_ms: number;
  throughput_per_hour: number;
}

export interface ExecutionTrendPoint {
  date: string;
  total: number;
  succeeded: number;
  failed: number;
}

export interface AgentHealthSummary {
  total: number;
  active: number;
  degraded: number;
  offline: number;
  agents: AgentHealthItem[];
}

export interface AgentHealthItem {
  id: string;
  team_id: string;
  version: string;
  status: string;
  health: string;
  lifecycle: string;
  last_heartbeat: string;
  reasoners: number;
  skills: number;
  uptime?: string;
}

export interface EnhancedWorkflowInsights {
  top_workflows: WorkflowStat[];
  active_runs: ActiveWorkflowRun[];
  longest_executions: CompletedExecutionStat[];
}

export interface WorkflowStat {
  workflow_id: string;
  name?: string;
  total_executions: number;
  success_rate: number;
  failed_executions: number;
  average_duration_ms: number;
  last_activity: string;
}

export interface ActiveWorkflowRun {
  execution_id: string;
  workflow_id: string;
  name?: string;
  started_at: string;
  elapsed_ms: number;
  agent_node_id: string;
  reasoner_id: string;
  status: string;
}

export interface CompletedExecutionStat {
  execution_id: string;
  workflow_id: string;
  name?: string;
  duration_ms: number;
  completed_at?: string;
  status: string;
}

export interface IncidentItem {
  execution_id: string;
  workflow_id: string;
  name?: string;
  status: string;
  started_at: string;
  completed_at?: string;
  agent_node_id: string;
  reasoner_id: string;
  error?: string;
}
