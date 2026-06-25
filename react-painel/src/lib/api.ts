import axios from "axios";
import { logout, refreshToken } from "./auth";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "",
  withCredentials: true, // envia cookies httpOnly automaticamente em toda requisição
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
        // FormData streams são consumidos no primeiro envio — não pode retentar automaticamente
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
