import { FolderOpen, Loader2 } from "lucide-react";
import { useDocuments } from "../context/DocumentsContext";
import DocumentList from "../components/DocumentList";
import UploadZone from "../components/UploadZone";
import { EmptyState, ErrorBanner, PageHeader } from "../components/ui";

export default function Documents() {
  const { documents, loading, loadError, refresh } = useDocuments();
  return (
    <div className="mx-auto max-w-4xl p-4 sm:p-8">
      <PageHeader title="Documents">Everything you upload is split into passages and made searchable.</PageHeader>
      <UploadZone />
      <section className="mt-8" aria-labelledby="all">
        <h2 id="all" className="mb-3 font-serif text-xl font-medium">Your documents{documents.length > 0 && <span className="ml-2 text-base text-muted">({documents.length})</span>}</h2>
        {loadError && <div className="mb-3"><ErrorBanner onRetry={refresh}>{loadError}</ErrorBanner></div>}
        {loading ? (
          <div className="flex justify-center py-10"><Loader2 className="size-6 animate-spin text-muted" /></div>
        ) : documents.length === 0 ? (
          <EmptyState icon={FolderOpen} title="Nothing here yet">Drop a file above to get started.</EmptyState>
        ) : (
          <DocumentList documents={documents} />
        )}
      </section>
    </div>
  );
}
