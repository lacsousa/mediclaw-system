"use client";

import { useEffect } from "react";
import { Box, Grid, Heading, Stat, Text } from "@chakra-ui/react";
import { FullPageSpinner } from "@/components/common/FullPageSpinner";
import { PageShell } from "@/components/layout/PageShell";
import { RequireAdmin } from "@/components/auth/RequireAdmin";
import { useAdminMetrics } from "@/hooks/useAdminMetrics";

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <Box bg="bg" p={6} borderRadius="lg" borderWidth="1px" borderColor="border">
      <Stat.Root>
        <Stat.Label>{label}</Stat.Label>
        <Stat.ValueText fontSize="3xl" fontWeight="bold" color="fg">
          {value}
        </Stat.ValueText>
      </Stat.Root>
    </Box>
  );
}

function MetricsContent() {
  const { metrics, isLoading, fetchMetrics } = useAdminMetrics();

  useEffect(() => {
    void fetchMetrics();
  }, [fetchMetrics]);

  if (isLoading || !metrics) {
    return <FullPageSpinner />;
  }

  return (
    <PageShell>
      <Box mb={6}>
        <Heading size="lg" mb={2}>
          Métricas da Plataforma
        </Heading>
        <Text color="fg.muted">Visão geral de uso da aplicação.</Text>
      </Box>

      <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)", xl: "repeat(3, 1fr)" }} gap={6}>
        <MetricCard label="Usuários" value={metrics.users_total} />
        <MetricCard label="Conversas" value={metrics.conversations_total} />
        <MetricCard label="Mensagens hoje" value={metrics.messages_today} />
        <MetricCard label="Tokens hoje" value={metrics.tokens_today} />
        <MetricCard label="Bloqueios hoje" value={metrics.guardrail_blocks_today} />
        <MetricCard label="Docs indexados" value={metrics.kb_documents_indexed} />
      </Grid>
    </PageShell>
  );
}

export default function AdminMetricsPage() {
  return (
    <RequireAdmin>
      <MetricsContent />
    </RequireAdmin>
  );
}
