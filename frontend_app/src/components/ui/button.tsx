import { Slot } from "@radix-ui/react-slot";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: boolean;
  variant?: "primary" | "secondary" | "danger";
};

export function Button({
  className,
  asChild = false,
  variant = "primary",
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp
      className={cn(
        "inline-flex min-h-11 items-center justify-center rounded-[var(--radius-control)] px-4 py-2 text-base font-semibold transition-all duration-200 md:text-sm",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        variant === "primary" &&
          "bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] text-white shadow-lg shadow-sky-200/60 hover:-translate-y-0.5 hover:brightness-105 focus-visible:ring-[var(--color-primary)] disabled:translate-y-0",
        variant === "secondary" &&
          "border border-[var(--color-border)] bg-white text-[var(--color-text)] hover:bg-[var(--color-surface-2)] focus-visible:ring-[var(--color-primary)]",
        variant === "danger" &&
          "bg-[var(--color-danger)] text-white shadow-md shadow-red-200 hover:brightness-95 focus-visible:ring-[var(--color-danger)]",
        "disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      {...props}
    />
  );
}
