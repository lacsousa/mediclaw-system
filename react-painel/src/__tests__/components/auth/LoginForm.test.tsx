import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithChakra, screen, waitFor } from "@/test-utils";
import userEvent from "@testing-library/user-event";
import type { User } from "@/types/api";

const mocks = vi.hoisted(() => ({
  routerReplace: vi.fn(),
  authLogin: vi.fn(),
  showToast: vi.fn(),
  libLogin: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mocks.routerReplace, push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
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

vi.mock("@/lib/auth", () => ({
  login: mocks.libLogin,
}));

import { LoginForm } from "@/components/auth/LoginForm";

const mockUser: User = {
  id: 1,
  email: "test@test.com",
  first_name: "Test",
  role: "USER",
  accepted_terms_at: null,
  profile: null,
};

describe("LoginForm", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders email and password fields", () => {
    renderWithChakra(<LoginForm />);
    expect(screen.getByPlaceholderText("seu@email.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("••••••••")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /entrar/i })).toBeInTheDocument();
  });

  it("shows inline error message on INVALID_CREDENTIALS", async () => {
    mocks.libLogin.mockRejectedValueOnce({
      response: { data: { error: { code: "INVALID_CREDENTIALS" } } },
    });

    renderWithChakra(<LoginForm />);
    await user.type(screen.getByPlaceholderText("seu@email.com"), "test@test.com");
    await user.type(screen.getByPlaceholderText("••••••••"), "wrongpass");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    expect(await screen.findByText("E-mail ou senha inválidos")).toBeInTheDocument();
    expect(mocks.showToast).not.toHaveBeenCalled();
  });

  it("shows toast for unexpected errors", async () => {
    mocks.libLogin.mockRejectedValueOnce(new Error("Network error"));

    renderWithChakra(<LoginForm />);
    await user.type(screen.getByPlaceholderText("seu@email.com"), "test@test.com");
    await user.type(screen.getByPlaceholderText("••••••••"), "somepass");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    await waitFor(() =>
      expect(mocks.showToast).toHaveBeenCalledWith("Erro ao fazer login. Tente novamente.", "error")
    );
  });

  it("redirects to /chat on successful login", async () => {
    mocks.libLogin.mockResolvedValueOnce({ access: "acc", refresh: "ref", user: mockUser });

    renderWithChakra(<LoginForm />);
    await user.type(screen.getByPlaceholderText("seu@email.com"), "test@test.com");
    await user.type(screen.getByPlaceholderText("••••••••"), "validpass");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    await waitFor(() => expect(mocks.routerReplace).toHaveBeenCalledWith("/chat"));
    expect(mocks.authLogin).toHaveBeenCalledWith({ access: "acc", refresh: "ref" }, mockUser);
  });
});
