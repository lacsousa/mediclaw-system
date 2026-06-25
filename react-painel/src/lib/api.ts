import axios from "axios";
import { refreshToken } from "./auth";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "",
  withCredentials: true,
});

api.interceptors.response.use(
  (res) => {
    if (res.data && typeof res.data === "object" && "data" in res.data && "error" in res.data) {
      res.data = res.data.data;
    }
    return res;
  },
  async (error) => {
    const isRefreshEndpoint = error.config?.url?.includes("/auth/refresh/");

    if (error.response?.status === 401 && !error.config._retry && !isRefreshEndpoint) {
      error.config._retry = true;
      const refreshed = await refreshToken();
      if (refreshed) {
        if (error.config.data instanceof FormData) {
          return Promise.reject(error);
        }
        return api(error.config);
      }
    }
    return Promise.reject(error);
  }
);
