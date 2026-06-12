"use client";

import Link from "next/link";
import {
  Box,
  chakra,
  Flex,
  Skeleton,
  Stack,
  Text,
} from "@chakra-ui/react";
import type { Patient } from "@/types/api";

const ChakraLink = chakra(Link);

function formatRelative(dateStr: string | null): string {
  if (!dateStr) return "—";
  const diffMs = Date.now() - new Date(dateStr).getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  if (diffMin < 60) return `há ${diffMin} min`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `há ${diffH}h`;
  return `há ${Math.floor(diffH / 24)}d`;
}

function calcBmi(weightKg: number | null, heightCm: number | null): string {
  if (!weightKg || !heightCm) return "—";
  const bmi = weightKg / Math.pow(heightCm / 100, 2);
  return bmi.toFixed(1);
}

function PatientRowSkeleton() {
  return (
    <Flex px={4} py={3} gap={4} borderTopWidth="1px" borderColor="border">
      <Skeleton h={4} flex={2} borderRadius="md" />
      <Skeleton h={4} flex={2} borderRadius="md" />
      <Skeleton h={4} w={12} borderRadius="md" />
      <Skeleton h={4} w={12} borderRadius="md" />
      <Skeleton h={4} w={12} borderRadius="md" />
    </Flex>
  );
}

interface PatientTableProps {
  patients: Patient[];
  isLoading: boolean;
}

export function PatientTable({ patients, isLoading }: PatientTableProps) {
  return (
    <Box bg="bg" borderRadius="xl" borderWidth="1px" borderColor="border" shadow="card">
      {/* Header */}
      <Flex
        px={4}
        py={2}
        bg="bg.subtle"
        borderBottomWidth="1px"
        borderColor="border"
        borderTopRadius="xl"
        gap={4}
      >
        <Text fontSize="xs" fontWeight="semibold" color="fg.muted" flex={2}>
          Nome
        </Text>
        <Text fontSize="xs" fontWeight="semibold" color="fg.muted" flex={2}>
          Último atend.
        </Text>
        <Text fontSize="xs" fontWeight="semibold" color="fg.muted" w={12} textAlign="center">
          Consultas
        </Text>
        <Text fontSize="xs" fontWeight="semibold" color="fg.muted" w={16} textAlign="center">
          Peso
        </Text>
        <Text fontSize="xs" fontWeight="semibold" color="fg.muted" w={12} textAlign="center">
          IMC
        </Text>
      </Flex>

      {isLoading && patients.length === 0 ? (
        <Stack gap={0}>
          {[1, 2, 3].map((i) => (
            <PatientRowSkeleton key={i} />
          ))}
        </Stack>
      ) : patients.length === 0 ? (
        <Text p={6} color="fg.muted" textAlign="center">
          Nenhum paciente ainda. Inicie uma consulta no chat!
        </Text>
      ) : (
        <Stack gap={0}>
          {patients.map((p, idx) => (
            <ChakraLink
              key={p.id}
              href={`/patients/${p.id}`}
              display="flex"
              alignItems="center"
              px={4}
              py={3}
              gap={4}
              borderTopWidth={idx > 0 ? "1px" : "0"}
              borderColor="border"
              _hover={{ bg: "bg.subtle" }}
              textDecoration="none"
              color="fg"
            >
              <Text fontWeight="medium" flex={2} truncate>
                {p.first_name}
              </Text>
              <Text fontSize="sm" color="fg.muted" flex={2}>
                {formatRelative(p.last_seen_at)}
              </Text>
              <Text fontSize="sm" color="fg.muted" w={12} textAlign="center">
                {p.conversation_count}
              </Text>
              <Text fontSize="sm" color="fg.muted" w={16} textAlign="center">
                {p.latest_weight_kg ? `${p.latest_weight_kg} kg` : "—"}
              </Text>
              <Text fontSize="sm" color="fg.muted" w={12} textAlign="center">
                {calcBmi(p.latest_weight_kg, p.height_cm)}
              </Text>
            </ChakraLink>
          ))}
        </Stack>
      )}
    </Box>
  );
}
