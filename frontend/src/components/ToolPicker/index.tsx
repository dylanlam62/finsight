import { useQuery } from "@tanstack/react-query";
import { Shield, Zap } from "lucide-react";
import { listTools } from "../../api/client";
import type { Tool } from "../../types";

interface Props {
  selectedToolIds: string[];
  onChange: (ids: string[]) => void;
}

function ToolRow({ tool, checked, onToggle }: { tool: Tool; checked: boolean; onToggle: () => void }) {
  return (
    <label className="flex items-start gap-3 p-3 rounded-lg border border-gray-800 hover:border-gray-700 cursor-pointer transition-colors">
      <input
        type="checkbox"
        checked={checked}
        onChange={onToggle}
        className="mt-0.5 w-4 h-4 accent-brand-500"
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <code className="text-xs font-mono text-brand-400">{tool.name}</code>
          {tool.tool_type === "builtin" ? (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 flex items-center gap-1">
              <Shield className="w-2.5 h-2.5" /> built-in
            </span>
          ) : (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-400 flex items-center gap-1">
              <Zap className="w-2.5 h-2.5" /> custom
            </span>
          )}
        </div>
        {tool.description && <p className="text-xs text-gray-500 mt-0.5">{tool.description}</p>}
      </div>
    </label>
  );
}

export default function ToolPicker({ selectedToolIds, onChange }: Props) {
  const { data: tools = [] } = useQuery({ queryKey: ["tools"], queryFn: listTools });

  const builtins = tools.filter((t) => t.tool_type === "builtin");
  const custom = tools.filter((t) => t.tool_type === "custom");

  const toggle = (id: string) => {
    onChange(selectedToolIds.includes(id) ? selectedToolIds.filter((x) => x !== id) : [...selectedToolIds, id]);
  };

  return (
    <div className="space-y-4">
      <div>
        <p className="label mb-2">Built-in Tools</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {builtins.map((t) => (
            <ToolRow key={t.id} tool={t} checked={selectedToolIds.includes(t.id)} onToggle={() => toggle(t.id)} />
          ))}
        </div>
      </div>
      {custom.length > 0 && (
        <div>
          <p className="label mb-2">Custom Tools</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {custom.map((t) => (
              <ToolRow key={t.id} tool={t} checked={selectedToolIds.includes(t.id)} onToggle={() => toggle(t.id)} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
