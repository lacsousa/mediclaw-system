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
      // Tenta restaurar sessão via cookie httpOnly (sem localStorage).
      // O cookie access_token é enviado automaticamente via withCredentials.
      try {
        const res = await api.get<User>("/api/v1/auth/me/");
        setUser(res.data);
      } catch {
        // Access token expirado: tenta renovar via refresh token (também cookie).
        const refreshed = await refreshToken();
        if (refreshed) {
          try {
            const res = await api.get<User>("/api/v1/auth/me/");
            setUser(res.data);
          } catch {
            // Refresh também falhou: sessão encerrada, nenhum cookie válido.
            setUser(null);
          }
        } else {
          setUser(null);
        }
      } finally {
        setIsLoading(false);
      }
    }

    hydrate();
  }, []);

  const login = useCallback((_tokens: { access: string; refresh: string }, userData: User) => {
    // Os cookies são setados pelo backend na resposta de login.
    // Aqui apenas sincronizamos o estado React com o usuário recebido.
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    authLogout(); // chama backend para blacklistar token e limpar cookies
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
