"use client";

import { Suspense } from "react";
import { Flex } from "@chakra-ui/react";
import { GuestOnly } from "@/components/auth/GuestOnly";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={null}>
      <GuestOnly>
        <Flex minH="100dvh" align="center" justify="center" bg="teal.50" px={4} py={8}>
          {children}
        </Flex>
      </GuestOnly>
    </Suspense>
  );
}
