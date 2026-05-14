import MonacoEditor from "@monaco-editor/react";

interface Props {
  value: string;
  onChange: (value: string) => void;
  height?: string;
  placeholder?: string;
}

export default function PromptEditor({ value, onChange, height = "300px" }: Props) {
  return (
    <div className="rounded-lg overflow-hidden border border-gray-700">
      <MonacoEditor
        height={height}
        defaultLanguage="markdown"
        theme="vs-dark"
        value={value}
        onChange={(v) => onChange(v ?? "")}
        options={{
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbers: "off",
          wordWrap: "on",
          scrollBeyondLastLine: false,
          padding: { top: 12, bottom: 12 },
          renderLineHighlight: "none",
          overviewRulerBorder: false,
          hideCursorInOverviewRuler: true,
        }}
      />
    </div>
  );
}
