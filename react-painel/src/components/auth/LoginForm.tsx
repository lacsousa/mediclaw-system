"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Button,
  FieldErrorText,
  FieldLabel,
  FieldRoot,
  Input,
  Stack,
  Text,
  chakra,
} from "@chakra-ui/react";
import Link from "next/link";
import { login } from "@/lib/auth";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";

const ChakraLink = chakra(Link);

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login: authLogin } = useAuth();
  const { showToast } = useToast();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [credError, setCredError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setCredError("");
    setIsLoading(true);

    try {
      const data = await login(email, password);
      authLogin({ access: data.access, refresh: data.refresh }, data.user);
      const next = searchParams.get("next");
      router.replace(next && next.startsWith("/") ? next : "/chat");
    } catch (err: unknown) {
      const apiError = (err as { response?: { data?: { error?: { code?: string } } } })?.response
        ?.data?.error;
      if (apiError?.code === "INVALID_CREDENTIALS") {
        setCredError("E-mail ou senha inválidos");
      } else {
        showToast("Erro ao fazer login. Tente novamente.", "error");
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <chakra.form
      onSubmit={handleSubmit}
      bg="bg"
      borderWidth="1px"
      borderColor="border"
      borderRadius="xl"
      shadow="card"
      p={8}
      w={{ base: "full", sm: "sm" }}
    >
      <Stack gap={5}>
        <Text fontWeight="bold" fontSize="2xl" textAlign="center">
          Entrar
        </Text>

        <FieldRoot>
          <FieldLabel>E-mail</FieldLabel>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="seu@email.com"
            required
          />
        </FieldRoot>

        <FieldRoot invalid={!!credError}>
          <FieldLabel>Senha</FieldLabel>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
          {credError && <FieldErrorText>{credError}</FieldErrorText>}
        </FieldRoot>

        <Button type="submit" colorPalette="teal" loading={isLoading} disabled={isLoading} w="full">
          Entrar
        </Button>

        <Text fontSize="sm" textAlign="center" color="fg.muted">
          Ainda não tem conta?{" "}
          <ChakraLink href="/register" color="teal.500">
            Cadastre-se
          </ChakraLink>
        </Text>
      </Stack>
    </chakra.form>
  );
}
