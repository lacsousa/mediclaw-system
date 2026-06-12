"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Box,
  Button,
  Flex,
  Heading,
  HStack,
  IconButton,
  Spinner,
  Stack,
  Text,
} from "@chakra-ui/react";
import { PageShell } from "@/components/layout/PageShell";
import { useConversations } from "@/hooks/useConversations";
import { DeleteConfirmModal } from "@/components/common/DeleteConfirmModal";

function formatRelative(dateStr: string): string {
  const diffMs = Date.now() - new Date(dateStr).getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  if (diffMin < 60) return `há ${diffMin} min`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `há ${diffH}h`;
  return `há ${Math.floor(diffH / 24)}d`;
}

export default function ChatPage() {
  const router = useRouter();
  const {
    conversations,
    isLoading,
    hasMore,
    fetchConversations,
    createConversation,
    deleteConversation,
  } = useConversations();

  const [isCreating, setIsCreating] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    fetchConversations(true);
  }, [fetchConversations]);

  const handleNew = async () => {
    setIsCreating(true);
    const conv = await createConversation();
    setIsCreating(false);
    if (conv) router.push(`/chat/${conv.id}`);
  };

  const confirmDelete = async () => {
    if (!deleteId) return;
    setIsDeleting(true);
    await deleteConversation(deleteId);
    setIsDeleting(false);
    setDeleteId(null);
  };

  return (
    <PageShell>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg">Minhas Conversas</Heading>
        <Button colorPalette="teal" borderRadius="lg" loading={isCreating} onClick={handleNew}>
          + Nova
        </Button>
      </Flex>

      <Box bg="bg" borderRadius="xl" borderWidth="1px" borderColor="border" shadow="card">
        {isLoading && conversations.length === 0 ? (
          <Flex justify="center" py={8}>
            <Spinner />
          </Flex>
        ) : conversations.length === 0 ? (
          <Text p={6} color="fg.muted" textAlign="center">
            Nenhuma conversa ainda. Crie uma nova!
          </Text>
        ) : (
          <Stack gap={0}>
            {conversations.map((conv, idx) => (
              <HStack
                key={conv.id}
                px={4}
                py={3}
                cursor="pointer"
                borderTopWidth={idx > 0 ? "1px" : "0"}
                borderColor="border"
                _hover={{ bg: "bg.subtle" }}
                onClick={() => router.push(`/chat/${conv.id}`)}
              >
                <Box flex={1} minW={0}>
                  <Text fontWeight="medium" truncate>
                    {conv.patient?.first_name ?? conv.title ?? "Nova conversa"}
                  </Text>
                  <Text fontSize="sm" color="fg.muted">
                    {formatRelative(conv.updated_at)}
                  </Text>
                </Box>
                <IconButton
                  aria-label="Excluir conversa"
                  size="sm"
                  variant="ghost"
                  colorPalette="red"
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteId(conv.id);
                  }}
                >
                  🗑
                </IconButton>
              </HStack>
            ))}
          </Stack>
        )}
      </Box>

      {hasMore && (
        <Flex justify="center" mt={4}>
          <Button variant="outline" loading={isLoading} onClick={() => fetchConversations(false)}>
            Carregar mais
          </Button>
        </Flex>
      )}

      <DeleteConfirmModal
        isOpen={deleteId !== null}
        onOpenChange={(d) => !d.open && setDeleteId(null)}
        onConfirm={confirmDelete}
        isDeleting={isDeleting}
        title="Excluir conversa"
        description="Tem certeza que deseja excluir esta conversa? As mensagens serão removidas."
      />
    </PageShell>
  );
}
