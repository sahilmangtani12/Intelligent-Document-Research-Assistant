import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { FileTypeIcon } from "./ui";

/** A source styled as a margin note: numbered to match the [n] marks in the answer. */
export default function SourceCard({ source, onOpen, highlighted }) {
  const [open, setOpen] = useState(false);
  const preview = source.text.length > 220 && !open ? source.text.slice(0, 220).trimEnd() + "…" : source.text;
  return (
    <li id={`source-${source.index}`} className={`rounded-lg border-l-4 bg-cite-soft/60 py-3 pl-4 pr-3 transition-colors ${highlighted ? "border-cite bg-cite-soft" : "border-cite/50"}`}>
      <div className="flex items-start gap-3">
        <FileTypeIcon type={source.file_type} className="!size-8" />
        <div className="min-w-0 flex-1">
          <p className="flex flex-wrap items-baseline gap-x-2 text-sm">
            <span className="font-semibold text-cite">[{source.index}]</span>
            <button onClick={() => onOpen(source)} className="truncate font-medium underline-offset-2 hover:underline">{source.filename}</button>
            <span className="text-muted">{source.location}</span>
          </p>
          <p className="mt-1.5 font-serif text-[15px] leading-relaxed text-ink/90">{preview}</p>
          <div className="mt-2 flex items-center gap-4 text-xs text-muted">
            {source.text.length > 220 && (
              <button onClick={() => setOpen((o) => !o)} className="inline-flex items-center gap-1 hover:text-ink" aria-expanded={open}>
                <ChevronDown className={`size-3.5 transition-transform ${open ? "rotate-180" : ""}`} />{open ? "Show less" : "Show full passage"}
              </button>
            )}
            <span title="Cosine similarity between your question and this passage">Match {Math.round(source.score * 100)}%</span>
          </div>
        </div>
      </div>
    </li>
  );
}
