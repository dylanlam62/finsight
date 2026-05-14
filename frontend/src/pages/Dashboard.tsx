import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, Plus, Play, Trash2, Clock, Cpu } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { createAgent, deleteAgent, listAgents } from "../api/client";
import type { AgentSummary } from "../types";

function AgentCard({ agent, onDelete }: { agent: AgentSummary; onDelete: () => void }) {
  const navigate = useNavigate();

  return (
    <div className="card flex flex-col gap-3 hover:border-warm-300 hover:shadow-md transition-all duration-200 group cursor-default">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-brand-500/10 flex items-center justify-center shrink-0">
            <Bot className="w-4.5 h-4.5 text-brand-500" />
          </div>
          <div>
            <h3 className="font-semibold text-sm text-warm-900">{agent.name}</h3>
            <p className="text-xs text-warm-400 font-mono mt-0.5">{agent.model}</p>
          </div>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          className="p-1.5 rounded-lg text-warm-300 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {agent.description && (
        <p className="text-xs text-warm-500 line-clamp-2 leading-relaxed">{agent.description}</p>
      )}

      <div className="flex items-center gap-3 text-xs text-warm-400">
        <span className="flex items-center gap-1.5">
          <Cpu className="w-3 h-3" /> {agent.subagent_count} sub-agent{agent.subagent_count !== 1 ? "s" : ""}
        </span>
        <span className="flex items-center gap-1.5">
          <Clock className="w-3 h-3" />
          {new Date(agent.created_at).toLocaleDateString()}
        </span>
      </div>

      <div className="flex gap-2 pt-1 border-t border-warm-100">
        <button
          className="btn-secondary flex-1 justify-center text-xs py-1.5"
          onClick={() => navigate(`/agents/${agent.id}`)}
        >
          Configure
        </button>
        <button
          className="btn-primary px-3 py-1.5"
          onClick={() => navigate(`/agents/${agent.id}/run`)}
        >
          <Play className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: agents = [], isLoading } = useQuery({
    queryKey: ["agents"],
    queryFn: listAgents,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createAgent({ name: "New Agent", model: "openai:gpt-4o", temperature: 0.0 }),
    onSuccess: (agent) => {
      qc.invalidateQueries({ queryKey: ["agents"] });
      navigate(`/agents/${agent.id}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAgent,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agents"] }),
  });

  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-warm-900">Deep Agents</h1>
          <p className="text-sm text-warm-500 mt-1">Create and manage LangGraph deep agents</p>
        </div>
        <button
          className="btn-primary"
          onClick={() => createMutation.mutate()}
          disabled={createMutation.isPending}
        >
          <Plus className="w-4 h-4" /> New Agent
        </button>
      </div>

      {isLoading ? (
        <div className="text-center text-warm-400 py-20">Loading agents…</div>
      ) : agents.length === 0 ? (
        <div className="text-center py-24">
          <div className="w-16 h-16 rounded-2xl bg-brand-500/10 flex items-center justify-center mx-auto mb-4">
            <Bot className="w-8 h-8 text-brand-500" />
          </div>
          <p className="text-warm-700 font-medium">No agents yet</p>
          <p className="text-warm-400 text-sm mt-1">Create your first deep agent to get started</p>
          <button className="btn-primary mt-5" onClick={() => createMutation.mutate()}>
            <Plus className="w-4 h-4" /> Create Agent
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {agents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onDelete={() => {
                if (confirm(`Delete agent "${agent.name}"?`)) deleteMutation.mutate(agent.id);
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
