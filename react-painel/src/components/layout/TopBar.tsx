"use client";

import { Box, Button, Flex, IconButton, Text } from "@chakra-ui/react";
import { useAuth } from "@/context/AuthContext";

interface TopBarProps {
  onMenuClick?: () => void;
  showMenuButton?: boolean;
}

export function TopBar({ onMenuClick, showMenuButton = false }: TopBarProps) {
  const { user, logout } = useAuth();

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
      shadow="sm"
    >
      <Flex align="center" gap={3}>
        {showMenuButton && (
          <IconButton
            aria-label="Abrir menu"
            variant="ghost"
            size="sm"
            borderRadius="lg"
            onClick={onMenuClick}
          >
            ☰
          </IconButton>
        )}
        <Box display={{ base: "block", md: "none" }}>
          <Text fontWeight="bold" color="teal.fg">
            MediClaw
          </Text>
        </Box>
      </Flex>

      <Flex align="center" gap={3}>
        {user && (
          <Text fontSize="sm" color="fg.muted" display={{ base: "none", sm: "block" }}>
            {user.first_name}
          </Text>
        )}
        <Button size="sm" variant="outline" colorPalette="red" borderRadius="lg" onClick={logout}>
          Sair
        </Button>
      </Flex>
    </Flex>
  );
}
