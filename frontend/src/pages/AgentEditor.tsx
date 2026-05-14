import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Play, Save } from "lucide-react";
import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getAgent, updateAgent } from "../api/client";
import GraphViewer from "../components/GraphViewer";
import ModelSelector from "../components/ModelSelector";
import PromptEditor from "../components/PromptEditor";
import SubagentPanel from "../components/SubagentPanel";
import ToolPicker from "../components/ToolPicker";

type Tab = "overview" | "prompt" | "subagents" | "tools" | "graph" | "history";

const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "prompt", label: "System Prompt" },
  { id: "subagents", label: "Sub-Agents" },
  { id: "tools", label: "Tools" },
  { id: "graph", label: "Graph" },
  { id: "history", label: "Run History" },
];

export default function AgentEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: agent, isLoading } = useQuery({
    queryKey: ["agent", id],
    queryFn: () => getAgent(id!),
    enabled: !!id,
  });

  const [tab, setTab] = useState<Tab>("overview");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [model, setModel] = useState("openai:gpt-4o");
  const [temperature, setTemperature] = useState(0);
  const [systemPrompt, setSystemPrompt] = useState("");
  const [toolIds, setToolIds] = useState<string[]>([]);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (agent) {
      setName(agent.name);
      setDescription(agent.description);
      setModel(agent.model);
      setTemperature(agent.temperature);
      setSystemPrompt(agent.system_prompt);
      setToolIds(agent.tools.map((t) => t.id));
    }
  }, [agent]);

  const updateMutation = useMutation({
    mutationFn: () =>
      updateAgent(id!, {
        name,
        description,
        model,
        temperature,
        system_prompt: systemPrompt,
        tool_ids: toolIds,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["agent", id] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  if (isLoading) {
    return <div className="p-8 text-warm-400">Loading…</div>;
  }

  if (!agent) {
    return <div className="p-8 text-red-500">Agent not found.</div>;
  }

  return (
    <div className="flex flex-col h-full bg-warm-50">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-warm-200 bg-white shadow-sm">
        <button
          className="p-1.5 rounded-lg text-warm-400 hover:text-warm-800 hover:bg-warm-100 transition-colors"
          onClick={() => navigate("/")}
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="flex-1 min-w-0">
          <input
            className="bg-transparent text-base font-semibold text-warm-900 focus:outline-none w-full truncate placeholder-warm-300"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Agent name"
          />
        </div>
        <div className="flex gap-2">
          <button
            className="btn-secondary"
            onClick={() => navigate(`/agents/${id}/run`)}
          >
            <Play className="w-4 h-4" /> Run
          </button>
          <button
            className="btn-primary"
            onClick={() => updateMutation.mutate()}
            disabled={updateMutation.isPending}
          >
            <Save className="w-4 h-4" />
            {saved ? "Saved!" : "Save"}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-0 px-6 border-b border-warm-200 bg-white overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={tab === t.id ? "tab-active" : "tab-inactive"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {tab === "overview" && (
          <div className="max-w-xl space-y-5">
            <div>
              <label className="label">Description</label>
              <textarea
                className="input resize-none"
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What does this agent do?"
              />
            </div>
            <ModelSelector
              model={model}
              temperature={temperature}
              onModelChange={setModel}
              onTemperatureChange={setTemperature}
            />
          </div>
        )}

        {tab === "prompt" && (
          <div className="space-y-3">
            <p className="text-sm text-warm-500">
              This prompt is placed <strong className="text-warm-700 font-medium">before</strong> the deepagents default prompt. Leave blank to use only the default.
            </p>
            <PromptEditor
              value={systemPrompt}
              onChange={setSystemPrompt}
              height="calc(100vh - 280px)"
            />
          </div>
        )}

        {tab === "subagents" && <SubagentPanel agent={agent} />}

        {tab === "tools" && (
          <div className="space-y-3">
            <p className="text-sm text-warm-500">
              Select which built-in tools this agent can use. Deselected built-ins will be excluded via <code className="text-brand-500 text-xs bg-brand-50 px-1.5 py-0.5 rounded">HarnessProfile.excluded_tools</code>.
            </p>
            <ToolPicker selectedToolIds={toolIds} onChange={setToolIds} />
          </div>
        )}

        {tab === "graph" && <GraphViewer agent={agent} />}

        {tab === "history" && <RunHistory agentId={id!} />}
      </div>
    </div>
  );
}

function RunHistory({ agentId }: { agentId: string }) {
  const { data: runs = [] } = useQuery({
    queryKey: ["runs", agentId],
    queryFn: () => import("../api/client").then((m) => m.listAgentRuns(agentId)),
  });

  if (runs.length === 0) {
    return <p className="text-sm text-warm-400 text-center py-10">No runs yet.</p>;
  }

  return (
    <div className="space-y-2">
      {runs.map((run: any) => (
        <div key={run.id} className="card flex items-start gap-3">
          <div
            className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${
              run.status === "completed"
                ? "bg-green-400"
                : run.status === "failed"
                ? "bg-red-400"
                : "bg-amber-400 animate-pulse"
            }`}
          />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-warm-800 truncate">{run.input}</p>
            {run.output && (
              <p className="text-xs text-warm-400 mt-0.5 truncate">{run.output.slice(0, 120)}</p>
            )}
          </div>
          <span className="text-xs text-warm-400 shrink-0">
            {new Date(run.created_at).toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  );
}
