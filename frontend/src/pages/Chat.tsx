import { useEffect, useRef, useState } from "react";
import {
  MessageSquare, Plus, Send, Trash2, FileText, User, Bot,
  Copy, Check, RefreshCw, ThumbsUp, ThumbsDown, ExternalLink,
} from "lucide-react";
import {
  ask, deleteConversation, getConversation, listConversations, rateMessage,
  type Conversation, type Message, type SourceRef,
} from "../api/chat";
import { getErrorMessage } from "../api/client";
import { useToast } from "../context/ToastContext";
import EmptyState from "../components/ui/EmptyState";
import Spinner from "../components/ui/Spinner";
import SourcePassageDialog from "../components/chat/SourcePassageDialog";

function CitationBadges({
  refs, onOpen,
}: { refs: SourceRef[]; onOpen: (s: SourceRef) => void }) {
  if (!refs.length) return null;
  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {refs.map((r, i) => (
        <button
          key={i}
          type="button"
          onClick={() => onOpen(r)}
          className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full bg-brand-50 text-brand-700 border border-brand-200 hover:bg-brand-100 dark:bg-brand-500/15 dark:text-brand-200 dark:border-brand-500/40 dark:hover:bg-brand-500/25 transition"
          title={r.snippet ?? ""}
        >
          <FileText className="w-3 h-3" />
          <span className="font-medium truncate max-w-[160px]">{r.title}</span>
          {r.page_number != null && (
            <span className="text-brand-500 dark:text-brand-300">p.{r.page_number}</span>
          )}
        </button>
      ))}
    </div>
  );
}

function MessageActions({
  message, onRegenerate, onOpenSource,
}: {
  message: Message;
  onRegenerate: () => void;
  onOpenSource: (s: SourceRef) => void;
}) {
  const { push } = useToast();
  const [copied, setCopied] = useState(false);
  const [rating, setRating] = useState<"up" | "down" | null>(message.feedback ?? null);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      push("success", "Answer copied");
      setTimeout(() => setCopied(false), 1500);
    } catch {
      push("error", "Copy failed");
    }
  };

  const sendFeedback = async (value: "up" | "down") => {
    const next = rating === value ? null : value;
    try {
      await rateMessage(message.id, next);
      setRating(next);
      push(
        "success",
        next === "up" ? "Marked helpful"
        : next === "down" ? "Marked unhelpful"
        : "Feedback cleared",
      );
    } catch {
      push("error", "Feedback failed");
    }
  };

  return (
    <div className="flex items-center gap-1 mt-2">
      <button
        onClick={copy}
        className="p-1.5 rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-500 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition"
        title="Copy answer"
      >
        {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
      </button>
      <button
        onClick={onRegenerate}
        className="p-1.5 rounded-md text-slate-400 hover:bg-slate-100 hover:text-brand-600 dark:text-slate-500 dark:hover:bg-slate-800 dark:hover:text-brand-300 transition"
        title="Regenerate answer"
      >
        <RefreshCw className="w-3.5 h-3.5" />
      </button>
      <div className="w-px h-3 bg-slate-200 dark:bg-slate-700 mx-1" />
      <button
        onClick={() => sendFeedback("up")}
        className={`p-1.5 rounded-md transition ${
          rating === "up"
            ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-300"
            : "text-slate-400 hover:bg-slate-100 hover:text-emerald-600 dark:text-slate-500 dark:hover:bg-slate-800 dark:hover:text-emerald-400"
        }`}
        title="Helpful"
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>
      <button
        onClick={() => sendFeedback("down")}
        className={`p-1.5 rounded-md transition ${
          rating === "down"
            ? "bg-rose-50 text-rose-600 dark:bg-rose-500/20 dark:text-rose-300"
            : "text-slate-400 hover:bg-slate-100 hover:text-rose-600 dark:text-slate-500 dark:hover:bg-slate-800 dark:hover:text-rose-400"
        }`}
        title="Not helpful"
      >
        <ThumbsDown className="w-3.5 h-3.5" />
      </button>
      {message.source_references.length > 0 && (
        <>
          <div className="w-px h-3 bg-slate-200 dark:bg-slate-700 mx-1" />
          <button
            onClick={() => onOpenSource(message.source_references[0])}
            className="p-1.5 rounded-md text-slate-400 hover:bg-slate-100 hover:text-brand-600 dark:text-slate-500 dark:hover:bg-slate-800 dark:hover:text-brand-300 transition"
            title="Open source passage"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
        </>
      )}
    </div>
  );
}

function MessageBubble({
  m, onRegenerate, onOpenSource,
}: {
  m: Message;
  onRegenerate: () => void;
  onOpenSource: (s: SourceRef) => void;
}) {
  const isUser = m.role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : ""}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-brand-tile flex items-center justify-center shrink-0 shadow">
          <Bot className="w-4 h-4 text-white" />
        </div>
      )}
      <div className={`max-w-2xl ${isUser ? "order-first" : ""}`}>
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm whitespace-pre-line ${
            isUser
              ? "bg-brand-gradient text-white shadow-md"
              : "bg-white border border-slate-200 text-slate-800 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100"
          }`}
        >
          {m.content}
        </div>
        {!isUser && (
          <>
            <CitationBadges refs={m.source_references} onOpen={onOpenSource} />
            <MessageActions
              message={m}
              onRegenerate={onRegenerate}
              onOpenSource={onOpenSource}
            />
          </>
        )}
        <p className={`text-[11px] text-slate-400 dark:text-slate-500 mt-1 ${isUser ? "text-right" : ""}`}>
          {new Date(m.created_at).toLocaleTimeString()}
        </p>
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-lg bg-slate-200 dark:bg-slate-700 flex items-center justify-center shrink-0">
          <User className="w-4 h-4 text-slate-600 dark:text-slate-300" />
        </div>
      )}
    </div>
  );
}

export default function Chat() {
  const { push } = useToast();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [loadingConv, setLoadingConv] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [openSource, setOpenSource] = useState<SourceRef | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const fetchConversations = async () => {
    setLoadingConv(true);
    try {
      const data = await listConversations();
      setConversations(data.items);
    } catch (err) {
      push("error", getErrorMessage(err, "Failed to load conversations"));
    } finally {
      setLoadingConv(false);
    }
  };

  useEffect(() => { void fetchConversations(); }, []);

  useEffect(() => {
    if (!activeId) { setMessages([]); return; }
    (async () => {
      setLoadingMessages(true);
      try {
        const data = await getConversation(activeId);
        setMessages(data.messages);
      } catch (err) {
        push("error", getErrorMessage(err, "Failed to load conversation"));
      } finally {
        setLoadingMessages(false);
      }
    })();
  }, [activeId, push]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const startNew = () => {
    setActiveId(null);
    setMessages([]);
    setQuestion("");
  };

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || sending) return;
    const q = question.trim();
    setQuestion("");
    setSending(true);

    const tempId = `tmp-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: tempId, conversation_id: activeId ?? "new", user_id: "me",
        role: "user", content: q, source_references: [],
        created_at: new Date().toISOString(),
      },
    ]);

    try {
      const res = await ask(q, activeId ?? undefined);
      setActiveId(res.conversation_id);
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempId),
        {
          id: `u-${Date.now()}`, conversation_id: res.conversation_id,
          user_id: "me", role: "user", content: q,
          source_references: [], created_at: new Date().toISOString(),
        },
        res.message,
      ]);
      void fetchConversations();
    } catch (err) {
      push("error", getErrorMessage(err, "Message failed"));
      setMessages((prev) => prev.filter((m) => m.id !== tempId));
    } finally {
      setSending(false);
    }
  };

  const regenerate = async () => {
    if (sending) return;
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    if (!lastUser) return;

    setMessages((prev) => {
      const trimmed = [...prev];
      while (trimmed.length && trimmed[trimmed.length - 1].role !== "user") trimmed.pop();
      return trimmed;
    });

    setSending(true);
    try {
      const res = await ask(lastUser.content, activeId ?? undefined);
      setMessages((prev) => [...prev, res.message]);
    } catch (err) {
      push("error", getErrorMessage(err, "Regenerate failed"));
      if (activeId) {
        const data = await getConversation(activeId);
        setMessages(data.messages);
      }
    } finally {
      setSending(false);
    }
  };

  const removeConv = async (id: string) => {
    if (!confirm("Delete this conversation?")) return;
    try {
      await deleteConversation(id);
      push("success", "Conversation deleted");
      if (activeId === id) startNew();
      void fetchConversations();
    } catch (err) {
      push("error", getErrorMessage(err, "Delete failed"));
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] max-w-6xl gap-4">
      <aside className="w-64 shrink-0 card flex flex-col overflow-hidden">
        <div className="p-3 border-b border-slate-100 dark:border-slate-800">
          <button onClick={startNew} className="btn-primary w-full">
            <Plus className="w-4 h-4" /> New conversation
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {loadingConv ? (
            <p className="p-4 text-sm text-slate-500 dark:text-slate-400">Loading...</p>
          ) : conversations.length === 0 ? (
            <p className="p-4 text-sm text-slate-500 dark:text-slate-400">No conversations yet</p>
          ) : (
            <ul>
              {conversations.map((c) => (
                <li key={c.id} className="group">
                  <div
                    className={`flex items-center gap-2 px-3 py-2 cursor-pointer text-sm border-l-2 transition ${
                      activeId === c.id
                        ? "border-l-accent-500 bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-200"
                        : "border-l-transparent text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800/60"
                    }`}
                    onClick={() => setActiveId(c.id)}
                  >
                    <MessageSquare className="w-4 h-4 shrink-0" />
                    <span className="truncate flex-1">{c.title}</span>
                    <button
                      onClick={(e) => { e.stopPropagation(); void removeConv(c.id); }}
                      className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-600 dark:text-slate-500 dark:hover:text-red-400"
                      title="Delete"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      <section className="flex-1 card flex flex-col overflow-hidden">
        <div className="p-4 border-b border-slate-100 dark:border-slate-800">
          <h1 className="font-semibold text-slate-900 dark:text-white">
            {activeId ? "Conversation" : "New conversation"}
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Answers grounded in your documents with citations.
          </p>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 dark:bg-slate-950">
          {loadingMessages ? (
            <Spinner label="Loading messages..." />
          ) : messages.length === 0 ? (
            <EmptyState
              icon={MessageSquare}
              title="Ask your knowledge base"
              description="Try a question about your uploaded documents."
            />
          ) : (
            messages.map((m) => (
              <MessageBubble
                key={m.id}
                m={m}
                onRegenerate={regenerate}
                onOpenSource={(s) => setOpenSource(s)}
              />
            ))
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={send} className="p-3 border-t border-slate-100 dark:border-slate-800 flex gap-2">
          <input
            className="input flex-1"
            placeholder="Ask a question..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={sending}
          />
          <button
            type="submit"
            className="btn-primary"
            disabled={sending || !question.trim()}
          >
            <Send className="w-4 h-4" />
            {sending ? "..." : "Send"}
          </button>
        </form>
      </section>

      {openSource && (
        <SourcePassageDialog source={openSource} onClose={() => setOpenSource(null)} />
      )}
    </div>
  );
}
