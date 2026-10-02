import { useCallback, useEffect, useState } from "react";
import { api, errorMessage } from "../api/client";
import { useDocuments } from "../context/DocumentsContext";

const KEY = "chat-history-v1";
const load = () => { try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch { return []; } };

export function useChat() {
  const { bumpStats } = useDocuments();
  const [messages, setMessages] = useState(load);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    try { localStorage.setItem(KEY, JSON.stringify(messages.slice(-60))); } catch {}
  }, [messages]);

  const ask = useCallback(async (question, documentIds) => {
    const q = question.trim();
    if (!q || pending) return;
    setMessages((m) => [...m, { id: crypto.randomUUID(), role: "user", text: q }]);
    setPending(true);
    try {
      const res = await api.query(q, documentIds);
      setMessages((m) => [...m, { id: crypto.randomUUID(), role: "assistant", text: res.answer, grounded: res.grounded, sources: res.sources, latency: res.latency_ms }]);
    } catch (e) {
      setMessages((m) => [...m, { id: crypto.randomUUID(), role: "assistant", error: errorMessage(e), question: q }]);
    } finally {
      setPending(false);
      bumpStats();
    }
  }, [pending, bumpStats]);

  const clear = useCallback(() => setMessages([]), []);
  const dropMessage = useCallback((id) => setMessages((m) => m.filter((x) => x.id !== id)), []);
  return { messages, pending, ask, clear, dropMessage };
}
