"use client";

import { Suspense } from "react";
import { RequireAuth } from "@/components/auth/RequireAuth";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={null}>
      <RequireAuth>{children}</RequireAuth>
    </Suspense>
  );
}
