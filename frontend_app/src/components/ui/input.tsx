import { forwardRef } from "react";
import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "min-h-11 w-full rounded-[var(--radius-control)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-base text-[var(--color-text)] shadow-sm md:text-sm",
          "placeholder:text-[var(--color-muted)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20",
          "aria-[invalid=true]:border-[var(--color-danger)] aria-[invalid=true]:ring-2 aria-[invalid=true]:ring-[color-mix(in_oklab,var(--color-danger)_24%,transparent)]",
          className,
        )}
        {...props}
      />
    );
  },
);

Input.displayName = "Input";
