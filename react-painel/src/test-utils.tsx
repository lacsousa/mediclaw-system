import React, { ReactNode } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { ChakraProvider, Theme } from "@chakra-ui/react";
import { mediclawSystem } from "@/theme/system";

function ChakraWrapper({ children }: { children: ReactNode }) {
  return (
    <ChakraProvider value={mediclawSystem}>
      <Theme appearance="light">{children}</Theme>
    </ChakraProvider>
  );
}

export function renderWithChakra(ui: ReactNode, options?: Omit<RenderOptions, "wrapper">) {
  return render(ui, { wrapper: ChakraWrapper, ...options });
}

export * from "@testing-library/react";
