"use client";

import { Flex, Spinner } from "@chakra-ui/react";

export function FullPageSpinner() {
  return (
    <Flex minH="100dvh" align="center" justify="center">
      <Spinner size="xl" colorPalette="teal" />
    </Flex>
  );
}
