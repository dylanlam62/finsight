import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  Bot,
  Check,
  ChevronDown,
  ChevronRight,
  Copy,
  Download,
  Loader2,
  User,
  Wrench,
  Sparkles,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Activity {
  id: string;
  toolName: string;
  label: string;
  status: "running" | "done";
  input?: unknown;
  output?: string;
  streamedText?: string;
}

export interface MultiField {
  id: string;
  label: string;
  options?: string[];
}

export interface HitlData {
  question: string;
  options: string[];
  multi_fields?: MultiField[];
  runId: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "agent";
  content: string;
  activities: Activity[];
  status: "streaming" | "done" | "error" | "interrupted";
  hitl?: HitlData;
}

interface Props {
  messages: ChatMessage[];
  isRunning: boolean;
  liveStatus: string;
  onHitlSubmit: (runId: string, answer: string) => void;
}

// ---------------------------------------------------------------------------
// Markdown renderer (no external deps)
// ---------------------------------------------------------------------------

function parseInline(text: string): React.ReactNode {
  const tokens: React.ReactNode[] = [];
  let rest = text;
  let key = 0;

  while (rest.length > 0) {
    const bold   = rest.match(/^([\s\S]*?)\*\*([\s\S]*?)\*\*([\s\S]*)$/);
    const code   = rest.match(/^([\s\S]*?)`([^`]+)`([\s\S]*)$/);
    const italic = rest.match(/^([\s\S]*?)\*([\s\S]*?)\*([\s\S]*)$/);

    const candidates = [
      bold   && { before: bold[1],   inner: bold[2],   after: bold[3],   tag: "bold"   as const },
      code   && { before: code[1],   inner: code[2],   after: code[3],   tag: "code"   as const },
      italic && { before: italic[1], inner: italic[2], after: italic[3], tag: "italic" as const },
    ].filter(Boolean) as { before: string; inner: string; after: string; tag: "bold" | "code" | "italic" }[];

    candidates.sort((a, b) => a.before.length - b.before.length);
    const winner = candidates[0];

    if (!winner) { tokens.push(rest); break; }
    if (winner.before) tokens.push(winner.before);
    if (winner.tag === "bold")
      tokens.push(<strong key={key++} className="font-semibold text-warm-900">{winner.inner}</strong>);
    else if (winner.tag === "code")
      tokens.push(<code key={key++} className="bg-warm-100 border border-warm-200 rounded px-1.5 py-0.5 text-xs font-mono text-brand-600">{winner.inner}</code>);
    else
      tokens.push(<em key={key++} className="italic">{winner.inner}</em>);
    rest = winner.after;
  }

  return tokens.length === 1 ? tokens[0] : <>{tokens}</>;
}

function Markdown({ content }: { content: string }) {
  const lines = content.split("\n");
  const nodes: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("```")) {
      const lang = line.slice(3).trim();
      const code: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) { code.push(lines[i]); i++; }
      nodes.push(
        <div key={i} className="my-3 rounded-xl overflow-hidden border border-warm-200">
          {lang && (
            <div className="px-4 py-1.5 bg-warm-100 border-b border-warm-200 text-xs font-mono text-warm-500">
              {lang}
            </div>
          )}
          <pre className="bg-warm-50 p-4 text-xs overflow-x-auto font-mono text-warm-800 leading-relaxed">
            {code.join("\n")}
          </pre>
        </div>
      );
    } else if (line.startsWith("# ")) {
      nodes.push(<h1 key={i} className="font-serif text-xl font-semibold text-warm-900 mt-5 mb-2">{parseInline(line.slice(2))}</h1>);
    } else if (line.startsWith("## ")) {
      nodes.push(<h2 key={i} className="font-serif text-base font-semibold text-warm-900 mt-4 mb-1.5 pb-1 border-b border-warm-200">{parseInline(line.slice(3))}</h2>);
    } else if (line.startsWith("### ")) {
      nodes.push(<h3 key={i} className="text-sm font-semibold text-warm-800 mt-3 mb-1">{parseInline(line.slice(4))}</h3>);
    } else if (/^---+$/.test(line.trim())) {
      nodes.push(<hr key={i} className="border-warm-200 my-3" />);
    } else if (/^[-*] /.test(line)) {
      const items: React.ReactNode[] = [];
      while (i < lines.length && /^[-*] /.test(lines[i])) {
        items.push(<li key={i}>{parseInline(lines[i].slice(2))}</li>);
        i++;
      }
      nodes.push(<ul key={`ul-${i}`} className="list-disc pl-5 my-2 space-y-1 text-warm-700">{items}</ul>);
      continue;
    } else if (/^\d+\. /.test(line)) {
      const items: React.ReactNode[] = [];
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        items.push(<li key={i}>{parseInline(lines[i].replace(/^\d+\. /, ""))}</li>);
        i++;
      }
      nodes.push(<ol key={`ol-${i}`} className="list-decimal pl-5 my-2 space-y-1 text-warm-700">{items}</ol>);
      continue;
    } else if (line.startsWith("> ")) {
      nodes.push(
        <blockquote key={i} className="border-l-2 border-brand-300 pl-4 my-2 text-warm-500 italic text-sm">
          {parseInline(line.slice(2))}
        </blockquote>
      );
    } else if (line.trim() === "") {
      // spacing handled by parent
    } else {
      nodes.push(<p key={i} className="my-1.5 text-warm-700 leading-relaxed">{parseInline(line)}</p>);
    }

    i++;
  }

  return <div className="text-sm space-y-0.5">{nodes}</div>;
}

// ---------------------------------------------------------------------------
// Activity feed — collapsible, Claude Code style
// ---------------------------------------------------------------------------

function ActivityFeed({ activities }: { activities: Activity[] }) {
  const [open, setOpen] = useState(false);
  if (activities.length === 0) return null;

  const done   = activities.filter((a) => a.status === "done").length;
  const allDone = done === activities.length;

  return (
    <div className="mb-3 border border-warm-200 rounded-xl overflow-hidden text-xs shadow-sm">
      <button
        className="w-full flex items-center gap-2 px-3 py-2.5 bg-warm-50 hover:bg-warm-100 transition-colors text-left"
        onClick={() => setOpen((v) => !v)}
      >
        {open
          ? <ChevronDown className="w-3.5 h-3.5 text-warm-400 shrink-0" />
          : <ChevronRight className="w-3.5 h-3.5 text-warm-400 shrink-0" />}
        <Wrench className="w-3.5 h-3.5 text-warm-400 shrink-0" />
        <span className="text-warm-600 font-medium flex-1">
          {allDone ? `${activities.length} step${activities.length !== 1 ? "s" : ""} completed` : `${done} / ${activities.length} steps`}
        </span>
        {!allDone && <Loader2 className="w-3 h-3 text-brand-400 animate-spin" />}
      </button>

      {open && (
        <div className="divide-y divide-warm-100">
          {activities.map((a) => (
            <div key={a.id} className="flex flex-col gap-1.5 px-3 py-2 bg-white">
              <div className="flex items-start gap-2.5">
                {a.status === "running"
                  ? <Loader2 className="w-3 h-3 text-brand-400 mt-0.5 shrink-0 animate-spin" />
                  : <Check className="w-3 h-3 text-green-500 mt-0.5 shrink-0" />}
                <span className={a.status === "running" ? "text-brand-600" : "text-warm-500"}>
                  {a.label}
                </span>
              </div>
              {a.streamedText && (
                <div className="pl-6 text-warm-600">
                  <Markdown content={a.streamedText} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// HITL card — warm amber style
// ---------------------------------------------------------------------------

function HitlCard({ hitl, onSubmit }: { hitl: HitlData; onSubmit: (runId: string, answer: string) => void }) {
  if (hitl.multi_fields && hitl.multi_fields.length > 0) {
    return <HitlMultiTabCard hitl={hitl} onSubmit={onSubmit} />;
  }

  const [selected, setSelected] = useState<string | null>(null);
  const [freeText, setFreeText] = useState("");

  function submit(answer: string) {
    if (!answer.trim()) return;
    onSubmit(hitl.runId, answer.trim());
  }

  return (
    <div className="mb-3 border border-amber-200 rounded-xl overflow-hidden bg-amber-50 shadow-sm">
      <div className="flex items-start gap-3 px-4 pt-4 pb-3">
        <div className="w-6 h-6 rounded-full bg-amber-100 border border-amber-200 flex items-center justify-center shrink-0 mt-0.5">
          <Sparkles className="w-3 h-3 text-amber-600" />
        </div>
        <div>
          <p className="text-xs font-semibold text-amber-700 mb-1 uppercase tracking-wide">Input needed</p>
          <p className="text-sm text-warm-800 leading-relaxed">{hitl.question}</p>
        </div>
      </div>

      {hitl.options.length > 0 && (
        <div className="px-4 pb-3 flex flex-wrap gap-2">
          {hitl.options.map((opt, idx) => (
            <button
              key={idx}
              onClick={() => { setSelected(opt); setFreeText(""); }}
              className={`text-xs rounded-lg border px-3 py-1.5 transition-all font-medium ${
                selected === opt
                  ? "border-brand-400 bg-brand-50 text-brand-700 shadow-sm"
                  : "border-warm-300 bg-white text-warm-700 hover:border-warm-400 hover:bg-warm-50"
              }`}
            >
              {idx + 1}. {opt}
            </button>
          ))}
        </div>
      )}

      <div className="px-4 pb-4 flex gap-2 items-end">
        <div className="flex-1">
          {hitl.options.length > 0 && (
            <p className="text-xs text-warm-400 mb-1">Or type a custom answer:</p>
          )}
          <textarea
            className="input w-full resize-none text-sm"
            rows={2}
            placeholder="Type your answer…"
            value={selected ? "" : freeText}
            onChange={(e) => { setSelected(null); setFreeText(e.target.value); }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(selected ?? freeText); }
            }}
          />
        </div>
        <button
          className="btn-primary self-end text-sm px-4"
          onClick={() => submit(selected ?? freeText)}
          disabled={!selected && !freeText.trim()}
        >
          Submit
        </button>
      </div>
    </div>
  );
}

function HitlMultiTabCard({ hitl, onSubmit }: { hitl: HitlData; onSubmit: (runId: string, answer: string) => void }) {
  const fields = hitl.multi_fields || [];
  const [activeTab, setActiveTab] = useState(0);
  const [answers, setAnswers] = useState<Record<string, { selected: string | null; freeText: string }>>(() => {
    const init: any = {};
    fields.forEach(f => init[f.id] = { selected: null, freeText: "" });
    return init;
  });

  function updateAnswer(id: string, selected: string | null, freeText: string) {
    setAnswers(prev => ({ ...prev, [id]: { selected, freeText } }));
  }

  function submit() {
    const finalAnswers = fields.map(f => {
      const ans = answers[f.id];
      return `${f.label}: ${(ans.selected ?? ans.freeText.trim()) || 'Not provided'}`;
    }).join("\n");
    onSubmit(hitl.runId, finalAnswers);
  }

  const currentField = fields[activeTab];
  const currentAns = answers[currentField.id];
  const allAnswered = fields.every(f => answers[f.id].selected || answers[f.id].freeText.trim());

  return (
    <div className="mb-3 border border-amber-200 rounded-xl overflow-hidden bg-amber-50 shadow-sm">
      <div className="flex items-start gap-3 px-4 pt-4 pb-3">
        <div className="w-6 h-6 rounded-full bg-amber-100 border border-amber-200 flex items-center justify-center shrink-0 mt-0.5">
          <Sparkles className="w-3 h-3 text-amber-600" />
        </div>
        <div>
          <p className="text-xs font-semibold text-amber-700 mb-1 uppercase tracking-wide">Input needed</p>
          <p className="text-sm text-warm-800 leading-relaxed">{hitl.question}</p>
        </div>
      </div>

      <div className="border-b border-amber-200 flex overflow-x-auto">
        {fields.map((f, idx) => (
          <button
            key={f.id}
            onClick={() => setActiveTab(idx)}
            className={`px-4 py-2 text-xs font-medium whitespace-nowrap border-b-2 transition-colors ${
              activeTab === idx ? "border-amber-600 text-amber-800 bg-amber-100/50" : "border-transparent text-warm-600 hover:text-warm-800 hover:bg-amber-100/30"
            }`}
          >
            {f.label} {(answers[f.id].selected || answers[f.id].freeText.trim()) && <Check className="w-3 h-3 inline text-green-600 ml-1" />}
          </button>
        ))}
      </div>

      <div className="p-4 bg-white">
        {currentField.options && currentField.options.length > 0 && (
          <div className="pb-4 flex flex-wrap gap-2">
            {currentField.options.map((opt, idx) => (
              <button
                key={idx}
                onClick={() => updateAnswer(currentField.id, opt, "")}
                className={`text-xs rounded-lg border px-3 py-1.5 transition-all font-medium ${
                  currentAns.selected === opt
                    ? "border-brand-400 bg-brand-50 text-brand-700 shadow-sm"
                    : "border-warm-300 bg-white text-warm-700 hover:border-warm-400 hover:bg-warm-50"
                }`}
              >
                {opt}
              </button>
            ))}
          </div>
        )}
        <div className="flex gap-2 items-end">
          <div className="flex-1">
            <p className="text-xs text-warm-400 mb-1">Custom answer:</p>
            <textarea
              className="input w-full resize-none text-sm bg-warm-50 focus:bg-white"
              rows={2}
              placeholder={`Type answer for ${currentField.label}…`}
              value={currentAns.selected ? "" : currentAns.freeText}
              onChange={(e) => updateAnswer(currentField.id, null, e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="px-4 py-3 bg-amber-50 border-t border-amber-200 flex justify-between items-center">
        <div className="text-xs text-warm-500">
          Step {activeTab + 1} of {fields.length}
        </div>
        <div className="flex gap-2">
          {activeTab < fields.length - 1 ? (
            <button className="btn-secondary text-sm px-4" onClick={() => setActiveTab(a => a + 1)}>Next</button>
          ) : (
            <button
              className="btn-primary text-sm px-4"
              onClick={submit}
              disabled={!allAnswered}
            >
              Submit All
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Message bubbles — Claude aesthetic
// ---------------------------------------------------------------------------

function UserBubble({ msg }: { msg: ChatMessage }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[72%] flex items-end gap-2.5">
        <div className="bg-warm-800 rounded-2xl rounded-br-sm px-4 py-3 text-sm text-warm-50 leading-relaxed whitespace-pre-wrap shadow-sm">
          {msg.content}
        </div>
        <div className="w-7 h-7 rounded-full bg-warm-200 border border-warm-300 flex items-center justify-center shrink-0">
          <User className="w-3.5 h-3.5 text-warm-600" />
        </div>
      </div>
    </div>
  );
}

function AgentBubble({
  msg,
  onHitlSubmit,
}: {
  msg: ChatMessage;
  onHitlSubmit: (runId: string, answer: string) => void;
}) {
  const [copied, setCopied] = useState(false);

  function copyContent() {
    navigator.clipboard.writeText(msg.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function downloadContent() {
    const blob = new Blob([msg.content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "response.md";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="flex justify-start items-start gap-3">
      {/* Agent avatar */}
      <div className="w-7 h-7 rounded-lg bg-brand-500 flex items-center justify-center shrink-0 mt-1 shadow-sm">
        <Bot className="w-3.5 h-3.5 text-white" />
      </div>

      <div className="flex-1 min-w-0 max-w-[88%]">
        {/* Activity feed */}
        <ActivityFeed activities={msg.activities} />

        {/* HITL card */}
        {msg.hitl && <HitlCard hitl={msg.hitl} onSubmit={onHitlSubmit} />}

        {/* Error state */}
        {msg.status === "error" && (
          <div className="flex items-center gap-2 text-red-600 text-sm px-4 py-3 bg-red-50 border border-red-200 rounded-xl">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {msg.content || "An error occurred"}
          </div>
        )}

        {/* Thinking animation — no content yet */}
        {msg.status === "streaming" && !msg.content && !msg.hitl && (
          <div className="flex items-center gap-2 text-warm-400 text-sm py-2">
            <span className="flex gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-warm-400 animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-warm-400 animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-warm-400 animate-bounce" style={{ animationDelay: "300ms" }} />
            </span>
          </div>
        )}

        {/* Main content — no bubble, just text (Claude style) */}
        {msg.content && msg.status !== "error" && (
          <div className="prose-like">
            <Markdown content={msg.content} />

            {/* Copy / download — only when done */}
            {msg.status === "done" && (
              <div className="flex gap-3 mt-4 pt-3 border-t border-warm-100">
                <button
                  onClick={copyContent}
                  className="flex items-center gap-1.5 text-xs text-warm-400 hover:text-warm-700 transition-colors"
                >
                  {copied
                    ? <><Check className="w-3.5 h-3.5 text-green-500" /> Copied</>
                    : <><Copy className="w-3.5 h-3.5" /> Copy</>}
                </button>
                <button
                  onClick={downloadContent}
                  className="flex items-center gap-1.5 text-xs text-warm-400 hover:text-warm-700 transition-colors"
                >
                  <Download className="w-3.5 h-3.5" /> Download .md
                </button>
              </div>
            )}

            {/* Streaming cursor */}
            {msg.status === "streaming" && (
              <span className="inline-block w-0.5 h-4 bg-warm-400 animate-pulse ml-0.5 align-middle" />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Thread container
// ---------------------------------------------------------------------------

export default function ChatThread({ messages, isRunning, liveStatus, onHitlSubmit }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-center px-6">
        <div>
          <div className="w-16 h-16 rounded-2xl bg-brand-500/10 flex items-center justify-center mx-auto mb-4 shadow-sm">
            <Bot className="w-8 h-8 text-brand-500" />
          </div>
          <p className="font-serif text-lg font-medium text-warm-800">How can I help you today?</p>
          <p className="text-warm-400 text-sm mt-1.5">Type a message below to start the conversation</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-8">
      <div className="max-w-3xl mx-auto space-y-8">
        {messages.map((msg) =>
          msg.role === "user"
            ? <UserBubble key={msg.id} msg={msg} />
            : <AgentBubble key={msg.id} msg={msg} onHitlSubmit={onHitlSubmit} />
        )}

        {/* Live status ticker */}
        {isRunning && liveStatus && (
          <div className="flex items-center gap-2 text-xs text-warm-400 pl-10">
            <Loader2 className="w-3 h-3 animate-spin text-brand-400" />
            {liveStatus}
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
