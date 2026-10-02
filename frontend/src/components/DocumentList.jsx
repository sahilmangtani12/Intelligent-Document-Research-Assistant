import { useState } from "react";
import { Trash2, Eye } from "lucide-react";
import { useDocuments } from "../context/DocumentsContext";
import { FileTypeIcon, StatusBadge } from "./ui";
import { formatBytes, timeAgo } from "../utils/format";
import DocumentPreview from "./DocumentPreview";

function unitLabel(d) {
  if (d.file_type === "pdf") return `${d.unit_count} page${d.unit_count === 1 ? "" : "s"}`;
  if (d.file_type === "csv") return `${d.unit_count.toLocaleString()} rows`;
  return "Text";
}

export default function DocumentList({ documents, limit, selectable, selected = [], onToggle }) {
  const { remove } = useDocuments();
  const [confirmId, setConfirmId] = useState(null);
  const [preview, setPreview] = useState(null);
  const items = limit ? documents.slice(0, limit) : documents;

  return (
    <>
      <ul className="divide-y divide-line overflow-hidden rounded-xl border border-line bg-surface">
        {items.map((d) => (
          <li key={d.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
            {selectable && (
              <input type="checkbox" className="size-4 accent-[var(--color-navy)]" disabled={d.status !== "ready"} checked={selected.includes(d.id)} onChange={() => onToggle(d.id)} aria-label={`Search in ${d.filename}`} />
            )}
            <FileTypeIcon type={d.file_type} />
            <div className="min-w-0 flex-1 basis-48">
              <p className="truncate font-medium" title={d.filename}>{d.filename}</p>
              <p className="text-xs text-muted">
                {formatBytes(d.size_bytes)} · {unitLabel(d)}{d.status === "ready" && ` · ${d.chunk_count} passages`} · {timeAgo(d.created_at)}
              </p>
              {d.status === "failed" && d.error && <p className="mt-1 text-xs text-red-600 dark:text-red-400">{d.error}</p>}
            </div>
            <StatusBadge status={d.status} error={d.error} />
            {!limit && (
              <div className="flex items-center gap-1">
                {d.status === "ready" && (
                  <button onClick={() => setPreview(d)} className="rounded-md p-2 text-muted hover:bg-paper hover:text-ink" aria-label={`View passages in ${d.filename}`}><Eye className="size-4" /></button>
                )}
                {confirmId === d.id ? (
                  <span className="flex items-center gap-2 text-sm">
                    <button onClick={() => { remove(d); setConfirmId(null); }} className="rounded-md bg-red-600 px-2.5 py-1 text-white hover:bg-red-700">Delete</button>
                    <button onClick={() => setConfirmId(null)} className="text-muted hover:text-ink">Cancel</button>
                  </span>
                ) : (
                  <button onClick={() => setConfirmId(d.id)} className="rounded-md p-2 text-muted hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40" aria-label={`Delete ${d.filename}`}><Trash2 className="size-4" /></button>
                )}
              </div>
            )}
          </li>
        ))}
      </ul>
      {preview && <DocumentPreview document={preview} onClose={() => setPreview(null)} />}
    </>
  );
}
