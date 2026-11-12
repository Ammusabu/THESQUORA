import { api } from "./client";
import type { AuthResponse, User } from "../types";

export async function register(data: {
  name: string;
  email: string;
  password: string;
  department?: string | null;
}): Promise<User> {
  const res = await api.post<User>("/api/auth/register", data);
  return res.data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await api.post<AuthResponse>("/api/auth/login", { email, password });
  return res.data;
}

export async function me(): Promise<User> {
  const res = await api.get<User>("/api/auth/me");
  return res.data;
}
