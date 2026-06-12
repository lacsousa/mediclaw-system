"use client";

import { useCallback, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import type { Conversation } from "@/types/api";

interface PaginatedResponse {
  results: Conversation[];
  count: number;
  next: string | null;
}

export function useConversations() {
  const { showToast } = useToast();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const pageRef = useRef(1);

  const fetchConversations = useCallback(
    async (reset = false) => {
      if (reset) pageRef.current = 1;
      setIsLoading(true);
      try {
        const res = await api.get<PaginatedResponse>(
          `/api/v1/conversations/?page=${pageRef.current}`
        );
        const { results, next } = res.data;
        setConversations((prev) => (reset ? results : [...prev, ...results]));
        setHasMore(next !== null);
        pageRef.current += 1;
      } catch {
        showToast("Erro ao carregar conversas.", "error");
      } finally {
        setIsLoading(false);
      }
    },
    [showToast]
  );

  const createConversation = async (): Promise<Conversation | null> => {
    try {
      const res = await api.post<Conversation>("/api/v1/conversations/");
      return res.data;
    } catch {
      showToast("Erro ao criar conversa.", "error");
      return null;
    }
  };

  const deleteConversation = async (id: number): Promise<boolean> => {
    try {
      await api.delete(`/api/v1/conversations/${id}/`);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      return true;
    } catch {
      showToast("Erro ao excluir conversa.", "error");
      return false;
    }
  };

  const updateConversationPatient = (
    id: number,
    patient: { id: number; first_name: string }
  ) => {
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? { ...c, patient } : c))
    );
  };

  return {
    conversations,
    isLoading,
    hasMore,
    fetchConversations,
    createConversation,
    deleteConversation,
    updateConversationPatient,
  };
}
