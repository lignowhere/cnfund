"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { useEffect } from "react";

import { THEME_STORAGE_KEY } from "@/lib/theme";
import type { ResolvedTheme, ThemePreference } from "@/lib/types";

type ThemeState = {
  preference: ThemePreference;
  resolvedTheme: ResolvedTheme;
  setPreference: (preference: ThemePreference) => void;
  setResolvedTheme: (theme: ResolvedTheme) => void;
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      preference: "system",
      resolvedTheme: "light",
      setPreference: (preference) => set({ preference }),
      setResolvedTheme: (resolvedTheme) => set({ resolvedTheme }),
    }),
    {
      name: THEME_STORAGE_KEY,
      partialize: (state) => ({ preference: state.preference }),
    },
  ),
);

function resolveTheme(preference: ThemePreference, isSystemDark: boolean): ResolvedTheme {
  if (preference === "system") {
    return isSystemDark ? "dark" : "light";
  }
  return preference;
}

export function applyThemeToDocument(theme: ResolvedTheme) {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
}

export function useApplyTheme() {
  const preference = useThemeStore((state) => state.preference);
  const setResolvedTheme = useThemeStore((state) => state.setResolvedTheme);

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const nextResolved = resolveTheme(preference, media.matches);
    applyThemeToDocument(nextResolved);
    setResolvedTheme(nextResolved);

    if (preference !== "system") {
      return undefined;
    }

    const handler = (event: MediaQueryListEvent) => {
      const resolved = resolveTheme("system", event.matches);
      applyThemeToDocument(resolved);
      setResolvedTheme(resolved);
    };
    media.addEventListener("change", handler);
    return () => {
      media.removeEventListener("change", handler);
    };
  }, [preference, setResolvedTheme]);
}
