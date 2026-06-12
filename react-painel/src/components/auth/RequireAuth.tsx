"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { FullPageSpinner } from "@/components/common/FullPageSpinner";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    if (isLoading || isAuthenticated) return;
    const next = encodeURIComponent(pathname + (searchParams.toString() ? `?${searchParams}` : ""));
    router.replace(`/login?next=${next}`);
  }, [isLoading, isAuthenticated, pathname, searchParams, router]);

  if (isLoading || !isAuthenticated) return <FullPageSpinner />;

  return <>{children}</>;
}
