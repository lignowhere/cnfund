import { Slot } from "@radix-ui/react-slot";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: boolean;
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
};

export function Button({
  className,
  asChild = false,
  variant = "primary",
  size = "md",
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp
      className={cn(
        "inline-flex items-center justify-center rounded-[var(--radius-control)] font-semibold transition-all duration-200",
        size === "sm" && "min-h-9 px-3 py-1.5 text-sm",
        size === "md" && "min-h-11 px-4 py-2 text-base md:text-sm",
        size === "lg" && "min-h-12 px-5 py-2.5 text-base",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-surface)]",
        variant === "primary" &&
          "bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] text-white shadow-lg hover:-translate-y-0.5 hover:brightness-105 focus-visible:ring-[var(--color-primary)] disabled:translate-y-0",
        variant === "secondary" &&
          "border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] hover:bg-[var(--color-surface-2)] focus-visible:ring-[var(--color-primary)]",
        variant === "danger" &&
          "bg-[var(--color-danger)] text-white shadow-md hover:brightness-95 focus-visible:ring-[var(--color-danger)]",
        variant === "ghost" &&
          "text-[var(--color-text)] hover:bg-[var(--color-surface-2)] focus-visible:ring-[var(--color-primary)]",
        "disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      {...props}
    />
  );
}
