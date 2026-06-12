"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { FullPageSpinner } from "@/components/common/FullPageSpinner";

export function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    if (user?.role !== "ADMIN") {
      router.replace("/chat");
    }
  }, [isLoading, user, router]);

  if (isLoading || user?.role !== "ADMIN") return <FullPageSpinner />;

  return <>{children}</>;
}
