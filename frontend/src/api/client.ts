import axios from "axios";
import type {
  AgentCreate,
  AgentDetail,
  AgentSummary,
  AgentUpdate,
  RunSummary,
  Settings,
  SettingsUpdate,
  SubAgent,
  SubAgentCreate,
  SubAgentUpdate,
  Tool,
} from "../types";

const http = axios.create({ baseURL: "/api" });

// ── Agents ────────────────────────────────────────────────────────────────────

export const listAgents = (): Promise<AgentSummary[]> =>
  http.get("/agents").then((r) => r.data);

export const getAgent = (id: string): Promise<AgentDetail> =>
  http.get(`/agents/${id}`).then((r) => r.data);

export const createAgent = (body: AgentCreate): Promise<AgentDetail> =>
  http.post("/agents", body).then((r) => r.data);

export const updateAgent = (id: string, body: AgentUpdate): Promise<AgentDetail> =>
  http.put(`/agents/${id}`, body).then((r) => r.data);

export const deleteAgent = (id: string): Promise<void> =>
  http.delete(`/agents/${id}`).then(() => undefined);

export const listAgentRuns = (agentId: string): Promise<RunSummary[]> =>
  http.get(`/agents/${agentId}/runs`).then((r) => r.data);

export const resumeRun = (runId: string, answer: string): Promise<Response> =>
  fetch(`/api/runs/${runId}/resume`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer }),
  });

// ── Sub-agents ────────────────────────────────────────────────────────────────

export const createSubAgent = (agentId: string, body: SubAgentCreate): Promise<SubAgent> =>
  http.post(`/agents/${agentId}/subagents`, body).then((r) => r.data);

export const updateSubAgent = (id: string, body: SubAgentUpdate): Promise<SubAgent> =>
  http.put(`/subagents/${id}`, body).then((r) => r.data);

export const deleteSubAgent = (id: string): Promise<void> =>
  http.delete(`/subagents/${id}`).then(() => undefined);

// ── Tools ─────────────────────────────────────────────────────────────────────

export const listTools = (): Promise<Tool[]> =>
  http.get("/tools").then((r) => r.data);

export const createTool = (body: Partial<Tool>): Promise<Tool> =>
  http.post("/tools", body).then((r) => r.data);

export const updateTool = (id: string, body: Partial<Tool>): Promise<Tool> =>
  http.put(`/tools/${id}`, body).then((r) => r.data);

export const deleteTool = (id: string): Promise<void> =>
  http.delete(`/tools/${id}`).then(() => undefined);

// ── Settings ──────────────────────────────────────────────────────────────────

export const getSettings = (): Promise<Settings> =>
  http.get("/settings").then((r) => r.data);

export const updateSettings = (body: SettingsUpdate): Promise<Settings> =>
  http.put("/settings", body).then((r) => r.data);
