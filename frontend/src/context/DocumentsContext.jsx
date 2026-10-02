import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, errorMessage } from "../api/client";
import { useToast } from "./ToastContext";

const Ctx = createContext(null);
export const useDocuments = () => useContext(Ctx);

export function DocumentsProvider({ children }) {
  const toast = useToast();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [uploads, setUploads] = useState([]); // in flight: {id, name, progress}
  const [statsVersion, setStatsVersion] = useState(0);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await api.listDocuments());
      setLoadError(null);
    } catch (e) {
      setLoadError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  // Poll while any document is still being embedded.
  const hasProcessing = documents.some((d) => d.status === "processing");
  useEffect(() => {
    if (!hasProcessing) return;
    const t = setInterval(() => { refresh().then(() => setStatsVersion((v) => v + 1)); }, 2000);
    return () => clearInterval(t);
  }, [hasProcessing, refresh]);

  const upload = useCallback(async (files) => {
    for (const file of files) {
      const id = crypto.randomUUID();
      setUploads((u) => [...u, { id, name: file.name, progress: 0 }]);
      try {
        await api.uploadDocument(file, (p) => setUploads((u) => u.map((x) => (x.id === id ? { ...x, progress: p } : x))));
        toast.success(`${file.name} uploaded. Indexing now.`);
        await refresh();
        setStatsVersion((v) => v + 1);
      } catch (e) {
        toast.error(`${file.name}: ${errorMessage(e)}`);
      } finally {
        setUploads((u) => u.filter((x) => x.id !== id));
      }
    }
  }, [refresh, toast]);

  const remove = useCallback(async (doc) => {
    try {
      await api.deleteDocument(doc.id);
      setDocuments((d) => d.filter((x) => x.id !== doc.id));
      setStatsVersion((v) => v + 1);
      toast.success(`${doc.filename} deleted.`);
    } catch (e) {
      toast.error(errorMessage(e));
    }
  }, [toast]);

  const bumpStats = useCallback(() => setStatsVersion((v) => v + 1), []);

  const value = useMemo(
    () => ({ documents, loading, loadError, uploads, upload, remove, refresh, statsVersion, bumpStats }),
    [documents, loading, loadError, uploads, upload, remove, refresh, statsVersion, bumpStats]
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
