"use client";

import { CheckCircle2, Info, X, XCircle } from "lucide-react";

import { cn } from "@/lib/utils";
import { useToastStore } from "@/store/toast-store";

const variantStyles = {
  success: {
    icon: CheckCircle2,
    className:
      "border-[var(--color-success-border)] bg-[var(--color-success-bg)] text-[var(--color-success-text)]",
  },
  error: {
    icon: XCircle,
    className:
      "border-[var(--color-danger-border)] bg-[var(--color-danger-bg)] text-[var(--color-danger-text)]",
  },
  info: {
    icon: Info,
    className: "border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)]",
  },
};

export function ToastViewport() {
  const items = useToastStore((state) => state.items);
  const remove = useToastStore((state) => state.remove);

  return (
    <div className="pointer-events-none fixed inset-x-3 bottom-[calc(5.8rem+env(safe-area-inset-bottom))] z-[90] space-y-2 md:inset-x-auto md:right-6 md:top-20 md:w-[360px]">
      {items.map((toast) => {
        const style = variantStyles[toast.variant];
        const Icon = style.icon;
        return (
          <article
            key={toast.id}
            className={cn(
              "pointer-events-auto rounded-xl border p-3 shadow-[var(--shadow-card)] backdrop-blur",
              style.className,
            )}
            role="status"
            aria-live="polite"
          >
            <div className="flex items-start gap-2">
              <Icon className="mt-0.5 h-4 w-4 shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold">{toast.title}</p>
                {toast.description ? <p className="mt-1 text-xs opacity-90">{toast.description}</p> : null}
              </div>
              <button
                type="button"
                className="inline-flex h-6 w-6 items-center justify-center rounded-md opacity-75 transition hover:opacity-100"
                onClick={() => remove(toast.id)}
                aria-label="Đóng thông báo"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          </article>
        );
      })}
    </div>
  );
}
