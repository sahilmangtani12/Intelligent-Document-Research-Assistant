import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FolderOpen, MessagesSquare, FileCheck2 } from "lucide-react";
import { api, errorMessage } from "../api/client";
import { useDocuments } from "../context/DocumentsContext";
import DocumentList from "../components/DocumentList";
import UploadZone from "../components/UploadZone";
import { EmptyState, ErrorBanner, PageHeader, btnPrimary } from "../components/ui";

function Stat({ label, value, hint }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <dt className="text-sm text-muted">{label}</dt>
      <dd className="mt-1 font-serif text-3xl font-medium tabular-nums">{value}</dd>
      {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
    </div>
  );
}

export default function Dashboard() {
  const { documents, loading, loadError, refresh, statsVersion } = useDocuments();
  const [stats, setStats] = useState(null);
  const [statsError, setStatsError] = useState(null);

  useEffect(() => {
    api.stats().then((s) => { setStats(s); setStatsError(null); }).catch((e) => setStatsError(errorMessage(e)));
  }, [statsVersion]);

  const answered = stats?.queries_answered ?? 0;
  const total = stats?.queries_total ?? 0;

  return (
    <div className="mx-auto max-w-5xl p-4 sm:p-8">
      <PageHeader title="Dashboard">Your documents and how they're being used.</PageHeader>
      {(loadError || statsError) && <div className="mb-4"><ErrorBanner onRetry={refresh}>{loadError || statsError}</ErrorBanner></div>}

      <dl className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Documents" value={stats?.documents_total ?? "–"} hint={stats ? `${stats.documents_processing} indexing · ${stats.documents_failed} failed` : undefined} />
        <Stat label="Searchable passages" value={stats ? stats.total_chunks.toLocaleString() : "–"} />
        <Stat label="Questions asked" value={total || (stats ? 0 : "–")} hint={total ? `${answered} answered from your documents` : undefined} />
        <Stat label="Avg. response time" value={stats?.avg_latency_ms ? `${(stats.avg_latency_ms / 1000).toFixed(1)}s` : "–"} />
      </dl>

      <div className="mt-8 grid gap-8 lg:grid-cols-3">
        <section className="lg:col-span-2" aria-labelledby="recent">
          <div className="mb-3 flex items-center justify-between">
            <h2 id="recent" className="font-serif text-xl font-medium">Recent documents</h2>
            {documents.length > 0 && <Link to="/documents" className="text-sm font-medium text-navy hover:underline">View all</Link>}
          </div>
          {loading ? (
            <div className="h-24 animate-pulse rounded-xl bg-line/60" />
          ) : documents.length === 0 ? (
            <EmptyState icon={FolderOpen} title="No documents yet" action={<Link to="/documents" className={btnPrimary}>Upload a document</Link>}>
              Upload a PDF, TXT or CSV file, then ask questions about it.
            </EmptyState>
          ) : (
            <DocumentList documents={documents} limit={5} />
          )}
        </section>

        <section aria-labelledby="quick" className="space-y-6">
          <div>
            <h2 id="quick" className="mb-3 font-serif text-xl font-medium">Add a document</h2>
            <UploadZone compact />
          </div>
          <div className="rounded-xl border border-line bg-surface p-4">
            <h3 className="flex items-center gap-2 text-sm font-semibold"><FileCheck2 className="size-4" />Supported files</h3>
            <ul className="mt-2 space-y-1 text-sm text-muted">
              <li><span className="font-medium text-ink">PDF</span> – cited by page</li>
              <li><span className="font-medium text-ink">CSV</span> – cited by row</li>
              <li><span className="font-medium text-ink">TXT</span> – cited by passage</li>
            </ul>
          </div>
          <Link to="/research" className={`${btnPrimary} w-full`}><MessagesSquare className="size-4" />Ask a question</Link>
        </section>
      </div>
    </div>
  );
}
