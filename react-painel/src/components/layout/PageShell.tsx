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

const SIDEBAR_W_EXPANDED = "220px";
const SIDEBAR_W_COLLAPSED = "52px";

export function PageShell({ children }: { children: React.ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  const sidebarW = collapsed ? SIDEBAR_W_COLLAPSED : SIDEBAR_W_EXPANDED;

  return (
    <Flex minH="100dvh">
      {/* Desktop sidebar */}
      <Box
        display={{ base: "none", md: "flex" }}
        flexDir="column"
        flexShrink={0}
        position="fixed"
        top={0}
        left={0}
        bottom={0}
        zIndex={10}
        style={{
          width: sidebarW,
          transition: "width 0.22s cubic-bezier(.4,0,.2,1)",
        }}
      >
        <SidebarContent collapsed={collapsed} onToggle={() => setCollapsed((v) => !v)} />
      </Box>

      {/* Mobile drawer */}
      <DrawerRoot open={drawerOpen} onOpenChange={(e) => setDrawerOpen(e.open)} placement="start">
        <DrawerBackdrop />
        <DrawerPositioner>
          <DrawerContent w={SIDEBAR_W_EXPANDED} maxW={SIDEBAR_W_EXPANDED}>
            <DrawerCloseTrigger />
            <SidebarContent collapsed={false} onToggle={() => setDrawerOpen(false)} />
          </DrawerContent>
        </DrawerPositioner>
      </DrawerRoot>

      {/* Main area */}
      <Flex
        flex={1}
        direction="column"
        minW={0}
        ml={{ base: 0, md: sidebarW }}
        style={{ transition: "margin-left 0.22s cubic-bezier(.4,0,.2,1)" }}
      >
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
