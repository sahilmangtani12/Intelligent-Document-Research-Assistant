import { createContext, useCallback, useContext, useState } from "react";
import { CheckCircle2, AlertCircle, X } from "lucide-react";

const ToastContext = createContext(null);
export const useToast = () => useContext(ToastContext);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const dismiss = useCallback((id) => setToasts((t) => t.filter((x) => x.id !== id)), []);
  const push = useCallback(
    (message, kind = "success") => {
      const id = crypto.randomUUID();
      setToasts((t) => [...t, { id, message, kind }]);
      setTimeout(() => dismiss(id), 5000);
    },
    [dismiss]
  );
  const value = { success: (m) => push(m, "success"), error: (m) => push(m, "error") };
  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed bottom-4 right-4 left-4 sm:left-auto z-50 flex flex-col gap-2 sm:w-96" role="status" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className="flex items-start gap-3 rounded-lg border border-line bg-surface p-3 shadow-lg">
            {t.kind === "error" ? <AlertCircle className="mt-0.5 size-5 shrink-0 text-red-500" /> : <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-emerald-500" />}
            <p className="flex-1 text-sm">{t.message}</p>
            <button onClick={() => dismiss(t.id)} aria-label="Dismiss notification" className="text-muted hover:text-ink"><X className="size-4" /></button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
