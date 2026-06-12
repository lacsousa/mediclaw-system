"use client";

import { useEffect, useState } from "react";
import {
  Badge,
  Box,
  Button,
  FieldRoot,
  FieldLabel,
  Heading,
  Input,
  Stack,
  Table,
  Text,
} from "@chakra-ui/react";
import { PageShell } from "@/components/layout/PageShell";
import { DeleteConfirmModal } from "@/components/common/DeleteConfirmModal";
import { useToast } from "@/context/ToastContext";
import { useKnowledge } from "@/hooks/useKnowledge";

function statusColor(status: string) {
  switch (status) {
    case "INDEXED":
      return "green";
    case "PROCESSING":
      return "yellow";
    case "ERROR":
      return "red";
    default:
      return "gray";
  }
}

export default function KnowledgePage() {
  const { showToast } = useToast();
  const { documents, isLoading, fetchDocuments, uploadDocument, deleteDocument } = useKnowledge();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    void fetchDocuments();
  }, [fetchDocuments]);

  async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    if (!selectedFile) {
      showToast("Selecione um arquivo", "error");
      return;
    }

    setIsSubmitting(true);

    try {
      await uploadDocument(selectedFile);
      setSelectedFile(null);
      showToast("Documento enviado com sucesso", "success");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao enviar documento";
      showToast(msg, "error");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function confirmDelete() {
    if (!deleteId) return;

    setIsDeleting(true);

    try {
      await deleteDocument(deleteId);
      showToast("Documento removido com sucesso", "success");
    } catch {
      showToast("Erro ao remover documento", "error");
    } finally {
      setIsDeleting(false);
      setDeleteId(null);
    }
  }

  return (
    <PageShell>
      <Box mb={6}>
        <Heading size="lg" mb={2}>
          Base de Conhecimento
        </Heading>
        <Text color="fg.muted">
          Envie PDFs, TXT ou Markdown para enriquecer as respostas do chat (RAG). A base é
          compartilhada por todos os usuários.
        </Text>
      </Box>

      <Box bg="bg" p={6} borderRadius="lg" borderWidth="1px" borderColor="border" mb={8}>
        <form onSubmit={handleUpload}>
          <Stack gap={4}>
            <FieldRoot>
              <FieldLabel>Arquivo</FieldLabel>
              <Input
                type="file"
                accept=".pdf,.txt,.md"
                onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
              />
            </FieldRoot>

            <Button type="submit" colorPalette="teal" loading={isSubmitting} maxW="220px">
              Enviar documento
            </Button>
          </Stack>
        </form>
      </Box>

      <Box bg="bg" borderRadius="lg" borderWidth="1px" borderColor="border" overflowX="auto">
        <Table.Root variant="line">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>Título</Table.ColumnHeader>
              <Table.ColumnHeader>Status</Table.ColumnHeader>
              <Table.ColumnHeader>Chunks</Table.ColumnHeader>
              <Table.ColumnHeader>Data</Table.ColumnHeader>
              <Table.ColumnHeader textAlign="right">Ações</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>

          <Table.Body>
            {isLoading ? (
              <Table.Row>
                <Table.Cell colSpan={5} textAlign="center">
                  Carregando...
                </Table.Cell>
              </Table.Row>
            ) : documents.length === 0 ? (
              <Table.Row>
                <Table.Cell colSpan={5} textAlign="center">
                  Nenhum documento encontrado.
                </Table.Cell>
              </Table.Row>
            ) : (
              documents.map((doc) => (
                <Table.Row key={doc.id}>
                  <Table.Cell>{doc.title}</Table.Cell>
                  <Table.Cell>
                    <Badge colorPalette={statusColor(doc.status)}>{doc.status}</Badge>
                  </Table.Cell>
                  <Table.Cell>{doc.chunk_count ?? "—"}</Table.Cell>
                  <Table.Cell>{new Date(doc.created_at).toLocaleString()}</Table.Cell>
                  <Table.Cell textAlign="right">
                    <Button
                      size="sm"
                      colorPalette="red"
                      variant="ghost"
                      onClick={() => setDeleteId(doc.id)}
                    >
                      Excluir
                    </Button>
                  </Table.Cell>
                </Table.Row>
              ))
            )}
          </Table.Body>
        </Table.Root>
      </Box>

      <DeleteConfirmModal
        isOpen={deleteId !== null}
        onOpenChange={(details) => !details.open && setDeleteId(null)}
        onConfirm={confirmDelete}
        isDeleting={isDeleting}
      />
    </PageShell>
  );
}
