"use client";

import { use, useEffect, useRef, useState } from "react";
import { Box, Flex, Heading, Spinner } from "@chakra-ui/react";
import { PageShell } from "@/components/layout/PageShell";
import { useMessages } from "@/hooks/useMessages";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import type { Message } from "@/types/api";

const GREETING_MESSAGE: Message = {
  id: 0,
  role: "ASSISTANT",
  content:
    "Olá! Sou o MediClaw, assistente de saúde preventiva com IA.\n\n" +
    "Para iniciar uma consulta, informe os dados do paciente em linguagem natural — por exemplo:\n\n" +
    "> \"Paciente: João Silva, 45 anos, 1,78 m, 82 kg, nasceu em 10/05/1980, sexo masculino. Dorme em média 6 horas por noite e caminha 30 minutos diariamente.\"\n\n" +
    "Salvo automaticamente peso, sono, atividade e refeições quando mencionados. O nome do paciente aparece na conversa assim que é identificado.\n\n" +
    "Esta orientação é educativa e não substitui consulta com profissional de saúde.",
  tokens_used: null,
  blocked_by_guardrail: false,
  metadata: {},
  created_at: "",
};

export default function ChatDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const conversationId = parseInt(id, 10);

  const { conversation, messages, isLoading, fetchMessages } = useMessages(conversationId);
  const [patientName, setPatientName] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  // Inicializa o nome do paciente a partir dos dados carregados da conversa
  useEffect(() => {
    if (conversation?.patient?.first_name) {
      setPatientName(conversation.patient.first_name);
    }
  }, [conversation]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const headingLabel = patientName
    ?? conversation?.patient?.first_name
    ?? (isLoading ? "Carregando..." : conversation?.title ?? "Nova conversa");

  return (
    <PageShell>
      <Flex direction="column" h="calc(100dvh - 120px)">
        <Heading size="md" mb={4}>
          {headingLabel}
        </Heading>

        <Box flex={1} overflowY="auto" mb={4} pr={1}>
          {isLoading ? (
            <Flex justify="center" py={8}>
              <Spinner />
            </Flex>
          ) : messages.length === 0 ? (
            <MessageBubble message={GREETING_MESSAGE} />
          ) : (
            messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
          )}
          <div ref={bottomRef} />
        </Box>

        <ChatInput
          conversationId={conversationId}
          onStreamComplete={fetchMessages}
          onPatientIdentified={(_, firstName) => setPatientName(firstName)}
        />
      </Flex>
    </PageShell>
  );
}
