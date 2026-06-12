"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Button,
  CheckboxControl,
  CheckboxHiddenInput,
  CheckboxIndicator,
  CheckboxLabel,
  CheckboxRoot,
  FieldErrorText,
  FieldLabel,
  FieldRoot,
  Flex,
  Input,
  Stack,
  Text,
  chakra,
} from "@chakra-ui/react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import type { User } from "@/types/api";

const ChakraLink = chakra(Link);

interface RegisterResponse {
  access: string;
  refresh: string;
  user: User;
}

function validate(
  name: string,
  password: string,
  confirmPassword: string,
  acceptTerms: boolean
): string {
  if (name.trim().length < 2) return "Nome deve ter ao menos 2 caracteres";
  if (password.length < 8) return "Senha precisa de ao menos 8 caracteres";
  if (!/[a-zA-Z]/.test(password) || !/[0-9]/.test(password))
    return "Senha deve conter letra e número";
  if (password !== confirmPassword) return "Senhas não coincidem";
  if (!acceptTerms) return "Aceite os termos para continuar";
  return "";
}

export function RegisterForm() {
  const router = useRouter();
  const { login: authLogin } = useAuth();
  const { showToast } = useToast();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [fieldError, setFieldError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFieldError("");
    setEmailError("");

    const validationError = validate(name, password, confirmPassword, acceptTerms);
    if (validationError) {
      setFieldError(validationError);
      return;
    }

    setIsLoading(true);

    try {
      const res = await api.post<RegisterResponse>("/api/v1/auth/register/", {
        name,
        email,
        password,
        accept_terms: true,
      });
      authLogin({ access: res.data.access, refresh: res.data.refresh }, res.data.user);
      router.replace("/chat");
    } catch (err: unknown) {
      const apiError = (
        err as { response?: { data?: { error?: { code?: string; message?: string } } } }
      )?.response?.data?.error;
      const isEmailDuplicate =
        apiError?.code === "EMAIL_ALREADY_EXISTS" || apiError?.message?.includes("já cadastrado");
      if (isEmailDuplicate) {
        setEmailError("Este e-mail já está cadastrado");
      } else {
        showToast("Erro ao criar conta. Tente novamente.", "error");
      }
    } finally {
      setIsLoading(false);
    }
  }

  const isPasswordError =
    !!fieldError && (fieldError.includes("Senha") || fieldError.includes("coincidem"));

  return (
    <chakra.form
      onSubmit={handleSubmit}
      bg="bg"
      borderWidth="1px"
      borderColor="border"
      borderRadius="xl"
      shadow="card"
      p={8}
      w={{ base: "full", sm: "md" }}
    >
      <Stack gap={5}>
        <Text fontWeight="bold" fontSize="2xl" textAlign="center">
          Criar conta
        </Text>

        <FieldRoot invalid={!!fieldError && fieldError.includes("Nome")}>
          <FieldLabel>Nome</FieldLabel>
          <Input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Seu nome"
            required
          />
          {fieldError.includes("Nome") && <FieldErrorText>{fieldError}</FieldErrorText>}
        </FieldRoot>

        <FieldRoot invalid={!!emailError}>
          <FieldLabel>E-mail</FieldLabel>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="seu@email.com"
            required
          />
          {emailError && <FieldErrorText>{emailError}</FieldErrorText>}
        </FieldRoot>

        <FieldRoot invalid={isPasswordError}>
          <FieldLabel>Senha</FieldLabel>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Mínimo 8 caracteres, letra e número"
            required
          />
          {fieldError.includes("Senha") && <FieldErrorText>{fieldError}</FieldErrorText>}
        </FieldRoot>

        <FieldRoot invalid={!!fieldError && fieldError.includes("coincidem")}>
          <FieldLabel>Confirmar senha</FieldLabel>
          <Input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Repita a senha"
            required
          />
          {fieldError.includes("coincidem") && <FieldErrorText>{fieldError}</FieldErrorText>}
        </FieldRoot>

        <FieldRoot invalid={!!fieldError && fieldError.includes("termos")}>
          <CheckboxRoot
            checked={acceptTerms}
            onCheckedChange={(e) => setAcceptTerms(e.checked === true)}
          >
            <CheckboxHiddenInput />
            <Flex align="center" gap={2}>
              <CheckboxControl>
                <CheckboxIndicator />
              </CheckboxControl>
              <CheckboxLabel>Aceito os termos de uso</CheckboxLabel>
            </Flex>
          </CheckboxRoot>
          {fieldError.includes("termos") && <FieldErrorText>{fieldError}</FieldErrorText>}
        </FieldRoot>

        <Button type="submit" colorPalette="teal" loading={isLoading} disabled={isLoading} w="full">
          Criar conta
        </Button>

        <Text fontSize="sm" textAlign="center" color="fg.muted">
          Já tem uma conta?{" "}
          <ChakraLink href="/login" color="teal.500">
            Entrar
          </ChakraLink>
        </Text>
      </Stack>
    </chakra.form>
  );
}
