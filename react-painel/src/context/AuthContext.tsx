"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { logout as authLogout, refreshToken } from "@/lib/auth";
import type { User } from "@/types/api";

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (tokens: { access: string; refresh: string }, user: User) => void;
  logout: () => void;
  setUser: React.Dispatch<React.SetStateAction<User | null>>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function hydrate() {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const res = await api.get<User>("/api/v1/auth/me/");
        setUser(res.data);
      } catch {
        const refreshed = await refreshToken();
        if (refreshed) {
          try {
            const res = await api.get<User>("/api/v1/auth/me/");
            setUser(res.data);
          } catch {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
          }
        } else {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        }
      } finally {
        setIsLoading(false);
      }
    }

    hydrate();
  }, []);

  const login = useCallback((tokens: { access: string; refresh: string }, userData: User) => {
    localStorage.setItem("access_token", tokens.access);
    localStorage.setItem("refresh_token", tokens.refresh);
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    authLogout();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
        isLoading,
        login,
        logout,
        setUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
