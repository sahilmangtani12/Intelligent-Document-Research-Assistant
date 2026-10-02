import axios from "axios";

const http = axios.create({ baseURL: import.meta.env.VITE_API_URL || "", timeout: 60000 });

/** Turn any axios failure into a user-readable message. */
export function errorMessage(err) {
  if (err?.response?.data?.error?.message) {
    const { message, details } = err.response.data.error;
    return details?.length ? `${message} ${details[0].message}` : message;
  }
  if (err?.code === "ECONNABORTED") return "The request timed out. Please try again.";
  if (err?.request && !err.response) return "Can't reach the server. Check your connection and that the backend is running.";
  return "Something went wrong. Please try again.";
}

export const api = {
  listDocuments: () => http.get("/api/documents").then((r) => r.data),
  uploadDocument: (file, onProgress) => {
    const form = new FormData();
    form.append("file", file);
    return http
      .post("/api/documents/upload", form, {
        timeout: 120000,
        onUploadProgress: (e) => e.total && onProgress?.(Math.round((e.loaded / e.total) * 100)),
      })
      .then((r) => r.data);
  },
  deleteDocument: (id) => http.delete(`/api/documents/${id}`),
  documentChunks: (id, limit = 50, offset = 0) =>
    http.get(`/api/documents/${id}/sources`, { params: { limit, offset } }).then((r) => r.data),
  stats: () => http.get("/api/stats").then((r) => r.data),
  query: (question, documentIds) =>
    http
      .post("/api/query", { question, document_ids: documentIds?.length ? documentIds : undefined }, { timeout: 90000 })
      .then((r) => r.data),
};
