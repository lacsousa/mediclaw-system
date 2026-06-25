import axios from "axios";
import { logout, refreshToken } from "./auth";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "",
});

api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => {
    // unwrap envelope {data, error, meta} retornado pelo EnvelopeJSONRenderer
    if (res.data && typeof res.data === "object" && "data" in res.data && "error" in res.data) {
      res.data = res.data.data;
    }
    return res;
  },
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      const refreshed = await refreshToken();
      if (refreshed) {
        const token = localStorage.getItem("access_token");
        error.config.headers.Authorization = `Bearer ${token}`;
        // FormData streams are consumed on first send — cannot retry automatically
        if (error.config.data instanceof FormData) {
          return Promise.reject(error);
        }
        return api(error.config);
      }
      logout();
    }
    return Promise.reject(error);
  }
);
