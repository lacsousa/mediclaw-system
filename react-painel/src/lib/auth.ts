import type { User } from "@/types/api";
import { api } from "./api";

export async function refreshToken(): Promise<boolean> {
  try {
    // O cookie refresh_token é enviado automaticamente via withCredentials.
    // O backend emite novos cookies access_token e refresh_token na resposta.
    await api.post("/api/v1/auth/refresh/");
    return true;
  } catch {
    return false;
  }
}

export function logout(): void {
  // Chama o backend para blacklistar o refresh token e limpar os cookies.
  // Usa fetch plain para evitar loop de interceptor do axios.
  const base = process.env.NEXT_PUBLIC_API_URL ?? "";
  fetch(`${base}/api/v1/auth/logout/`, {
    method: "POST",
    credentials: "include",
  }).finally(() => {
    window.location.href = "/login";
  });
}

export async function login(
  email: string,
  password: string
): Promise<{ access: string; refresh: string; user: User }> {
  const res = await api.post<{ access: string; refresh: string; user: User }>(
    "/api/v1/auth/login/",
    { email, password }
  );
  // Os tokens são setados como cookies httpOnly pelo backend.
  // O body ainda retorna access/refresh para compatibilidade com testes.
  return res.data;
}
