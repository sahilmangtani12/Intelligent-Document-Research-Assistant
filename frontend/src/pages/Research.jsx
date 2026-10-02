import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUp, BookOpen, Filter, Trash2 } from "lucide-react";
import { useChat } from "../hooks/useChat";
import { useDocuments } from "../context/DocumentsContext";
import ChatMessage from "../components/ChatMessage";
import DocumentList from "../components/DocumentList";
import { EmptyState, btnPrimary } from "../components/ui";

export default function Research() {
  const { documents } = useDocuments();
  const { messages, pending, ask, clear, dropMessage } = useChat();
  const [text, setText] = useState("");
  const [selected, setSelected] = useState([]);
  const [showFilter, setShowFilter] = useState(false);
  const end = useRef(null);

  const ready = useMemo(() => documents.filter((d) => d.status === "ready"), [documents]);
  const activeSelected = selected.filter((id) => ready.some((d) => d.id === id));

  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, pending]);

  const submit = (e) => {
    e?.preventDefault();
    if (!text.trim() || pending) return;
    ask(text, activeSelected);
    setText("");
  };

  const toggle = (id) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  const retry = (m) => { dropMessage(m.id); ask(m.question, activeSelected); };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between gap-3 border-b border-line bg-surface px-4 py-3 sm:px-8">
        <div className="min-w-0">
          <h1 className="font-serif text-xl font-medium">Research</h1>
          <p className="truncate text-xs text-muted">
            {activeSelected.length ? `Searching ${activeSelected.length} selected document${activeSelected.length > 1 ? "s" : ""}` : `Searching all ${ready.length} ready document${ready.length === 1 ? "" : "s"}`}
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowFilter((s) => !s)} aria-expanded={showFilter} className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium hover:bg-paper"><Filter className="size-4" />Scope</button>
          <button onClick={clear} disabled={!messages.length} className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium hover:bg-paper disabled:opacity-40"><Trash2 className="size-4" /><span className="hidden sm:inline">Clear chat</span><span className="sm:hidden sr-only">Clear chat</span></button>
        </div>
      </div>

      {showFilter && (
        <div className="max-h-64 overflow-y-auto border-b border-line bg-paper px-4 py-3 sm:px-8">
          {ready.length === 0 ? <p className="text-sm text-muted">No ready documents to choose from.</p> : (
            <>
              <p className="mb-2 text-sm text-muted">Tick documents to limit the search. Leave all unticked to search everything.</p>
              <DocumentList documents={ready} limit={ready.length} selectable selected={selected} onToggle={toggle} />
            </>
          )}
        </div>
      )}

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6 sm:px-8" aria-live="polite">
        <div className="mx-auto max-w-3xl space-y-6">
          {messages.length === 0 && (
            ready.length === 0 ? (
              <EmptyState icon={BookOpen} title="Upload something to read" action={<Link to="/documents" className={btnPrimary}>Upload a document</Link>}>
                Once a document is ready, ask a question and every answer will point back to the page, row or passage it came from.
              </EmptyState>
            ) : (
              <EmptyState icon={BookOpen} title="Ask your documents anything">
                Try "What were the key findings?", "Summarise the risks mentioned", or "Which region had the highest revenue?"
              </EmptyState>
            )
          )}
          {messages.map((m) => <ChatMessage key={m.id} message={m} onRetry={m.error ? () => retry(m) : undefined} />)}
          {pending && (
            <div className="flex items-center gap-1.5 text-muted" role="status" aria-label="Searching your documents">
              <span className="dot size-2 rounded-full bg-current" /><span className="dot size-2 rounded-full bg-current [animation-delay:.2s]" /><span className="dot size-2 rounded-full bg-current [animation-delay:.4s]" />
              <span className="ml-2 text-sm">Reading your documents…</span>
            </div>
          )}
          <div ref={end} />
        </div>
      </div>

      <form onSubmit={submit} className="border-t border-line bg-surface px-4 py-3 sm:px-8">
        <div className="mx-auto flex max-w-3xl items-end gap-2">
          <label htmlFor="q" className="sr-only">Your question</label>
          <textarea
            id="q" rows={1} value={text} maxLength={2000} disabled={ready.length === 0}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) submit(e); }}
            placeholder={ready.length ? "Ask a question about your documents" : "Upload a document first"}
            className="max-h-40 min-h-[44px] flex-1 resize-none rounded-xl border border-line bg-paper px-4 py-2.5 placeholder:text-muted disabled:opacity-60"
          />
          <button type="submit" disabled={!text.trim() || pending || ready.length === 0} className={`${btnPrimary} size-11 !rounded-xl !p-0`} aria-label="Send question"><ArrowUp className="size-5" /></button>
        </div>
      </form>
    </div>
  );
}
