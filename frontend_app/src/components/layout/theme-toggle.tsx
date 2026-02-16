"use client";

import { Laptop, Moon, Sun } from "lucide-react";

import type { ThemePreference } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useThemeStore } from "@/store/theme-store";

const options: Array<{
  value: ThemePreference;
  label: string;
  icon: typeof Sun;
}> = [
  { value: "system", label: "Hệ thống", icon: Laptop },
  { value: "light", label: "Sáng", icon: Sun },
  { value: "dark", label: "Tối", icon: Moon },
];

const cycleMap: Record<ThemePreference, ThemePreference> = {
  system: "light",
  light: "dark",
  dark: "system",
};

export function ThemeToggle({ className, compact = false }: { className?: string; compact?: boolean }) {
  const preference = useThemeStore((state) => state.preference);
  const setPreference = useThemeStore((state) => state.setPreference);

  if (compact) {
    const activeOption = options.find((item) => item.value === preference) ?? options[0];
    const Icon = activeOption.icon;
    return (
      <button
        type="button"
        className={cn(
          "inline-flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-muted)] transition hover:bg-[var(--color-surface-2)] hover:text-[var(--color-text)]",
          className,
        )}
        onClick={() => setPreference(cycleMap[preference])}
        aria-label={`Đổi giao diện: hiện tại ${activeOption.label}`}
        title={`Giao diện: ${activeOption.label}`}
      >
        <Icon className="h-4 w-4" />
      </button>
    );
  }

  return (
    <div
      role="group"
      aria-label="Chế độ giao diện"
      className={cn(
        "inline-flex items-center rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-1",
        className,
      )}
    >
      {options.map((option) => {
        const Icon = option.icon;
        const active = preference === option.value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => setPreference(option.value)}
            aria-pressed={active}
            className={cn(
              "inline-flex min-h-9 items-center gap-1.5 rounded-lg px-2.5 text-xs font-semibold transition-colors",
              active
                ? "bg-[var(--color-primary-50)] text-[var(--color-primary)]"
                : "text-[var(--color-muted)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-text)]",
            )}
          >
            <Icon className="h-3.5 w-3.5" />
            <span>{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}
