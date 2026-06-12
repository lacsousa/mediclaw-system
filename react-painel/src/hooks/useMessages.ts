"use client";

import { useCallback, useState } from "react";
import { api } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import type { Conversation, Message } from "@/types/api";

interface ConversationDetailResponse {
  conversation: Conversation;
  messages: Message[];
}

export function useMessages(conversationId: number) {
  const { showToast } = useToast();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchMessages = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await api.get<ConversationDetailResponse>(
        `/api/v1/conversations/${conversationId}/`
      );
      setConversation(res.data.conversation);
      setMessages(res.data.messages);
    } catch {
      showToast("Erro ao carregar mensagens.", "error");
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, showToast]);

  return { conversation, messages, isLoading, fetchMessages };
}
