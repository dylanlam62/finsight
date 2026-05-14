import { useEffect, useRef, useState } from "react";
import { Terminal, Wrench, Cpu, AlertCircle, CheckCircle2 } from "lucide-react";

type EventKind =
  | "on_chat_model_stream"
  | "on_tool_start"
  | "on_tool_end"
  | "on_chain_start"
  | "on_chain_end"
  | "done"
  | "error"
  | string;

interface StreamEvent {
  type: EventKind;
  data?: unknown;
  run_id?: string;
  message?: string;
}

interface LogLine {
  id: number;
  kind: EventKind;
  text: string;
  name?: string;
}

interface Props {
  agentId: string;
  input: string;
  onDone?: (runId: string) => void;
}

let lineId = 0;

export default function RunConsole({ agentId, input, onDone }: Props) {
  const [lines, setLines] = useState<LogLine[]>([]);
  const [status, setStatus] = useState<"idle" | "running" | "done" | "error">("idle");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!input) return;
    setLines([]);
    setStatus("running");

    const es = new EventSource(`/api/agents/${agentId}/run`, { withCredentials: false });

    // EventSource only supports GET; use fetch for POST with SSE
    const controller = new AbortController();
    es.close();

    fetch(`/api/agents/${agentId}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input }),
      signal: controller.signal,
    }).then(async (res) => {
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          const dataLine = part.split("\n").find((l) => l.startsWith("data:"));
          if (!dataLine) continue;
          try {
            const event: StreamEvent = JSON.parse(dataLine.slice(5).trim());
            handleEvent(event);
          } catch {
            // skip malformed
          }
        }
      }
    }).catch((err) => {
      if (err.name !== "AbortError") {
        addLine("error", `Connection error: ${err.message}`);
        setStatus("error");
      }
    });

    return () => controller.abort();
  }, [agentId, input]);

  function addLine(kind: EventKind, text: string, name?: string) {
    setLines((prev) => [...prev, { id: lineId++, kind, text, name }]);
  }

  function handleEvent(event: StreamEvent) {
    const { type, data } = event;

    if (type === "done") {
      setStatus("done");
      onDone?.(event.run_id ?? "");
      return;
    }

    if (type === "error") {
      addLine("error", event.message ?? "Unknown error");
      setStatus("error");
      return;
    }

    if (type === "on_chat_model_stream") {
      const chunk = (data as any)?.data?.chunk;
      const content: string = chunk?.content ?? "";
      if (content) {
        setLines((prev) => {
          const last = prev[prev.length - 1];
          if (last?.kind === "on_chat_model_stream") {
            return [...prev.slice(0, -1), { ...last, text: last.text + content }];
          }
          return [...prev, { id: lineId++, kind: "on_chat_model_stream", text: content }];
        });
      }
    } else if (type === "on_tool_start") {
      const name: string = (data as any)?.name ?? "tool";
      const input = JSON.stringify((data as any)?.data?.input ?? {});
      addLine("on_tool_start", input, name);
    } else if (type === "on_tool_end") {
      const name: string = (data as any)?.name ?? "tool";
      const output = String((data as any)?.data?.output ?? "");
      addLine("on_tool_end", output.slice(0, 300), name);
    }
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-950 overflow-hidden flex flex-col" style={{ minHeight: 400 }}>
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-800 bg-gray-900">
        <Terminal className="w-4 h-4 text-gray-500" />
        <span className="text-xs font-mono text-gray-400">Run Console</span>
        <span className="ml-auto">
          {status === "running" && <span className="text-xs text-yellow-400 animate-pulse">● running</span>}
          {status === "done" && <span className="text-xs text-green-400 flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> done</span>}
          {status === "error" && <span className="text-xs text-red-400 flex items-center gap-1"><AlertCircle className="w-3.5 h-3.5" /> error</span>}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 font-mono text-sm space-y-2">
        {lines.map((line) => (
          <div key={line.id}>
            {line.kind === "on_chat_model_stream" && (
              <p className="text-gray-100 whitespace-pre-wrap leading-relaxed">{line.text}</p>
            )}
            {line.kind === "on_tool_start" && (
              <div className="flex items-start gap-2 text-xs">
                <Wrench className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />
                <div>
                  <span className="text-amber-400 font-semibold">{line.name}</span>
                  <span className="text-gray-500 ml-1">→</span>
                  <code className="text-gray-400 ml-1 break-all">{line.text}</code>
                </div>
              </div>
            )}
            {line.kind === "on_tool_end" && (
              <div className="flex items-start gap-2 text-xs ml-5">
                <span className="text-gray-600">↳</span>
                <code className="text-gray-500 break-all">{line.text}</code>
              </div>
            )}
            {line.kind === "error" && (
              <div className="flex items-center gap-2 text-xs text-red-400">
                <AlertCircle className="w-3.5 h-3.5" />
                {line.text}
              </div>
            )}
          </div>
        ))}
        {lines.length === 0 && status === "idle" && (
          <p className="text-gray-600 text-center mt-8">Output will appear here when you run the agent.</p>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
