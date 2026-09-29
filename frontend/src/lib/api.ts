import axios from "axios";
import Cookies from "js-cookie";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

export const api = axios.create({ baseURL: `${API_URL}/api` });

api.interceptors.request.use((config) => {
  const token = Cookies.get("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401 && typeof window !== "undefined") {
      Cookies.remove("token");
      if (window.location.pathname !== "/login") {
        window.location.replace(
          new URL("/login", window.location.origin).toString(),
        );
      }
    }
    return Promise.reject(err);
  },
);

export async function fetcher<T>(url: string): Promise<T> {
  const { data } = await api.get<T>(url);
  return data;
}

export function getApiErrorMessage(error: unknown, fallback = "Greška") {
  const response = (error as {
    response?: { data?: { detail?: unknown } };
  })?.response;
  const detail = response?.data?.detail;

  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) {
          return String(item.msg);
        }
        return null;
      })
      .filter((message): message is string => Boolean(message));
    if (messages.length > 0) return messages.join("; ");
  }

  return fallback;
}
