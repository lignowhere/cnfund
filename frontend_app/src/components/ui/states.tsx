import { AlertCircle, Inbox, Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";

export function LoadingState({ label = "Đang tải dữ liệu..." }: { label?: string }) {
  return (
    <div className="flex min-h-24 items-center justify-center gap-2 rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-6 text-sm text-[var(--color-muted)]">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  className,
}: {
  title: string;
  description?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-8 text-center",
        className,
      )}
    >
      <Inbox className="mx-auto h-5 w-5 text-[var(--color-muted)]" />
      <p className="mt-2 text-sm font-medium">{title}</p>
      {description ? <p className="mt-1 text-xs text-[var(--color-muted)]">{description}</p> : null}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-[var(--color-danger-border)] bg-[var(--color-danger-bg)] px-4 py-3 text-sm text-[var(--color-danger-text)]">
      <div className="flex items-center gap-2">
        <AlertCircle className="h-4 w-4" />
        <span>{message}</span>
      </div>
    </div>
  );
}
