"use client";

import { Box, Flex, IconButton, Text } from "@chakra-ui/react";
import { useAuth } from "@/context/AuthContext";

function IconMenu() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}

interface TopBarProps {
  onMenuClick?: () => void;
  showMenuButton?: boolean;
}

export function TopBar({ onMenuClick, showMenuButton = false }: TopBarProps) {
  const { user } = useAuth();

  const initials = user ? `${user.first_name?.[0] ?? ""}`.toUpperCase() : "?";

  return (
    <Flex
      as="header"
      align="center"
      justify="space-between"
      px={{ base: 4, md: 6 }}
      h="14"
      borderBottomWidth="1px"
      borderColor="border"
      bg="bg/90"
      backdropFilter="blur(8px)"
    >
      <Flex align="center" gap={3}>
        {showMenuButton && (
          <IconButton
            aria-label="Abrir menu"
            variant="ghost"
            size="sm"
            borderRadius="lg"
            onClick={onMenuClick}
            display={{ base: "flex", md: "none" }}
          >
            <IconMenu />
          </IconButton>
        )}
        <Box display={{ base: "block", md: "none" }}>
          <Text fontWeight="bold" color="teal.fg">
            MediClaw
          </Text>
        </Box>
      </Flex>

      {user && (
        <Flex align="center" gap={2}>
          <Text fontSize="sm" color="fg.muted" display={{ base: "none", sm: "block" }}>
            {user.first_name}
          </Text>
          <Box
            style={{
              width: "30px",
              height: "30px",
              borderRadius: "50%",
              background: "#E1F5EE",
              color: "#0F6E56",
              fontSize: "12px",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
            aria-label={`Usuário: ${user.first_name}`}
          >
            {initials}
          </Box>
        </Flex>
      )}
    </Flex>
  );
}
