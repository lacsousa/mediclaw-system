"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Box, Button, Flex, Heading, Spinner, Text } from "@chakra-ui/react";
import { PageShell } from "@/components/layout/PageShell";
import { usePatient } from "@/hooks/usePatients";
import { PatientHeader } from "@/components/patients/PatientHeader";
import { PatientConversations } from "@/components/patients/PatientConversations";
import { PatientHealthTabs } from "@/components/patients/PatientHealthTabs";
import { DeleteConfirmModal } from "@/components/common/DeleteConfirmModal";
import { api } from "@/lib/api";
import { useToast } from "@/context/ToastContext";

export default function PatientDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const patientId = parseInt(id, 10);

  const router = useRouter();
  const { showToast } = useToast();
  const { patient, isLoading, notFound, fetchPatient } = usePatient(patientId);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    fetchPatient();
  }, [fetchPatient]);

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await api.delete(`/api/v1/patients/${patientId}/`);
      showToast("Paciente removido.", "success");
      router.push("/patients");
    } catch {
      showToast("Erro ao excluir paciente.", "error");
    } finally {
      setIsDeleting(false);
      setDeleteOpen(false);
    }
  };

  if (isLoading) {
    return (
      <PageShell>
        <Flex justify="center" py={16}>
          <Spinner />
        </Flex>
      </PageShell>
    );
  }

  if (notFound || !patient) {
    return (
      <PageShell>
        <Text color="fg.muted" textAlign="center" mt={16}>
          Paciente não encontrado.
        </Text>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <Flex align="center" gap={3} mb={4}>
        <Button variant="ghost" size="sm" onClick={() => router.push("/patients")}>
          ← Pacientes
        </Button>
        <Heading size="lg">{patient.first_name}</Heading>
      </Flex>

      <PatientHeader patient={patient} />

      <PatientConversations conversations={patient.conversations} />

      <PatientHealthTabs patient={patient} />

      <Box mt={8} pt={6} borderTopWidth="1px" borderColor="border">
        <Button
          colorPalette="red"
          variant="outline"
          size="sm"
          onClick={() => setDeleteOpen(true)}
        >
          Excluir paciente
        </Button>
      </Box>

      <DeleteConfirmModal
        isOpen={deleteOpen}
        onOpenChange={(d) => !d.open && setDeleteOpen(false)}
        onConfirm={handleDelete}
        isDeleting={isDeleting}
        title="Excluir paciente"
        description={`Tem certeza que deseja excluir "${patient.first_name}"? Todos os dados e conversas associados serão removidos permanentemente.`}
      />
    </PageShell>
  );
}
