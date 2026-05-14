const PRESET_MODELS = [
  // Bare names — used when OPENAI_BASE_URL points to a custom endpoint (Poe, Azure, Ollama…)
  "gpt-5.4-nano",
  "gpt-4o",
  "gpt-4o-mini",
  // Prefixed names — used when hitting the official provider APIs directly
  "openai:gpt-4o",
  "openai:gpt-4o-mini",
  "anthropic:claude-sonnet-4-6",
  "anthropic:claude-opus-4-7",
  "anthropic:claude-haiku-4-5",
];

interface Props {
  model: string;
  temperature: number;
  onModelChange: (v: string) => void;
  onTemperatureChange: (v: number) => void;
}

export default function ModelSelector({ model, temperature, onModelChange, onTemperatureChange }: Props) {
  return (
    <div className="space-y-4">
      <div>
        <label className="label">Model</label>
        <input
          className="input"
          value={model}
          onChange={(e) => onModelChange(e.target.value)}
          placeholder="openai:gpt-4o"
          list="model-presets"
        />
        <datalist id="model-presets">
          {PRESET_MODELS.map((m) => (
            <option key={m} value={m} />
          ))}
        </datalist>
        <p className="text-xs text-gray-500 mt-1">
          Bare name (e.g. <code className="text-brand-400">gpt-5.4-nano</code>) for custom endpoints ·
          Prefixed (e.g. <code className="text-brand-400">openai:gpt-4o</code>) for official APIs
        </p>
      </div>

      <div>
        <label className="label">Temperature — {temperature.toFixed(1)}</label>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          value={temperature}
          onChange={(e) => onTemperatureChange(parseFloat(e.target.value))}
          className="w-full accent-brand-500"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-0.5">
          <span>Precise (0)</span>
          <span>Creative (2)</span>
        </div>
      </div>
    </div>
  );
}
