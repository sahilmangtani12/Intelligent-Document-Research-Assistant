import { useRef, useState } from "react";
import { UploadCloud, Loader2 } from "lucide-react";
import { useDocuments } from "../context/DocumentsContext";
import { useToast } from "../context/ToastContext";
import { ACCEPT_ATTR } from "../utils/format";

const OK = /\.(pdf|txt|csv)$/i;

export default function UploadZone({ compact = false }) {
  const { upload, uploads } = useDocuments();
  const toast = useToast();
  const input = useRef(null);
  const [over, setOver] = useState(false);

  const handle = (fileList) => {
    const files = Array.from(fileList || []);
    const valid = files.filter((f) => OK.test(f.name));
    files.filter((f) => !OK.test(f.name)).forEach((f) => toast.error(`${f.name}: only PDF, TXT and CSV files are supported.`));
    if (valid.length) upload(valid);
    if (input.current) input.current.value = "";
  };

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); handle(e.dataTransfer.files); }}
        className={`rounded-xl border-2 border-dashed transition-colors ${over ? "border-navy bg-navy/5" : "border-line bg-surface"} ${compact ? "p-5" : "p-8 sm:p-10"} text-center`}
      >
        <UploadCloud className="mx-auto mb-3 size-8 text-navy" aria-hidden="true" />
        <p className="font-medium">Drag files here, or</p>
        <button type="button" onClick={() => input.current?.click()} className="mt-2 rounded-lg bg-navy px-4 py-2 text-sm font-medium text-white hover:opacity-90 dark:text-[#0f151d]">
          Choose files
        </button>
        <input ref={input} type="file" multiple accept={ACCEPT_ATTR} className="sr-only" aria-label="Upload documents" onChange={(e) => handle(e.target.files)} />
        <p className="mt-3 text-xs text-muted">PDF, TXT or CSV · up to 15 MB each</p>
      </div>

      {uploads.length > 0 && (
        <ul className="mt-3 space-y-2" aria-label="Uploads in progress">
          {uploads.map((u) => (
            <li key={u.id} className="rounded-lg border border-line bg-surface px-4 py-3">
              <div className="mb-1.5 flex items-center justify-between gap-3 text-sm">
                <span className="flex min-w-0 items-center gap-2"><Loader2 className="size-4 shrink-0 animate-spin text-navy" /><span className="truncate">{u.name}</span></span>
                <span className="text-muted tabular-nums">{u.progress < 100 ? `${u.progress}%` : "Processing…"}</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-line" role="progressbar" aria-valuenow={u.progress} aria-valuemin={0} aria-valuemax={100}>
                <div className="h-full bg-navy transition-all" style={{ width: `${u.progress}%` }} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
