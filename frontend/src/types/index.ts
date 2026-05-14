export interface Tool {
  id: string;
  name: string;
  tool_type: "builtin" | "custom";
  description: string;
  config: Record<string, unknown> | null;
  created_at: string;
}

export interface SubAgent {
  id: string;
  deep_agent_id: string;
  name: string;
  description: string;
  system_prompt: string;
  model: string | null;
  tools: Tool[];
  created_at: string;
  updated_at: string;
}

export interface AgentSummary {
  id: string;
  name: string;
  description: string;
  system_prompt: string;
  model: string;
  temperature: number;
  created_at: string;
  updated_at: string;
  subagent_count: number;
}

export interface AgentDetail extends Omit<AgentSummary, "subagent_count"> {
  subagents: SubAgent[];
  tools: Tool[];
}

export interface AgentCreate {
  name: string;
  description?: string;
  system_prompt?: string;
  model?: string;
  temperature?: number;
  tool_ids?: string[];
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  system_prompt?: string;
  model?: string;
  temperature?: number;
  tool_ids?: string[];
}

export interface SubAgentCreate {
  name: string;
  description?: string;
  system_prompt?: string;
  model?: string | null;
  tool_ids?: string[];
}

export interface SubAgentUpdate {
  name?: string;
  description?: string;
  system_prompt?: string;
  model?: string | null;
  tool_ids?: string[];
}

export interface RunSummary {
  id: string;
  agent_id: string;
  input: string;
  output: string;
  status: "running" | "completed" | "failed";
  created_at: string;
  completed_at: string | null;
}

export interface Settings {
  openai_api_key_set: boolean;
  openai_base_url: string;
  deepagent_model: string;
  langchain_api_key_set: boolean;
  langchain_tracing_v2: boolean;
}

export interface SettingsUpdate {
  openai_api_key?: string;
  openai_base_url?: string;
  deepagent_model?: string;
  langchain_api_key?: string;
  langchain_tracing_v2?: boolean;
}
