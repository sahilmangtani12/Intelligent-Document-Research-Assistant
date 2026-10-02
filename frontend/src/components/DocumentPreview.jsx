import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import Modal from "./Modal";
import { ErrorBanner } from "./ui";
import { api, errorMessage } from "../api/client";

const PAGE = 20;

export default function DocumentPreview({ document, onClose }) {
  const [chunks, setChunks] = useState([]);
  const [total, setTotal] = useState(document.chunk_count);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async (offset) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.documentChunks(document.id, PAGE, offset);
      setChunks((c) => (offset === 0 ? res.chunks : [...c, ...res.chunks]));
      setTotal(res.total_chunks);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { load(0); /* eslint-disable-next-line */ }, [document.id]);

  return (
    <Modal title={document.filename} subtitle={`${total} indexed passages`} onClose={onClose}>
      {error && <ErrorBanner onRetry={() => load(chunks.length)}>{error}</ErrorBanner>}
      <ol className="space-y-3">
        {chunks.map((c) => (
          <li key={c.chunk_id} className="rounded-lg border border-line p-3">
            <p className="mb-1 text-xs font-medium text-cite">{c.location}</p>
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{c.text}</p>
          </li>
        ))}
      </ol>
      {loading && <div className="flex justify-center py-6"><Loader2 className="size-5 animate-spin text-muted" /></div>}
      {!loading && chunks.length < total && (
        <button onClick={() => load(chunks.length)} className="mx-auto mt-4 block rounded-lg border border-line px-4 py-2 text-sm font-medium hover:bg-paper">Load more</button>
      )}
    </Modal>
  );
}
