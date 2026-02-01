export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  date_joined: string;
}

export interface APIConfig {
  openai_base_url: string;
  openai_model: string;
  openai_eval_model: string;
  openai_api_key?: string;
  tavily_api_key?: string;
  has_openai_key: boolean;
  has_tavily_key: boolean;
  updated_at: string;
}

export interface PostTemplate {
  id: string;
  name: string;
  description: string;
  tone: string;
  category: string;
  structure_prompt: string;
  example_post: string;
  is_system: boolean;
  created_at: string;
}

export interface PostProject {
  id: string;
  title: string;
  topic: string;
  status: ProjectStatus;
  template?: string;
  tone: string;
  target_audience: string;
  target_word_count_min: number;
  target_word_count_max: number;
  include_hashtags: boolean;
  include_cta: boolean;
  include_emoji: boolean;
  language: string;
  final_post: string;
  groundedness_score: number | null;
  groundedness_report: GroundednessReport | null;
  is_favorite: boolean;
  tags: string[];
  scheduled_at: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
  draft_count?: number;
  latest_draft_preview?: string;
  runs?: AgentRun[];
  drafts?: PostDraft[];
  findings?: ResearchFinding[];
}

export type ProjectStatus = 'draft' | 'researching' | 'writing' | 'reviewing' | 'approved' | 'published' | 'failed';

export interface AgentRun {
  id: string;
  project: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  total_revisions: number;
  error_message: string;
  steps: AgentStep[];
  findings: ResearchFinding[];
  drafts: PostDraft[];
}

export interface AgentStep {
  id: string;
  run: string;
  agent_name: 'supervisor' | 'researcher' | 'writer' | 'critic' | 'evaluator';
  step_number: number;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  decision: string;
  duration_ms: number | null;
  tokens_used: number | null;
  created_at: string;
}

export interface ResearchFinding {
  id: string;
  project: string;
  query: string;
  summary: string;
  sources: Array<{ title: string; url: string }>;
  created_at: string;
}

export interface PostDraft {
  id: string;
  project: string;
  version: number;
  content: string;
  word_count: number;
  critique_notes: string;
  is_approved: boolean;
  created_at: string;
}

export interface GroundednessReport {
  supported: string[];
  unsupported: string[];
  score: number;
  notes: string;
}

export interface PostAnalytics {
  id: string;
  project: string;
  impressions: number;
  likes: number;
  comments: number;
  shares: number;
  clicks: number;
  engagement_rate: number;
  recorded_at: string;
}

export interface CalendarEntry {
  id: string;
  project: string | null;
  title: string;
  description: string;
  scheduled_date: string;
  scheduled_time: string | null;
  recurrence: string;
  is_completed: boolean;
  color: string;
  project_title?: string;
}

export interface DashboardStats {
  total_projects: number;
  published_posts: number;
  avg_groundedness: number | null;
  total_revisions: number;
  posts_this_week: number;
  posts_this_month: number;
  top_tones: Array<{ tone: string; count: number }>;
  recent_projects: PostProject[];
}

export interface AgentEvent {
  type: string;
  channel?: string;
  data?: {
    type: string;
    run_id: string;
    project_id: string;
    step?: number;
    agent?: string;
    decision?: string;
    task?: string;
    duration_ms?: number;
    findings_preview?: string;
    draft_preview?: string;
    revision?: number;
    word_count?: number;
    approved?: boolean;
    feedback_preview?: string;
    final_post?: string;
    groundedness_score?: number;
    error?: string;
    status?: string;
  };
  timestamp?: number;
}
