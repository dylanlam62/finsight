import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Bot, Loader2, Plus } from "lucide-react";
import { useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getAgent } from "../api/client";
import ChatThread, { type ChatMessage } from "../components/ChatThread";

let msgId = 0;

export default function RunView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: agent } = useQuery({
    queryKey: ["agent", id],
    queryFn: () => getAgent(id!),
    enabled: !!id,
  });

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [liveStatus, setLiveStatus] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function appendToLastAgent(patch: Partial<ChatMessage>) {
    setMessages((prev) => {
      const idx = [...prev].reverse().findIndex((m) => m.role === "agent");
      if (idx === -1) return prev;
      const realIdx = prev.length - 1 - idx;
      const updated = [...prev];
      updated[realIdx] = { ...updated[realIdx], ...patch };
      return updated;
    });
  }

  function appendActivityToAgent(activity: ChatMessage["activities"][number]) {
    setMessages((prev) => {
      const idx = [...prev].reverse().findIndex((m) => m.role === "agent");
      if (idx === -1) return prev;
      const realIdx = prev.length - 1 - idx;
      const updated = [...prev];
      updated[realIdx] = {
        ...updated[realIdx],
        activities: [...updated[realIdx].activities, activity],
      };
      return updated;
    });
  }

  function appendContentToAgent(chunk: string) {
    setMessages((prev) => {
      const idx = [...prev].reverse().findIndex((m) => m.role === "agent");
      if (idx === -1) return prev;
      const realIdx = prev.length - 1 - idx;
      const updated = [...prev];
      updated[realIdx] = {
        ...updated[realIdx],
        content: updated[realIdx].content + chunk,
      };
      return updated;
    });
  }

  async function streamResponse(fetchPromise: Promise<Response>) {
    setIsRunning(true);
    setLiveStatus("");

    // Add empty agent bubble
    setMessages((prev) => [
      ...prev,
      { id: String(msgId++), role: "agent", content: "", activities: [], status: "streaming" },
    ]);

    try {
      const res = await fetchPromise;
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

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
            const event = JSON.parse(dataLine.slice(5).trim());
            handleEvent(event);
          } catch { /* skip malformed */ }
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Connection error";
      appendToLastAgent({ status: "error", content: msg });
    } finally {
      setIsRunning(false);
      setLiveStatus("");
    }
  }

  function handleEvent(event: Record<string, unknown>) {
    const type = event.type as string;
    const data = event.data as Record<string, unknown> | undefined;

    if (type === "done") {
      appendToLastAgent({ status: "done" });
      return;
    }

    if (type === "interrupt") {
      appendToLastAgent({
        status: "interrupted",
        hitl: {
          question: event.question as string,
          options: (event.options as string[]) ?? [],
          runId: event.run_id as string,
        },
      });
      return;
    }

    if (type === "error") {
      appendToLastAgent({ status: "error", content: event.message as string ?? "Unknown error" });
      return;
    }

    if (type === "on_chat_model_stream") {
      const chunk = (data as any)?.data?.chunk;
      const content: string = chunk?.content ?? "";
      if (content) appendContentToAgent(content);
      return;
    }

    if (type === "on_tool_start") {
      const name = (data as any)?.name ?? "tool";
      const toolInput = (data as any)?.data?.input;
      const label = friendlyToolLabel(name, toolInput);
      setLiveStatus(label);
      appendActivityToAgent({ id: String(msgId++), toolName: name, label, status: "running", input: toolInput });
      return;
    }

    if (type === "on_tool_end") {
      const name = (data as any)?.name ?? "tool";
      const output = String((data as any)?.data?.output ?? "");
      setLiveStatus("");
      setMessages((prev) => {
        const idx = [...prev].reverse().findIndex((m) => m.role === "agent");
        if (idx === -1) return prev;
        const realIdx = prev.length - 1 - idx;
        const updated = [...prev];
        const acts = updated[realIdx].activities.map((a) =>
          a.toolName === name && a.status === "running"
            ? { ...a, status: "done" as const, output: output.slice(0, 200) }
            : a
        );
        updated[realIdx] = { ...updated[realIdx], activities: acts };
        return updated;
      });
    }
  }

  function handleSend() {
    const text = input.trim();
    if (!text || isRunning) return;
    setInput("");

    setMessages((prev) => [
      ...prev,
      { id: String(msgId++), role: "user", content: text, activities: [], status: "done" },
    ]);

    streamResponse(
      fetch(`/api/agents/${id}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: text }),
      })
    );
  }

  function handleHitlSubmit(runId: string, answer: string) {
    setMessages((prev) => [
      ...prev,
      { id: String(msgId++), role: "user", content: answer, activities: [], status: "done" },
    ]);

    // Resume the interrupted run
    setMessages((p) => {
      // mark the interrupted agent bubble as streaming again
      const idx = [...p].reverse().findIndex((m) => m.role === "agent" && m.status === "interrupted");
      if (idx === -1) return p;
      const realIdx = p.length - 1 - idx;
      const updated = [...p];
      updated[realIdx] = { ...updated[realIdx], status: "streaming", hitl: undefined };
      return updated;
    });

    streamResponse(
      fetch(`/api/runs/${runId}/resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer }),
      })
    );
  }

  function handleNewConversation() {
    setMessages([]);
    setInput("");
    setLiveStatus("");
  }

  return (
    <div className="flex flex-col h-full bg-warm-50">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-3.5 border-b border-warm-200 bg-white shrink-0 shadow-sm">
        <button
          className="p-1.5 rounded-lg text-warm-400 hover:text-warm-800 hover:bg-warm-100 transition-colors"
          onClick={() => navigate(`/agents/${id}`)}
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center shadow-sm">
          <Bot className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-warm-900 truncate">{agent?.name ?? "Agent"}</p>
          {agent?.model && <p className="text-xs text-warm-400 font-mono">{agent.model}</p>}
        </div>
        {messages.length > 0 && (
          <button
            className="btn-secondary text-xs"
            onClick={handleNewConversation}
          >
            <Plus className="w-3 h-3" /> New conversation
          </button>
        )}
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <ChatThread
          messages={messages}
          isRunning={isRunning}
          liveStatus={liveStatus}
          onHitlSubmit={handleHitlSubmit}
        />
      </div>

      {/* Input area — floating Claude-style box */}
      <div className="shrink-0 px-4 pb-5 pt-3 bg-warm-50">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-0 bg-white border border-warm-300 rounded-2xl shadow-sm focus-within:border-brand-400 focus-within:ring-2 focus-within:ring-brand-400/15 transition-all overflow-hidden">
            <textarea
              ref={textareaRef}
              className="flex-1 resize-none px-4 py-3.5 text-sm text-warm-900 placeholder-warm-400 bg-transparent focus:outline-none leading-relaxed"
              rows={3}
              placeholder={isRunning ? "Agent is working…" : "Message the agent…"}
              value={input}
              disabled={isRunning}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <div className="p-2 self-end">
              <button
                className="w-9 h-9 rounded-xl bg-brand-500 text-white flex items-center justify-center hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm"
                onClick={handleSend}
                disabled={!input.trim() || isRunning}
              >
                {isRunning
                  ? <Loader2 className="w-4 h-4 animate-spin" />
                  : <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
                      <path d="M3 8L13 8M13 8L9 4M13 8L9 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                }
              </button>
            </div>
          </div>
          <p className="text-center text-xs text-warm-300 mt-2">
            Enter to send · Shift + Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}

function friendlyToolLabel(name: string, input: unknown): string {
  const i = input as Record<string, unknown> | undefined;
  switch (name) {
    case "write_todos": return "Planning steps…";
    case "market_research": return `Searching: "${String(i?.query ?? "").slice(0, 50)}"`;
    case "financial_calculator": return "Computing IRR & NPV…";
    case "sensitivity_analyzer": return "Running sensitivity scenarios…";
    case "kpi_generator": return "Generating KPI targets…";
    case "template_renderer": return `Writing section: ${i?.section_name ?? ""}`;
    case "validate_bcase": return "Validating business case…";
    case "risk_register": return "Building risk register…";
    case "document_parser": return "Parsing documents…";
    case "ask_human": return "Waiting for your input…";
    case "task": {
      const desc = String(i?.description ?? "").toLowerCase();
      if (desc.includes("research")) return "Delegating to research agent…";
      if (desc.includes("finance") || desc.includes("irr") || desc.includes("npv")) return "Delegating to finance agent…";
      if (desc.includes("write") || desc.includes("section")) return "Delegating to writer agent…";
      if (desc.includes("validate") || desc.includes("compliance")) return "Delegating to compliance agent…";
      return "Delegating to sub-agent…";
    }
    default: return `${name}…`;
  }
}
