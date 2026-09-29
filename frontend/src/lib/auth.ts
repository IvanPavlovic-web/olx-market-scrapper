"use client";
import Cookies from "js-cookie";
import { api } from "@/lib/api";

export async function login(email: string, password: string) {
  const { data } = await api.post("/auth/login", { email, password });
  Cookies.set("token", data.access_token, { expires: 1 });
  Cookies.set("user", JSON.stringify(data.user), { expires: 1 });
  return data.user;
}

export async function register(
  email: string,
  username: string,
  password: string,
) {
  const { data } = await api.post("/auth/register", {
    email,
    username,
    password,
  });
  Cookies.set("token", data.access_token, { expires: 1 });
  Cookies.set("user", JSON.stringify(data.user), { expires: 1 });
  return data.user;
}

export function logout() {
  Cookies.remove("token");
  Cookies.remove("user");
  window.location.replace(new URL("/login", window.location.origin).toString());
}

export function currentUser() {
  if (typeof window === "undefined") return null;
  const raw = Cookies.get("user");
  return raw ? JSON.parse(raw) : null;
}
