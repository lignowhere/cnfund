import { cn } from "@/lib/utils";

export function Card({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <section
      className={cn(
        "rounded-[var(--radius-card)] border border-[var(--color-border)] bg-[var(--color-surface)]/90 p-4 shadow-[var(--shadow-card)] backdrop-blur transition-all duration-200 md:p-5",
        "hover:-translate-y-0.5 hover:shadow-[var(--shadow-card-hover)]",
        className,
      )}
    >
      {children}
    </section>
  );
}
