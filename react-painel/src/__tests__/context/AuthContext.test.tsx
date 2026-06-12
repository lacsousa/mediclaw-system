import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";

vi.mock("@/lib/api", () => ({
  api: { get: vi.fn() },
}));

vi.mock("@/lib/auth", () => ({
  refreshToken: vi.fn(),
  logout: vi.fn(),
  login: vi.fn(),
}));

import { api } from "@/lib/api";
import { refreshToken } from "@/lib/auth";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import type { User } from "@/types/api";

const mockUser: User = {
  id: 1,
  email: "test@example.com",
  first_name: "Test",
  role: "USER",
  accepted_terms_at: null,
  profile: null,
};

describe("AuthContext", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("resolves with no user when no token is stored", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("hydrates user when a valid token is in localStorage", async () => {
    localStorage.setItem("access_token", "valid-token");
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockUser });

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it("tries refresh when token is expired and refresh succeeds", async () => {
    localStorage.setItem("access_token", "expired-token");
    vi.mocked(api.get)
      .mockRejectedValueOnce(new Error("Unauthorized"))
      .mockResolvedValueOnce({ data: mockUser });
    vi.mocked(refreshToken).mockResolvedValue(true);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.user).toEqual(mockUser);
  });

  it("clears storage when token is invalid and refresh also fails", async () => {
    localStorage.setItem("access_token", "expired-token");
    localStorage.setItem("refresh_token", "expired-refresh");
    vi.mocked(api.get).mockRejectedValue(new Error("Unauthorized"));
    vi.mocked(refreshToken).mockResolvedValue(false);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.user).toBeNull();
    expect(localStorage.getItem("access_token")).toBeNull();
    expect(localStorage.getItem("refresh_token")).toBeNull();
  });

  it("login stores tokens and sets user", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => {
      result.current.login({ access: "new-access", refresh: "new-refresh" }, mockUser);
    });

    expect(localStorage.getItem("access_token")).toBe("new-access");
    expect(localStorage.getItem("refresh_token")).toBe("new-refresh");
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });
});
