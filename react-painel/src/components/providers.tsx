"use client";

import { ChakraProvider, Theme } from "@chakra-ui/react";
import { AuthProvider } from "@/context/AuthContext";
import { ToastProvider } from "@/context/ToastContext";
import { mediclawSystem } from "@/theme/system";

type ProvidersProps = {
  children: React.ReactNode;
};

export function Providers({ children }: ProvidersProps) {
  return (
    <ChakraProvider value={mediclawSystem}>
      <Theme appearance="light" hasBackground>
        <AuthProvider>
          <ToastProvider>{children}</ToastProvider>
        </AuthProvider>
      </Theme>
    </ChakraProvider>
  );
}
