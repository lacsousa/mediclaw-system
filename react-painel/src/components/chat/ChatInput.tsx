"use client";

import { useEffect, useRef, useState } from "react";
import { Box, Button, Flex, Stack, Text, Textarea } from "@chakra-ui/react";
import { openStream } from "@/lib/sse";
import { useToast } from "@/context/ToastContext";
import type { Citation } from "@/types/api";
import { SourceAttribution } from "./SourceAttribution";
import { MessageContent } from "./MessageContent";

interface ChatInputProps {
  conversationId: number;
  onStreamComplete: () => void;
  onPatientIdentified?: (patientId: number, firstName: string) => void;
}

export function ChatInput({
  conversationId,
  onStreamComplete,
  onPatientIdentified,
}: ChatInputProps) {
  const { showToast } = useToast();
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [optimisticUserMsg, setOptimisticUserMsg] = useState("");
  const [partialReply, setPartialReply] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const cleanupRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    return () => cleanupRef.current?.();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const prompt = input.trim();
    setInput("");
    setIsStreaming(true);
    setOptimisticUserMsg(prompt);
    setPartialReply("");
    setCitations([]);

    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : "";
    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/conversations/${conversationId}/stream/?prompt=${encodeURIComponent(prompt)}&token=${token ?? ""}`;

    let isDone = false;

    const resetStreamingUi = () => {
      setIsStreaming(false);
      setOptimisticUserMsg("");
      setPartialReply("");
      setCitations([]);
    };

    const cleanup = openStream(url, {
      onToken: (content) => setPartialReply((prev) => prev + content),
      onCitation: (citation) => setCitations((prev) => [...prev, citation]),
      onDone: (result) => {
        isDone = true;
        resetStreamingUi();
        if (result.patient_id && result.patient_first_name) {
          onPatientIdentified?.(result.patient_id, result.patient_first_name);
        }
        onStreamComplete();
      },
      onError: (error) => {
        if (isDone) return;
        resetStreamingUi();
        showToast(error.message || "Erro na conexão com o assistente.", "error");
        onStreamComplete();
      },
    });

    cleanupRef.current = cleanup;
  };

  return (
    <Box>
      {isStreaming && (
        <Stack gap={2} mb={4}>
          {optimisticUserMsg && (
            <Flex justify="flex-end">
              <Box
                bg="teal.500"
                color="white"
                px={4}
                py={3}
                borderRadius="xl"
                borderBottomRightRadius="sm"
                shadow="sm"
                maxW="75%"
              >
                <Text whiteSpace="pre-wrap">{optimisticUserMsg}</Text>
              </Box>
            </Flex>
          )}
          <Flex justify="flex-start">
            <Box maxW="75%">
              <Box
                bg="bg"
                color="fg"
                px={4}
                py={3}
                borderRadius="xl"
                borderWidth="1px"
                borderColor="border"
                shadow="card"
                borderBottomLeftRadius="sm"
              >
                <MessageContent content={partialReply} variant="assistant" streaming />
              </Box>
              <Text fontSize="xs" color="fg.muted" mt={1}>
                ℹ Esta orientação é educativa e não substitui um profissional de saúde.
              </Text>
              <SourceAttribution citations={citations} />
            </Box>
          </Flex>
        </Stack>
      )}

      <form onSubmit={handleSubmit}>
        <Flex
          gap={2}
          p={2}
          bg="bg"
          borderWidth="1px"
          borderColor="border"
          borderRadius="xl"
          shadow="card"
          align="flex-end"
        >
          <Textarea
            flex={1}
            rows={2}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Digite sua mensagem..."
            disabled={isStreaming}
            border="none"
            _focusVisible={{ boxShadow: "none" }}
            resize="none"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e as unknown as React.FormEvent);
              }
            }}
          />
          <Button
            type="submit"
            colorPalette="teal"
            borderRadius="lg"
            disabled={isStreaming || !input.trim()}
            alignSelf="flex-end"
          >
            Enviar
          </Button>
        </Flex>
      </form>
    </Box>
  );
}
