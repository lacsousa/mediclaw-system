"use client";

import { createContext, useContext } from "react";
import {
  createToaster,
  Toaster,
  ToastCloseTrigger,
  ToastDescription,
  ToastIndicator,
  ToastRoot,
  ToastTitle,
} from "@chakra-ui/react";
import { Stack } from "@chakra-ui/react";

type ToastStatus = "success" | "error" | "info" | "warning";

interface ToastContextValue {
  showToast: (message: string, status: ToastStatus) => void;
}

export const toaster = createToaster({ placement: "top-end", pauseOnPageIdle: true });

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  function showToast(message: string, status: ToastStatus) {
    toaster.create({ type: status, title: message });
  }

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <Toaster toaster={toaster}>
        {(toast) => (
          <ToastRoot key={toast.id}>
            <ToastIndicator />
            <Stack gap="1" flex="1" maxW="100%">
              {toast.title && <ToastTitle>{toast.title}</ToastTitle>}
              {toast.description && <ToastDescription>{toast.description}</ToastDescription>}
            </Stack>
            <ToastCloseTrigger />
          </ToastRoot>
        )}
      </Toaster>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
