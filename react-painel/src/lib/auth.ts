import type { User } from "@/types/api";
import { api } from "./api";

export async function refreshToken(): Promise<boolean> {
  const refresh = localStorage.getItem("refresh_token");
  if (!refresh) return false;

  try {
    const res = await api.post<{ access: string }>("/api/v1/auth/refresh/", { refresh });
    localStorage.setItem("access_token", res.data.access);
    return true;
  } catch {
    return false;
  }
}

export function logout(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  window.location.href = "/login";
}

export async function login(
  email: string,
  password: string
): Promise<{ access: string; refresh: string; user: User }> {
  const res = await api.post<{ access: string; refresh: string; user: User }>(
    "/api/v1/auth/login/",
    { email, password }
  );
  return res.data;
}
