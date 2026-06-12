"use client";

import Link from "next/link";
import { Box, chakra, HStack, Stack, Text } from "@chakra-ui/react";
import type { ConversationSummary } from "@/types/api";

const ChakraLink = chakra(Link);

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

interface PatientConversationsProps {
  conversations: ConversationSummary[];
}

export function PatientConversations({ conversations }: PatientConversationsProps) {
  return (
    <Box mb={6}>
      <Text fontWeight="semibold" fontSize="sm" color="fg.muted" textTransform="uppercase" letterSpacing="wider" mb={3}>
        Consultas ({conversations.length})
      </Text>

      {conversations.length === 0 ? (
        <Text color="fg.muted" fontSize="sm">
          Nenhuma consulta registrada.
        </Text>
      ) : (
        <Box bg="bg" borderRadius="xl" borderWidth="1px" borderColor="border" shadow="card">
          <Stack gap={0}>
            {conversations.map((conv, idx) => (
              <HStack
                key={conv.id}
                px={4}
                py={3}
                borderTopWidth={idx > 0 ? "1px" : "0"}
                borderColor="border"
              >
                <Box flex={1} minW={0}>
                  <Text fontSize="sm" color="fg.muted">
                    {formatDate(conv.created_at)}
                  </Text>
                  <Text fontWeight="medium" truncate>
                    {conv.title || "Consulta"}
                  </Text>
                </Box>
                <ChakraLink
                  href={`/chat/${conv.id}`}
                  fontSize="sm"
                  color="teal.fg"
                  fontWeight="medium"
                  textDecoration="none"
                  _hover={{ textDecoration: "underline" }}
                >
                  Abrir →
                </ChakraLink>
              </HStack>
            ))}
          </Stack>
        </Box>
      )}
    </Box>
  );
}
