"use client";

import { useCallback, useState } from "react";
import { api } from "@/lib/api";
import type { AdminMetrics } from "@/types/api";

export function useAdminMetrics() {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchMetrics = useCallback(async () => {
    setIsLoading(true);

    try {
      const res = await api.get<AdminMetrics>("/api/v1/admin/metrics/");
      setMetrics(res.data);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    metrics,
    isLoading,
    fetchMetrics,
  };
}
