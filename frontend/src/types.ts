export type Origin = "extracted" | "inferred";

export interface Project {
  id: string;
  name: string;
  description: string;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface Finding {
  id: string;
  statement: string;
  origin: Origin;
  evidence: string | null;
  rationale: string | null;
}

export interface AnalysisPayload {
  summary: {
    input_kind: string;
    character_count: number;
    detector: string;
    llm_used: boolean;
    note: string;
  };
  functional_requirements: Finding[];
  business_rules: Finding[];
  actors: Finding[];
  preconditions: Finding[];
  expected_outcomes: Finding[];
  constraints: Finding[];
  missing_information: Finding[];
  ambiguities: Finding[];
  dependencies: Finding[];
  acceptance_criteria: Finding[];
}

export interface AnalysisRecord {
  id: string;
  project_id: string;
  source_id: string;
  payload: AnalysisPayload;
  created_at: string;
}

export interface TestCase {
  id: string;
  project_id: string;
  suite_id: string | null;
  source_id: string | null;
  case_key: string;
  title: string;
  description: string;
  requirement_ref: string;
  preconditions: string[];
  steps: string[];
  test_data: Record<string, string>;
  expected_result: string;
  test_type: string;
  priority: string;
  risk_level: string;
  automation_suitability: string;
  tags: string[];
  generation_metadata: {
    provider?: string;
    model?: string;
    deterministic?: boolean;
    scenario_origin?: Origin;
    token_usage?: { source?: string; note?: string; prompt_tokens?: number; completion_tokens?: number };
    produced_by_external_model?: boolean;
    latency_ms?: number;
    recovered_from_invalid_output?: boolean;
  };
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Suite {
  id: string;
  project_id: string;
  name: string;
  description: string;
  case_count: number;
  created_at: string;
}

export interface Coverage {
  basis: string;
  total_acceptance_criteria: number;
  covered: number;
  coverage_percent: number | null;
  items: { id: string; statement: string; covered: boolean; cases: { case_key: string; title: string }[] }[];
  uncovered: { id: string; statement: string }[];
  note: string | null;
  llm_used: boolean;
}

export interface Summary {
  project: Project;
  counts: { test_cases: number; suites: number; sources: number; analyses: number };
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
  by_risk: Record<string, number>;
  coverage: Coverage;
  latest_run: {
    provider: string;
    model: string;
    status: string;
    stats: { case_count?: number; deterministic?: boolean };
    created_at: string;
  } | null;
}

export interface SettingsPayload {
  provider: "mock" | "openai" | "anthropic";
  model: string;
  active_model: string;
  temperature: number;
  max_tokens: number;
  temperature_applied_to_mock: boolean;
  providers: { id: string; configured: boolean; description: string }[];
}

export interface ExampleItem {
  title: string;
  kind: "user_story" | "requirements_document";
  content: string;
  note: string;
}

export const TEST_TYPES = [
  "functional",
  "positive",
  "negative",
  "boundary",
  "edge",
  "error_handling",
  "security",
  "api",
  "ui",
] as const;
