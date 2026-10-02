import { FileText, FileSpreadsheet, FileType2, Loader2, CheckCircle2, AlertTriangle } from "lucide-react";
import { typeLabel } from "../utils/format";

const ICONS = { pdf: FileType2, txt: FileText, csv: FileSpreadsheet };
const TINTS = {
  pdf: "bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300",
  txt: "bg-sky-50 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300",
  csv: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300",
};

export function FileTypeIcon({ type, className = "" }) {
  const Icon = ICONS[type] || FileText;
  return (
    <span className={`inline-flex size-10 shrink-0 items-center justify-center rounded-lg ${TINTS[type] || ""} ${className}`} title={typeLabel[type]}>
      <Icon className="size-5" aria-hidden="true" />
      <span className="sr-only">{typeLabel[type]} file</span>
    </span>
  );
}

export function StatusBadge({ status, error }) {
  const map = {
    processing: ["Indexing", "bg-amber-50 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300", <Loader2 key="i" className="size-3.5 animate-spin" />],
    ready: ["Ready", "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300", <CheckCircle2 key="i" className="size-3.5" />],
    failed: ["Failed", "bg-red-50 text-red-800 dark:bg-red-950/50 dark:text-red-300", <AlertTriangle key="i" className="size-3.5" />],
  };
  const [label, cls, icon] = map[status] || map.processing;
  return (
    <span title={error || undefined} className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {icon}{label}
    </span>
  );
}

export function EmptyState({ icon: Icon, title, children, action }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-line px-6 py-12 text-center">
      <Icon className="mb-3 size-8 text-muted" aria-hidden="true" />
      <h3 className="font-serif text-lg font-medium">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-muted">{children}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorBanner({ children, onRetry }) {
  return (
    <div role="alert" className="flex items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
      <span>{children}</span>
      {onRetry && <button onClick={onRetry} className="shrink-0 font-medium underline underline-offset-2">Retry</button>}
    </div>
  );
}

export function PageHeader({ title, children }) {
  return (
    <div className="mb-6">
      <h1 className="font-serif text-3xl font-medium tracking-tight">{title}</h1>
      {children && <p className="mt-1 text-muted">{children}</p>}
    </div>
  );
}

export const btnPrimary = "inline-flex items-center justify-center gap-2 rounded-lg bg-navy px-4 py-2 text-sm font-medium text-white dark:text-[#0f151d] hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity";
export const btnGhost = "inline-flex items-center justify-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium hover:bg-paper transition-colors";
