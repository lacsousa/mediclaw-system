"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  SimpleGrid,
  Stack,
  Text,
  chakra,
} from "@chakra-ui/react";
import { useAuth } from "@/context/AuthContext";
import { FullPageSpinner } from "@/components/common/FullPageSpinner";

const ChakraLink = chakra(Link);

const steps = [
  {
    title: "Crie sua conta",
    description: "Cadastro rápido com e-mail e senha. Seus dados ficam protegidos.",
  },
  {
    title: "Converse com a IA",
    description: "Assistente com base em conhecimento médico e guardrails de segurança.",
  },
  {
    title: "Histórico salvo",
    description: "Suas conversas ficam disponíveis para retomar quando quiser.",
  },
];

export default function LandingPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/chat");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading || isAuthenticated) return <FullPageSpinner />;

  return (
    <Box minH="100dvh" bg="bg.subtle">
      <Box
        as="header"
        borderBottomWidth="1px"
        borderColor="border"
        bg="bg/90"
        backdropFilter="blur(8px)"
        position="sticky"
        top={0}
        zIndex={10}
      >
        <Container maxW="6xl" py={4}>
          <Flex justify="space-between" align="center">
            <Text fontWeight="bold" fontSize="xl" letterSpacing="tight" color="teal.fg">
              MediClaw
            </Text>
            <Flex gap={3}>
              <Button asChild variant="ghost" size="sm">
                <ChakraLink href="/login">Entrar</ChakraLink>
              </Button>
              <Button asChild colorPalette="teal" size="sm">
                <ChakraLink href="/register">Criar conta</ChakraLink>
              </Button>
            </Flex>
          </Flex>
        </Container>
      </Box>

      <Box bg="teal.50" borderBottomWidth="1px" borderColor="border">
        <Container maxW="6xl" py={{ base: 12, md: 20 }}>
          <Stack gap={10} align="center" textAlign="center">
            <Stack gap={4} maxW="3xl">
              <Heading size={{ base: "2xl", md: "4xl" }} lineHeight="shorter" letterSpacing="tight">
                Orientação em saúde com inteligência artificial
              </Heading>
              <Text fontSize={{ base: "md", md: "lg" }} color="fg.muted">
                Tire dúvidas, explore temas de bem-estar e receba respostas fundamentadas — com
                avisos claros de que não substituem consulta médica.
              </Text>
            </Stack>

            <Flex gap={4} wrap="wrap" justify="center">
              <Button asChild colorPalette="teal" size="lg" borderRadius="lg">
                <ChakraLink href="/register">Começar agora</ChakraLink>
              </Button>
              <Button asChild variant="outline" size="lg" borderRadius="lg">
                <ChakraLink href="/login">Já tenho conta</ChakraLink>
              </Button>
            </Flex>
          </Stack>
        </Container>
      </Box>

      <Container maxW="6xl" py={{ base: 10, md: 14 }}>
        <SimpleGrid columns={{ base: 1, md: 3 }} gap={6}>
          {steps.map((step) => (
            <Box
              key={step.title}
              bg="bg"
              p={6}
              borderRadius="xl"
              borderWidth="1px"
              borderColor="border"
              shadow="card"
              transition="shadow 0.2s ease, transform 0.2s ease"
              _hover={{ shadow: "elevated", transform: "translateY(-2px)" }}
            >
              <Heading size="sm" mb={2}>
                {step.title}
              </Heading>
              <Text color="fg.muted" fontSize="sm">
                {step.description}
              </Text>
            </Box>
          ))}
        </SimpleGrid>
      </Container>

      <Box as="footer" borderTopWidth="1px" borderColor="border" py={6} mt={8}>
        <Container maxW="6xl">
          <Text fontSize="sm" color="fg.muted" textAlign="center">
            MediClaw não substitui avaliação, diagnóstico ou tratamento por profissional de saúde.
          </Text>
        </Container>
      </Box>
    </Box>
  );
}
