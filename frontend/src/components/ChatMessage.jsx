import { useState } from "react";
import { AlertCircle, SearchX } from "lucide-react";
import SourceCard from "./SourceCard";
import Modal from "./Modal";

/** Render [1] / [1][2] markers as superscript chips that jump to the matching source. */
function AnswerText({ text, onCite }) {
  const parts = text.split(/(\[\d+\])/g);
  return (
    <p className="whitespace-pre-wrap font-serif text-[17px] leading-[1.7]">
      {parts.map((p, i) => {
        const m = p.match(/^\[(\d+)\]$/);
        return m ? (
          <button key={i} onClick={() => onCite(Number(m[1]))} className="mx-0.5 -translate-y-1 rounded bg-cite-soft px-1 align-baseline text-[11px] font-semibold text-cite hover:underline" aria-label={`Go to source ${m[1]}`}>
            {m[1]}
          </button>
        ) : (
          <span key={i}>{p}</span>
        );
      })}
    </p>
  );
}

export default function ChatMessage({ message, onRetry }) {
  const [active, setActive] = useState(null);
  const [modal, setModal] = useState(null);

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-navy px-4 py-2.5 text-white dark:text-[#0f151d]">{message.text}</p>
      </div>
    );
  }

  if (message.error) {
    return (
      <div role="alert" className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950/40">
        <AlertCircle className="mt-0.5 size-5 shrink-0 text-red-600" />
        <div className="flex-1 text-sm text-red-900 dark:text-red-200">
          <p>{message.error}</p>
          {onRetry && <button onClick={onRetry} className="mt-2 font-medium underline underline-offset-2">Try again</button>}
        </div>
      </div>
    );
  }

  const jump = (n) => {
    setActive(n);
    document.getElementById(`source-${n}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

  return (
    <div className="max-w-3xl">
      {message.grounded ? (
        <AnswerText text={message.text} onCite={jump} />
      ) : (
        <div className="flex items-start gap-3 rounded-xl border border-line bg-surface p-4">
          <SearchX className="mt-0.5 size-5 shrink-0 text-muted" />
          <div>
            <p className="font-medium">{message.text}</p>
            <p className="mt-1 text-sm text-muted">Try rephrasing, or check that the right documents are uploaded and selected.</p>
          </div>
        </div>
      )}
      {message.grounded && message.sources?.length > 0 && (
        <section className="mt-4" aria-label="Sources">
          <h3 className="mb-2 text-sm font-semibold text-muted">Sources</h3>
          <ul className="space-y-2">
            {message.sources.map((s) => <SourceCard key={s.chunk_id} source={s} highlighted={active === s.index} onOpen={setModal} />)}
          </ul>
        </section>
      )}
      {modal && (
        <Modal title={modal.filename} subtitle={modal.location} onClose={() => setModal(null)}>
          <p className="whitespace-pre-wrap font-serif text-[16px] leading-relaxed">{modal.text}</p>
        </Modal>
      )}
    </div>
  );
}
