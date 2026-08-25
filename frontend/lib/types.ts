export type ProjectType = 'website' | 'application' | 'unclassified';

export type TaskType = 
  | 'ui_scaffold' 
  | 'copy_generation' 
  | 'business_logic' 
  | 'data_models' 
  | 'security_review';

export type TierType = 'fast' | 'reasoning' | 'critic';

export interface Project {
  id: string;
  owner_id: string;
  title: string;
  prompt: string;
  project_type: ProjectType;
  status: 'generating' | 'ready' | 'failed' | 'awaiting_confirmation';
  created_at: string;
  updated_at: string;
}

export interface ProjectFile {
  id: string;
  project_id: string;
  path: string;
  content: string;
  generated_by_model: string;
  created_at: string;
}

export interface RoutingLog {
  id: string;
  project_id: string;
  task_type: TaskType;
  model_used: string;
  latency_ms: number;
  cost_usd: number;
  created_at: string;
}

export interface RoutingSegment {
  taskType: TaskType;
  modelUsed: string;
  tier: TierType;
  routingReason: string;
  status: 'pending' | 'running' | 'done' | 'flagged' | 'failed';
  latencyMs?: number;
  costUsd?: number;
  filePath?: string;
  criticPassed?: boolean;
}

export interface GateResult {
  gate_name: string;
  passed: boolean;
  details: string;
  score?: number;
  metric_data?: Record<string, any>;
}

export interface DeployResult {
  success: boolean;
  url?: string;
  deploy_id?: string;
  error?: string;
  deployment_type: string;
}

export interface RoutingEvent {
  event_type: 
    | 'classification_done' 
    | 'subtask_started' 
    | 'subtask_done' 
    | 'critic_started' 
    | 'critic_done' 
    | 'quality_gate_done' 
    | 'generation_complete' 
    | 'error' 
    | 'connected';
  project_type?: ProjectType;
  task_type?: TaskType;
  model_used?: string;
  tier?: TierType;
  routing_reason?: string;
  latency_ms?: number;
  cost_usd?: number;
  file_path?: string;
  progress_pct?: number;
  gate_name?: string;
  passed?: boolean;
  details?: string;
  score?: number;
  error_message?: string;
  timestamp: number;
}
