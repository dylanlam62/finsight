import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle, Eye, EyeOff, Save, Globe } from "lucide-react";
import { useState, useEffect } from "react";
import { getSettings, updateSettings } from "../api/client";

export default function SettingsPage() {
  const qc = useQueryClient();
  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: getSettings });

  const [openaiKey, setOpenaiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [deepagentModel, setDeepagentModel] = useState("gpt-4o");
  const [langchainKey, setLangchainKey] = useState("");
  const [tracing, setTracing] = useState(false);
  const [showOpenai, setShowOpenai] = useState(false);
  const [showLangchain, setShowLangchain] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (settings) {
      setBaseUrl(settings.openai_base_url ?? "");
      setDeepagentModel(settings.deepagent_model ?? "gpt-4o");
      setTracing(settings.langchain_tracing_v2 ?? false);
    }
  }, [settings]);

  const mutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["settings"] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      setOpenaiKey("");
      setLangchainKey("");
    },
  });

  const handleSave = () => {
    mutation.mutate({
      ...(openaiKey ? { openai_api_key: openaiKey } : {}),
      openai_base_url: baseUrl,
      deepagent_model: deepagentModel,
      ...(langchainKey ? { langchain_api_key: langchainKey } : {}),
      langchain_tracing_v2: tracing,
    });
  };

  const usingCustomEndpoint = !!(settings?.openai_base_url || baseUrl);

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="font-serif text-2xl font-semibold text-warm-900 mb-1">Settings</h1>
      <p className="text-warm-500 text-sm mb-8">Configure API keys, endpoint, and model defaults.</p>

      <div className="space-y-5">
        {/* Endpoint */}
        <div className="card space-y-5">
          <div className="flex items-center gap-2.5 pb-1 border-b border-warm-100">
            <div className="w-7 h-7 rounded-lg bg-brand-500/10 flex items-center justify-center">
              <Globe className="w-3.5 h-3.5 text-brand-500" />
            </div>
            <h2 className="font-semibold text-sm text-warm-900">OpenAI-Compatible Endpoint</h2>
          </div>

          <div>
            <label className="label">
              API Key
              {settings?.openai_api_key_set && (
                <span className="ml-2 inline-flex items-center gap-1 text-green-600 normal-case font-normal">
                  <CheckCircle className="w-3 h-3" /> set
                </span>
              )}
            </label>
            <div className="relative">
              <input
                type={showOpenai ? "text" : "password"}
                className="input pr-10"
                placeholder={settings?.openai_api_key_set ? "••••••••••••••• (update)" : "sk-..."}
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
              />
              <button
                type="button"
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-warm-400 hover:text-warm-700 transition-colors"
                onClick={() => setShowOpenai((v) => !v)}
              >
                {showOpenai ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div>
            <label className="label">
              Base URL
              <span className="ml-2 font-normal normal-case text-warm-400">
                — leave blank to use the official OpenAI API
              </span>
            </label>
            <input
              className="input font-mono text-sm"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://api.poe.com/v1"
            />
            {usingCustomEndpoint && (
              <p className="text-xs text-brand-500 mt-1.5 flex items-center gap-1">
                <Globe className="w-3 h-3" /> Using custom endpoint
              </p>
            )}
          </div>

          <div>
            <label className="label">
              Default Model
              <span className="ml-2 font-normal normal-case text-warm-400">
                — used for new agents
              </span>
            </label>
            <input
              className="input font-mono text-sm"
              value={deepagentModel}
              onChange={(e) => setDeepagentModel(e.target.value)}
              placeholder="gpt-4o"
              list="model-presets"
            />
            <datalist id="model-presets">
              <option value="gpt-4o" />
              <option value="gpt-4o-mini" />
              <option value="gpt-5.4-nano" />
              <option value="gpt-4-turbo" />
              <option value="claude-sonnet-4-6" />
              <option value="claude-opus-4-7" />
            </datalist>
            <p className="text-xs text-warm-400 mt-1.5">
              Custom endpoint: bare model name (e.g. <code className="text-brand-600 bg-brand-50 px-1 rounded">gpt-5.4-nano</code>).
              Official API: use <code className="text-brand-600 bg-brand-50 px-1 rounded">openai:gpt-4o</code> format.
            </p>
          </div>
        </div>

        {/* LangSmith */}
        <div className="card space-y-5">
          <div className="flex items-center gap-2.5 pb-1 border-b border-warm-100">
            <h2 className="font-semibold text-sm text-warm-900">LangSmith Tracing</h2>
          </div>

          <div>
            <label className="label">
              LangSmith API Key
              {settings?.langchain_api_key_set && (
                <span className="ml-2 inline-flex items-center gap-1 text-green-600 normal-case font-normal">
                  <CheckCircle className="w-3 h-3" /> set
                </span>
              )}
            </label>
            <div className="relative">
              <input
                type={showLangchain ? "text" : "password"}
                className="input pr-10"
                placeholder={settings?.langchain_api_key_set ? "••••••••••••••• (update)" : "ls__..."}
                value={langchainKey}
                onChange={(e) => setLangchainKey(e.target.value)}
              />
              <button
                type="button"
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-warm-400 hover:text-warm-700 transition-colors"
                onClick={() => setShowLangchain((v) => !v)}
              >
                {showLangchain ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="tracing"
              checked={tracing}
              onChange={(e) => setTracing(e.target.checked)}
              className="w-4 h-4 rounded"
            />
            <label htmlFor="tracing" className="text-sm text-warm-700">
              Enable LangSmith tracing
            </label>
          </div>
        </div>

        <button
          className="btn-primary"
          onClick={handleSave}
          disabled={mutation.isPending}
        >
          {saved ? <CheckCircle className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          {saved ? "Saved!" : "Save Settings"}
        </button>
      </div>
    </div>
  );
}
