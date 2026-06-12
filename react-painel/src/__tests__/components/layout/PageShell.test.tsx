import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderWithChakra, screen } from "@/test-utils";
import type { User } from "@/types/api";

vi.mock("@/context/AuthContext", () => ({
  useAuth: vi.fn(),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("next/navigation", () => ({
  usePathname: vi.fn(() => "/chat"),
  useRouter: vi.fn(() => ({ replace: vi.fn(), push: vi.fn() })),
}));

import { useAuth } from "@/context/AuthContext";
import { PageShell } from "@/components/layout/PageShell";

const baseAuth = {
  user: null as User | null,
  isAuthenticated: false,
  isLoading: false,
  login: vi.fn(),
  logout: vi.fn(),
};

describe("PageShell", () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({ ...baseAuth });
  });

  it("renders children content", () => {
    renderWithChakra(
      <PageShell>
        <p>conteúdo da página</p>
      </PageShell>
    );
    expect(screen.getByText("conteúdo da página")).toBeInTheDocument();
  });

  it("renders the MediClaw brand in the sidebar", () => {
    renderWithChakra(
      <PageShell>
        <p>test</p>
      </PageShell>
    );
    expect(screen.getAllByText("MediClaw").length).toBeGreaterThan(0);
  });

  it("renders the logout button", () => {
    renderWithChakra(
      <PageShell>
        <p>test</p>
      </PageShell>
    );
    expect(screen.getByRole("button", { name: /sair/i })).toBeInTheDocument();
  });

  it("shows chat navigation link", () => {
    renderWithChakra(
      <PageShell>
        <p>test</p>
      </PageShell>
    );
    expect(screen.getByText("Chat IA")).toBeInTheDocument();
  });

  it("shows the username in the topbar when user is logged in", () => {
    vi.mocked(useAuth).mockReturnValue({
      ...baseAuth,
      user: {
        id: 1,
        email: "user@test.com",
        first_name: "Maria",
        role: "USER",
        accepted_terms_at: null,
        profile: null,
      },
      isAuthenticated: true,
    });
    renderWithChakra(
      <PageShell>
        <p>test</p>
      </PageShell>
    );
    expect(screen.getByText("Maria")).toBeInTheDocument();
  });
});
