"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { FullPageSpinner } from "@/components/common/FullPageSpinner";

export function GuestOnly({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    if (isLoading || !isAuthenticated) return;
    const next = searchParams.get("next");
    router.replace(next && next.startsWith("/") ? next : "/chat");
  }, [isLoading, isAuthenticated, searchParams, router]);

  if (isLoading || isAuthenticated) return <FullPageSpinner />;

  return <>{children}</>;
}
