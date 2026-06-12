"use client";

import { useCallback, useState } from "react";
import { api } from "@/lib/api";
import type { KnowledgeDocument } from "@/types/api";

function normalizeFile(file: File): File {
  const ext = file.name.toLowerCase();

  if (ext.endsWith(".md")) {
    return new File([file], file.name, { type: "text/markdown" });
  }

  if (ext.endsWith(".txt")) {
    return new File([file], file.name, { type: "text/plain" });
  }

  return file;
}

export function useKnowledge() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);

    try {
      const res = await api.get<KnowledgeDocument[]>("/api/v1/admin/knowledge/");
      setDocuments(res.data ?? []);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const uploadDocument = useCallback(
    async (file: File) => {
      const normalized = normalizeFile(file);

      const formData = new FormData();
      formData.append("file", normalized);
      formData.append("title", normalized.name);

      try {
        await api.post("/api/v1/admin/knowledge/upload/", formData);
        await fetchDocuments();
      } catch (err: unknown) {
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (status === 401) {
          throw new Error("Sessão expirada. Tente novamente.");
        }
        throw err;
      }
    },
    [fetchDocuments]
  );

  const deleteDocument = useCallback(
    async (id: number) => {
      await api.delete(`/api/v1/admin/knowledge/${id}/`);
      await fetchDocuments();
    },
    [fetchDocuments]
  );

  return {
    documents,
    isLoading,
    fetchDocuments,
    uploadDocument,
    deleteDocument,
  };
}
