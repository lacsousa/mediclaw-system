import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithChakra, screen, waitFor } from "@/test-utils";
import userEvent from "@testing-library/user-event";

const mocks = vi.hoisted(() => ({
  routerReplace: vi.fn(),
  authLogin: vi.fn(),
  showToast: vi.fn(),
  apiPost: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mocks.routerReplace, push: vi.fn() }),
}));

vi.mock("@/context/AuthContext", () => ({
  useAuth: () => ({
    login: mocks.authLogin,
    logout: vi.fn(),
    user: null,
    isAuthenticated: false,
    isLoading: false,
  }),
}));

vi.mock("@/context/ToastContext", () => ({
  useToast: () => ({ showToast: mocks.showToast }),
}));

vi.mock("@/lib/api", () => ({
  api: { post: mocks.apiPost },
}));

import { RegisterForm } from "@/components/auth/RegisterForm";

describe("RegisterForm — client-side validation", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  async function fillValidForm(
    overrides: {
      name?: string;
      password?: string;
      confirmPassword?: string;
      skipTerms?: boolean;
    } = {}
  ) {
    const name = overrides.name ?? "João Silva";
    const password = overrides.password ?? "Senha123";
    const confirmPassword = overrides.confirmPassword ?? password;

    await user.type(screen.getByPlaceholderText("Seu nome"), name);
    await user.type(screen.getByPlaceholderText("seu@email.com"), "joao@test.com");
    await user.type(screen.getByPlaceholderText(/mínimo 8/i), password);
    await user.type(screen.getByPlaceholderText("Repita a senha"), confirmPassword);
    if (!overrides.skipTerms) {
      // Click the hidden checkbox input via its label
      const termsLabel = screen.getByText("Aceito os termos de uso");
      await user.click(termsLabel);
    }
  }

  it("shows error when name is too short", async () => {
    renderWithChakra(<RegisterForm />);
    await fillValidForm({ name: "J" });
    await user.click(screen.getByRole("button", { name: /criar conta/i }));
    expect(await screen.findByText("Nome deve ter ao menos 2 caracteres")).toBeInTheDocument();
  });

  it("shows error when password is shorter than 8 characters", async () => {
    renderWithChakra(<RegisterForm />);
    await fillValidForm({ password: "Ab12345", confirmPassword: "Ab12345" });
    await user.click(screen.getByRole("button", { name: /criar conta/i }));
    expect(await screen.findByText("Senha precisa de ao menos 8 caracteres")).toBeInTheDocument();
  });

  it("shows error when password has no digit", async () => {
    renderWithChakra(<RegisterForm />);
    await fillValidForm({ password: "abcdefgh", confirmPassword: "abcdefgh" });
    await user.click(screen.getByRole("button", { name: /criar conta/i }));
    expect(await screen.findByText("Senha deve conter letra e número")).toBeInTheDocument();
  });

  it("shows error when passwords do not match", async () => {
    renderWithChakra(<RegisterForm />);
    await fillValidForm({ confirmPassword: "Diferente1" });
    await user.click(screen.getByRole("button", { name: /criar conta/i }));
    const errors = await screen.findAllByText("Senhas não coincidem");
    expect(errors.length).toBeGreaterThan(0);
  });

  it("shows error when terms are not accepted", async () => {
    renderWithChakra(<RegisterForm />);
    await fillValidForm({ skipTerms: true });
    await user.click(screen.getByRole("button", { name: /criar conta/i }));
    expect(await screen.findByText("Aceite os termos para continuar")).toBeInTheDocument();
  });

  it("does not call the API when client validation fails", async () => {
    renderWithChakra(<RegisterForm />);
    await fillValidForm({ name: "A" });
    await user.click(screen.getByRole("button", { name: /criar conta/i }));
    await screen.findByText("Nome deve ter ao menos 2 caracteres");
    expect(mocks.apiPost).not.toHaveBeenCalled();
  });
});

describe("RegisterForm — API responses", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  async function fillAndSubmitValidForm() {
    await user.type(screen.getByPlaceholderText("Seu nome"), "Ana Costa");
    await user.type(screen.getByPlaceholderText("seu@email.com"), "ana@test.com");
    await user.type(screen.getByPlaceholderText(/mínimo 8/i), "Senha123");
    await user.type(screen.getByPlaceholderText("Repita a senha"), "Senha123");
    await user.click(screen.getByText("Aceito os termos de uso"));
    await user.click(screen.getByRole("button", { name: /criar conta/i }));
  }

  it("shows error when email is already registered", async () => {
    mocks.apiPost.mockRejectedValueOnce({
      response: { data: { error: { code: "EMAIL_ALREADY_EXISTS" } } },
    });

    renderWithChakra(<RegisterForm />);
    await fillAndSubmitValidForm();

    expect(await screen.findByText("Este e-mail já está cadastrado")).toBeInTheDocument();
  });

  it("redirects to /chat on successful registration", async () => {
    mocks.apiPost.mockResolvedValueOnce({
      data: {
        access: "acc",
        refresh: "ref",
        user: {
          id: 2,
          email: "ana@test.com",
          first_name: "Ana",
          role: "USER",
          accepted_terms_at: null,
          profile: null,
        },
      },
    });

    renderWithChakra(<RegisterForm />);
    await fillAndSubmitValidForm();

    await waitFor(() => expect(mocks.routerReplace).toHaveBeenCalledWith("/chat"));
  });
});
