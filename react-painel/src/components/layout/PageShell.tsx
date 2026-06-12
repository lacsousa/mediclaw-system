"use client";

import { useState } from "react";
import { Box, Flex } from "@chakra-ui/react";
import {
  DrawerBackdrop,
  DrawerCloseTrigger,
  DrawerContent,
  DrawerPositioner,
  DrawerRoot,
} from "@chakra-ui/react";
import { SidebarContent } from "./Sidebar";
import { TopBar } from "./TopBar";

const SIDEBAR_W = "240px";

export function PageShell({ children }: { children: React.ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <Flex minH="100dvh">
      {/* Desktop sidebar */}
      <Box
        display={{ base: "none", md: "flex" }}
        flexDir="column"
        w={SIDEBAR_W}
        flexShrink={0}
        borderRightWidth="1px"
        borderColor="border"
        bg="bg"
        shadow="sm"
        position="fixed"
        top={0}
        left={0}
        bottom={0}
        zIndex={10}
      >
        <SidebarContent />
      </Box>

      {/* Mobile drawer */}
      <DrawerRoot open={drawerOpen} onOpenChange={(e) => setDrawerOpen(e.open)} placement="start">
        <DrawerBackdrop />
        <DrawerPositioner>
          <DrawerContent w={SIDEBAR_W} maxW={SIDEBAR_W}>
            <DrawerCloseTrigger />
            <SidebarContent />
          </DrawerContent>
        </DrawerPositioner>
      </DrawerRoot>

      {/* Main area */}
      <Flex flex={1} direction="column" ml={{ base: 0, md: SIDEBAR_W }} minW={0}>
        <Box position="sticky" top={0} zIndex={9}>
          <TopBar showMenuButton={true} onMenuClick={() => setDrawerOpen(true)} />
        </Box>
        <Box as="main" flex={1} p={{ base: 4, md: 6 }} bg="bg.subtle" overflowY="auto">
          {children}
        </Box>
      </Flex>
    </Flex>
  );
}
