/**
 * Voxora Auth Store (Zustand)
 *
 * Manages authentication state: user, tokens, login/register/logout.
 */

import { create } from "zustand";
import { api } from "@/lib/api";
import type { AuthResponse, User } from "@/types/api";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    name: string,
    password: string,
    tenantName: string
  ) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post<AuthResponse>("/api/v1/auth/login", {
        email,
        password,
      });

      localStorage.setItem("voxora_access_token", response.tokens.access_token);
      localStorage.setItem("voxora_refresh_token", response.tokens.refresh_token);
      api.setToken(response.tokens.access_token);

      set({
        user: response.user,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Login failed";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  register: async (
    email: string,
    name: string,
    password: string,
    tenantName: string
  ) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post<AuthResponse>("/api/v1/auth/register", {
        email,
        name,
        password,
        tenant_name: tenantName,
      });

      localStorage.setItem("voxora_access_token", response.tokens.access_token);
      localStorage.setItem("voxora_refresh_token", response.tokens.refresh_token);
      api.setToken(response.tokens.access_token);

      set({
        user: response.user,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Registration failed";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem("voxora_access_token");
    localStorage.removeItem("voxora_refresh_token");
    api.setToken(null);
    set({ user: null, isAuthenticated: false });
  },

  loadUser: async () => {
    const token = localStorage.getItem("voxora_access_token");
    if (!token) return;

    api.setToken(token);
    set({ isLoading: true });

    try {
      const user = await api.get<User>("/api/v1/auth/me");
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      localStorage.removeItem("voxora_access_token");
      localStorage.removeItem("voxora_refresh_token");
      api.setToken(null);
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));
