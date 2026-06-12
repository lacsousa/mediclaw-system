"use client";

import { useState } from "react";
import { Box, Button, HStack, Stack, Text } from "@chakra-ui/react";
import type { ActivityLog, NutritionNote, PatientDetail, SleepLog, WeightLog } from "@/types/api";

type Tab = "weight" | "sleep" | "activity" | "nutrition";

const TABS: { key: Tab; label: string }[] = [
  { key: "weight", label: "Peso" },
  { key: "sleep", label: "Sono" },
  { key: "activity", label: "Atividade" },
  { key: "nutrition", label: "Nutrição" },
];

const SLEEP_QUALITY_COLORS: Record<string, string> = {
  low: "red",
  mid: "yellow",
  high: "green",
};

function sleepQualityColor(score: number): string {
  if (score <= 4) return SLEEP_QUALITY_COLORS.low;
  if (score <= 7) return SLEEP_QUALITY_COLORS.mid;
  return SLEEP_QUALITY_COLORS.high;
}

function formatDt(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function EmptyRow() {
  return (
    <Text p={4} color="fg.muted" fontSize="sm" textAlign="center">
      Nenhum registro.
    </Text>
  );
}

function WeightTab({ logs }: { logs: WeightLog[] }) {
  if (logs.length === 0) return <EmptyRow />;
  return (
    <Stack gap={0}>
      {logs.map((l, i) => (
        <HStack key={l.id} px={4} py={2.5} borderTopWidth={i > 0 ? "1px" : "0"} borderColor="border">
          <Text flex={1} fontSize="sm" fontWeight="medium">{l.value_kg} kg</Text>
          <Text fontSize="sm" color="fg.muted">{formatDt(l.measured_at)}</Text>
        </HStack>
      ))}
    </Stack>
  );
}

function SleepTab({ logs }: { logs: SleepLog[] }) {
  if (logs.length === 0) return <EmptyRow />;
  return (
    <Stack gap={0}>
      {logs.map((l, i) => (
        <HStack key={l.id} px={4} py={2.5} borderTopWidth={i > 0 ? "1px" : "0"} borderColor="border">
          <Text flex={1} fontSize="sm" fontWeight="medium">{l.duration_hours}h</Text>
          <Box
            px={2}
            py={0.5}
            borderRadius="md"
            fontSize="xs"
            fontWeight="semibold"
            bg={`${sleepQualityColor(l.quality_score)}.subtle`}
            color={`${sleepQualityColor(l.quality_score)}.fg`}
          >
            {l.quality_score}/10
          </Box>
          <Text fontSize="sm" color="fg.muted">{formatDt(l.started_at)}</Text>
        </HStack>
      ))}
    </Stack>
  );
}

function ActivityTab({ logs }: { logs: ActivityLog[] }) {
  if (logs.length === 0) return <EmptyRow />;
  return (
    <Stack gap={0}>
      {logs.map((l, i) => (
        <HStack key={l.id} px={4} py={2.5} borderTopWidth={i > 0 ? "1px" : "0"} borderColor="border">
          <Text flex={1} fontSize="sm" fontWeight="medium" textTransform="capitalize">{l.type}</Text>
          <Text fontSize="sm" color="fg.muted">{l.duration_min} min</Text>
          <Text fontSize="sm" color="fg.muted">{formatDt(l.performed_at)}</Text>
        </HStack>
      ))}
    </Stack>
  );
}

function NutritionTab({ notes }: { notes: NutritionNote[] }) {
  if (notes.length === 0) return <EmptyRow />;
  return (
    <Stack gap={0}>
      {notes.map((n, i) => (
        <Box key={n.id} px={4} py={2.5} borderTopWidth={i > 0 ? "1px" : "0"} borderColor="border">
          <Text fontSize="xs" color="fg.muted" mb={0.5}>{formatDt(n.logged_at)}</Text>
          <Text fontSize="sm">{n.note}</Text>
        </Box>
      ))}
    </Stack>
  );
}

interface PatientHealthTabsProps {
  patient: PatientDetail;
}

export function PatientHealthTabs({ patient }: PatientHealthTabsProps) {
  const [activeTab, setActiveTab] = useState<Tab>("weight");

  return (
    <Box>
      <Text fontWeight="semibold" fontSize="sm" color="fg.muted" textTransform="uppercase" letterSpacing="wider" mb={3}>
        Histórico de Saúde
      </Text>

      <HStack gap={2} mb={4} flexWrap="wrap">
        {TABS.map((t) => (
          <Button
            key={t.key}
            size="sm"
            variant={activeTab === t.key ? "solid" : "outline"}
            colorPalette={activeTab === t.key ? "teal" : "gray"}
            borderRadius="full"
            onClick={() => setActiveTab(t.key)}
          >
            {t.label}
          </Button>
        ))}
      </HStack>

      <Box bg="bg" borderRadius="xl" borderWidth="1px" borderColor="border" shadow="card">
        {activeTab === "weight" && <WeightTab logs={patient.weight_logs} />}
        {activeTab === "sleep" && <SleepTab logs={patient.sleep_logs} />}
        {activeTab === "activity" && <ActivityTab logs={patient.activity_logs} />}
        {activeTab === "nutrition" && <NutritionTab notes={patient.nutrition_notes} />}
      </Box>
    </Box>
  );
}
