"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Box, chakra, Flex, Text, VStack } from "@chakra-ui/react";
import { useAuth } from "@/context/AuthContext";

const ChakraLink = chakra(Link);

interface NavItem {
  label: string;
  href: string;
  icon: string;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  { label: "Chat IA", href: "/chat", icon: "💬" },
  { label: "Pacientes", href: "/patients", icon: "🧑‍⚕️" },
  { label: "Conhecimento", href: "/conhecimento", icon: "📚" },
];

const adminItems: NavItem[] = [
  { label: "Métricas", href: "/admin/metrics", icon: "📊", adminOnly: true },
];

function NavLink({ item }: { item: NavItem }) {
  const pathname = usePathname();
  const isActive = pathname === item.href || pathname.startsWith(item.href + "/");

  return (
    <ChakraLink
      href={item.href}
      display="flex"
      alignItems="center"
      gap={3}
      px={3}
      py={2.5}
      borderRadius="lg"
      fontWeight={isActive ? "semibold" : "medium"}
      fontSize="sm"
      bg={isActive ? "teal.subtle" : "transparent"}
      color={isActive ? "teal.fg" : "fg.muted"}
      _hover={{ bg: isActive ? "teal.subtle" : "bg.subtle", color: "fg" }}
      transition="background 0.15s ease, color 0.15s ease"
      textDecoration="none"
      w="full"
    >
      <Text as="span" fontSize="lg" lineHeight="1" aria-hidden>
        {item.icon}
      </Text>
      <Text>{item.label}</Text>
    </ChakraLink>
  );
}

export function SidebarContent() {
  const { user } = useAuth();

  return (
    <Flex direction="column" h="full" py={5} px={3} gap={2} overflowY="auto">
      <Box px={3} py={3} mb={2} borderRadius="xl" bg="teal.subtle">
        <Text fontWeight="bold" fontSize="lg" letterSpacing="tight" color="teal.fg">
          MediClaw
        </Text>
        <Text fontSize="xs" color="fg.muted" mt={0.5}>
          Assistente de saúde
        </Text>
      </Box>

      <VStack gap={1} align="stretch">
        {navItems.map((item) => (
          <NavLink key={item.href} item={item} />
        ))}
      </VStack>

      {user?.role === "ADMIN" && (
        <>
          <Box px={3} pt={4} pb={1}>
            <Text fontSize="xs" fontWeight="semibold" color="fg.muted" textTransform="uppercase" letterSpacing="wider">
              Administração
            </Text>
          </Box>
          <VStack gap={1} align="stretch">
            {adminItems.map((item) => (
              <NavLink key={item.href} item={item} />
            ))}
          </VStack>
        </>
      )}
    </Flex>
  );
}
