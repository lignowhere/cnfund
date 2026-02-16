"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import { authApi } from "@/lib/auth-api";
import type { UserInfo } from "@/lib/types";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserInfo | null;
  isHydrated: boolean;
  setHydrated: (hydrated: boolean) => void;
  login: (username: string, password: string) => Promise<void>;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isHydrated: false,
      setHydrated: (hydrated) => set({ isHydrated: hydrated }),
      login: async (username, password) => {
        const tokenPair = await authApi.login(username, password);
        const user = await authApi.me(tokenPair.access_token);
        set({
          accessToken: tokenPair.access_token,
          refreshToken: tokenPair.refresh_token,
          user,
        });
      },
      refresh: async () => {
        const refreshToken = get().refreshToken;
        if (!refreshToken) {
          throw new Error("Missing refresh token");
        }
        const tokenPair = await authApi.refresh(refreshToken);
        const user = await authApi.me(tokenPair.access_token);
        set({
          accessToken: tokenPair.access_token,
          refreshToken: tokenPair.refresh_token,
          user,
        });
      },
      logout: async () => {
        const refreshToken = get().refreshToken;
        if (refreshToken) {
          try {
            await authApi.logout(refreshToken);
          } catch {
            // Ignore logout API failures on client cleanup.
          }
        }
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
        });
      },
    }),
    {
      name: "cnfund-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHydrated(true);
      },
    },
  ),
);
