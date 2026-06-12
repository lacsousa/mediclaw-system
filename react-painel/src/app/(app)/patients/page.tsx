"use client";

import { useEffect } from "react";
import { Button, Flex, Heading, Text } from "@chakra-ui/react";
import { PageShell } from "@/components/layout/PageShell";
import { usePatients } from "@/hooks/usePatients";
import { PatientTable } from "@/components/patients/PatientTable";

export default function PatientsPage() {
  const { patients, isLoading, hasMore, error, fetchPatients } = usePatients();

  useEffect(() => {
    fetchPatients(true);
  }, [fetchPatients]);

  return (
    <PageShell>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg">Meus Pacientes</Heading>
      </Flex>

      {error && (
        <Text color="red.500" mb={4} fontSize="sm">
          {error}
        </Text>
      )}

      <PatientTable patients={patients} isLoading={isLoading} />

      {hasMore && (
        <Flex justify="center" mt={4}>
          <Button variant="outline" loading={isLoading} onClick={() => fetchPatients(false)}>
            Carregar mais
          </Button>
        </Flex>
      )}
    </PageShell>
  );
}
