"use client";

import { Box, HStack, Text, VStack } from "@chakra-ui/react";
import type { PatientDetail } from "@/types/api";

const SEX_LABELS: Record<string, string> = {
  M: "Masculino",
  F: "Feminino",
  OTHER: "Outro",
};

function bmiCategory(bmi: number): string {
  if (bmi < 18.5) return "Abaixo do peso";
  if (bmi < 25) return "Peso normal";
  if (bmi < 30) return "Sobrepeso";
  if (bmi < 35) return "Obesidade grau 1";
  if (bmi < 40) return "Obesidade grau 2";
  return "Obesidade grau 3";
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("pt-BR");
}

interface PatientHeaderProps {
  patient: PatientDetail;
}

export function PatientHeader({ patient }: PatientHeaderProps) {
  const latestWeight = patient.weight_logs[0]?.value_kg ?? null;
  const bmiValue =
    latestWeight && patient.height_cm
      ? latestWeight / Math.pow(patient.height_cm / 100, 2)
      : null;

  return (
    <Box
      bg="bg"
      borderRadius="xl"
      borderWidth="1px"
      borderColor="border"
      shadow="card"
      p={5}
      mb={6}
    >
      <Text fontSize="2xl" fontWeight="bold" mb={2}>
        {patient.first_name}
      </Text>

      <HStack gap={6} flexWrap="wrap">
        <VStack align="start" gap={0}>
          <Text fontSize="xs" color="fg.muted">
            Nascimento
          </Text>
          <Text fontSize="sm">{formatDate(patient.birth_date)}</Text>
        </VStack>

        <VStack align="start" gap={0}>
          <Text fontSize="xs" color="fg.muted">
            Sexo
          </Text>
          <Text fontSize="sm">
            {patient.biological_sex ? SEX_LABELS[patient.biological_sex] : "—"}
          </Text>
        </VStack>

        <VStack align="start" gap={0}>
          <Text fontSize="xs" color="fg.muted">
            Altura
          </Text>
          <Text fontSize="sm">
            {patient.height_cm ? `${patient.height_cm} cm` : "—"}
          </Text>
        </VStack>

        {latestWeight && (
          <VStack align="start" gap={0}>
            <Text fontSize="xs" color="fg.muted">
              Peso atual
            </Text>
            <Text fontSize="sm">{latestWeight} kg</Text>
          </VStack>
        )}

        {bmiValue && (
          <VStack align="start" gap={0}>
            <Text fontSize="xs" color="fg.muted">
              IMC
            </Text>
            <Text fontSize="sm">
              {bmiValue.toFixed(1)}{" "}
              <Text as="span" fontSize="xs" color="fg.muted">
                ({bmiCategory(bmiValue)})
              </Text>
            </Text>
          </VStack>
        )}
      </HStack>
    </Box>
  );
}
