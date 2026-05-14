import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, Plus, Trash2, Cpu } from "lucide-react";
import { useState } from "react";
import { createSubAgent, deleteSubAgent, updateSubAgent } from "../../api/client";
import type { AgentDetail, SubAgent } from "../../types";
import PromptEditor from "../PromptEditor";
import ToolPicker from "../ToolPicker";

interface SubagentFormData {
  name: string;
  description: string;
  system_prompt: string;
  model: string;
  tool_ids: string[];
}

function SubagentCard({
  sa,
  agentId,
  onDeleted,
}: {
  sa: SubAgent;
  agentId: string;
  onDeleted: () => void;
}) {
  const qc = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const [form, setForm] = useState<SubagentFormData>({
    name: sa.name,
    description: sa.description,
    system_prompt: sa.system_prompt,
    model: sa.model ?? "",
    tool_ids: sa.tools.map((t) => t.id),
  });

  const updateMutation = useMutation({
    mutationFn: () =>
      updateSubAgent(sa.id, {
        ...form,
        model: form.model || null,
        tool_ids: form.tool_ids,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agent", agentId] }),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteSubAgent(sa.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["agent", agentId] });
      onDeleted();
    },
  });

  return (
    <div className="border border-warm-200 rounded-xl overflow-hidden bg-white shadow-sm">
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-warm-50 transition-colors group"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="w-7 h-7 rounded-lg bg-brand-500/10 flex items-center justify-center shrink-0">
          <Cpu className="w-3.5 h-3.5 text-brand-500" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-warm-900 truncate">{sa.name}</p>
          {sa.model && <p className="text-xs text-warm-400 font-mono">{sa.model}</p>}
        </div>
        {expanded
          ? <ChevronDown className="w-4 h-4 text-warm-400" />
          : <ChevronRight className="w-4 h-4 text-warm-400" />}
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (confirm(`Delete sub-agent "${sa.name}"?`)) deleteMutation.mutate();
          }}
          className="p-1.5 rounded-lg text-warm-300 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {expanded && (
        <div className="border-t border-warm-200 p-4 space-y-4 bg-warm-50">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Name</label>
              <input
                className="input"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">Model Override</label>
              <input
                className="input font-mono text-sm"
                value={form.model}
                onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))}
                placeholder="Inherit from parent"
              />
            </div>
          </div>

          <div>
            <label className="label">Description</label>
            <input
              className="input"
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              placeholder="What this sub-agent does (shown to the supervisor)"
            />
          </div>

          <div>
            <label className="label">System Prompt</label>
            <PromptEditor
              value={form.system_prompt}
              onChange={(v) => setForm((f) => ({ ...f, system_prompt: v }))}
              height="200px"
            />
          </div>

          <div>
            <label className="label mb-2">Tools</label>
            <ToolPicker
              selectedToolIds={form.tool_ids}
              onChange={(ids) => setForm((f) => ({ ...f, tool_ids: ids }))}
            />
          </div>

          <button
            className="btn-primary"
            onClick={() => updateMutation.mutate()}
            disabled={updateMutation.isPending}
          >
            Save Sub-agent
          </button>
        </div>
      )}
    </div>
  );
}

export default function SubagentPanel({ agent }: { agent: AgentDetail }) {
  const qc = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [newForm, setNewForm] = useState<SubagentFormData>({
    name: "",
    description: "",
    system_prompt: "",
    model: "",
    tool_ids: [],
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createSubAgent(agent.id, {
        ...newForm,
        model: newForm.model || null,
        tool_ids: newForm.tool_ids,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["agent", agent.id] });
      setShowAdd(false);
      setNewForm({ name: "", description: "", system_prompt: "", model: "", tool_ids: [] });
    },
  });

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-400">
          {agent.subagents.length} sub-agent{agent.subagents.length !== 1 ? "s" : ""} — the supervisor delegates tasks to these agents via the <code className="text-brand-400 text-xs">task</code> tool.
        </p>
        <button className="btn-secondary text-xs" onClick={() => setShowAdd(true)}>
          <Plus className="w-3.5 h-3.5" /> Add Sub-agent
        </button>
      </div>

      {showAdd && (
        <div className="card space-y-4 border-brand-500/30">
          <h3 className="text-sm font-medium text-white">New Sub-agent</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Name</label>
              <input
                className="input"
                value={newForm.name}
                onChange={(e) => setNewForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="researcher"
              />
            </div>
            <div>
              <label className="label">Model Override</label>
              <input
                className="input"
                value={newForm.model}
                onChange={(e) => setNewForm((f) => ({ ...f, model: e.target.value }))}
                placeholder="Inherit from parent"
              />
            </div>
          </div>
          <div>
            <label className="label">Description</label>
            <input
              className="input"
              value={newForm.description}
              onChange={(e) => setNewForm((f) => ({ ...f, description: e.target.value }))}
              placeholder="Investigates topics and summarises findings"
            />
          </div>
          <div>
            <label className="label">System Prompt</label>
            <PromptEditor
              value={newForm.system_prompt}
              onChange={(v) => setNewForm((f) => ({ ...f, system_prompt: v }))}
              height="180px"
            />
          </div>
          <div>
            <label className="label mb-2">Tools</label>
            <ToolPicker
              selectedToolIds={newForm.tool_ids}
              onChange={(ids) => setNewForm((f) => ({ ...f, tool_ids: ids }))}
            />
          </div>
          <div className="flex gap-2">
            <button
              className="btn-primary"
              onClick={() => createMutation.mutate()}
              disabled={!newForm.name || createMutation.isPending}
            >
              Create Sub-agent
            </button>
            <button className="btn-secondary" onClick={() => setShowAdd(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {agent.subagents.map((sa) => (
        <SubagentCard key={sa.id} sa={sa} agentId={agent.id} onDeleted={() => {}} />
      ))}

      {agent.subagents.length === 0 && !showAdd && (
        <div className="text-center py-10 text-gray-600 text-sm">
          No sub-agents yet. The default general-purpose sub-agent will be used automatically.
        </div>
      )}
    </div>
  );
}
