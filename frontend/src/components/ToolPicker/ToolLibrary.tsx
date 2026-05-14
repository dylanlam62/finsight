import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Shield, Zap } from "lucide-react";
import { useState } from "react";
import { createTool, deleteTool, listTools } from "../../api/client";

export default function ToolLibrary() {
  const qc = useQueryClient();
  const { data: tools = [] } = useQuery({ queryKey: ["tools"], queryFn: listTools });
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [url, setUrl] = useState("");
  const [method, setMethod] = useState("POST");

  const deleteMutation = useMutation({
    mutationFn: deleteTool,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tools"] }),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createTool({
        name,
        tool_type: "custom",
        description,
        config: { type: "http", url, method },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tools"] });
      setShowForm(false);
      setName(""); setDescription(""); setUrl(""); setMethod("POST");
    },
  });

  const builtins = tools.filter((t) => t.tool_type === "builtin");
  const custom = tools.filter((t) => t.tool_type === "custom");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
          <Shield className="w-4 h-4 text-gray-500" /> Built-in Tools
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {builtins.map((t) => (
            <div key={t.id} className="card flex items-start gap-2">
              <div className="flex-1">
                <code className="text-xs font-mono text-brand-400">{t.name}</code>
                <p className="text-xs text-gray-500 mt-0.5">{t.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
            <Zap className="w-4 h-4 text-brand-400" /> Custom Tools
          </h2>
          <button className="btn-secondary text-xs" onClick={() => setShowForm(true)}>
            <Plus className="w-3.5 h-3.5" /> Add Custom Tool
          </button>
        </div>

        {showForm && (
          <div className="card mb-4 space-y-3">
            <h3 className="text-sm font-medium">New HTTP Tool</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Tool Name</label>
                <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="my_tool" />
              </div>
              <div>
                <label className="label">HTTP Method</label>
                <select className="input" value={method} onChange={(e) => setMethod(e.target.value)}>
                  <option>POST</option>
                  <option>GET</option>
                </select>
              </div>
            </div>
            <div>
              <label className="label">Endpoint URL</label>
              <input className="input" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://..." />
            </div>
            <div>
              <label className="label">Description</label>
              <input className="input" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What does this tool do?" />
            </div>
            <div className="flex gap-2">
              <button className="btn-primary" onClick={() => createMutation.mutate()} disabled={!name || !url || createMutation.isPending}>
                Create Tool
              </button>
              <button className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </div>
        )}

        {custom.length === 0 && !showForm ? (
          <p className="text-sm text-gray-500">No custom tools yet.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {custom.map((t) => (
              <div key={t.id} className="card flex items-start gap-2">
                <div className="flex-1">
                  <code className="text-xs font-mono text-brand-400">{t.name}</code>
                  <p className="text-xs text-gray-500 mt-0.5">{t.description}</p>
                  {t.config && (
                    <p className="text-xs text-gray-600 mt-0.5">
                      {(t.config as any).method} {(t.config as any).url}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => deleteMutation.mutate(t.id)}
                  className="p-1 rounded text-gray-600 hover:text-red-400 transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
