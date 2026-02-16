"use client";

import { create } from "zustand";

type ToastVariant = "success" | "error" | "info";

export type ToastItem = {
  id: string;
  title: string;
  description?: string;
  variant: ToastVariant;
};

type ToastState = {
  items: ToastItem[];
  push: (toast: Omit<ToastItem, "id" | "variant"> & { variant?: ToastVariant; durationMs?: number }) => void;
  remove: (id: string) => void;
};

function nextToastId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export const useToastStore = create<ToastState>((set, get) => ({
  items: [],
  push: ({ title, description, variant = "info", durationMs = 4200 }) => {
    const id = nextToastId();
    set((state) => ({
      items: [...state.items, { id, title, description, variant }],
    }));
    window.setTimeout(() => {
      get().remove(id);
    }, durationMs);
  },
  remove: (id) =>
    set((state) => ({
      items: state.items.filter((item) => item.id !== id),
    })),
}));
