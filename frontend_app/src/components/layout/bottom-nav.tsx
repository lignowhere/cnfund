"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";

import { getPrimaryNav } from "./nav-config";

export function BottomNav() {
  const pathname = usePathname();
  const user = useAuthStore((state) => state.user);
  const primaryNav = getPrimaryNav(user?.role);

  if (!primaryNav.length) {
    return null;
  }

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-[var(--color-border)] bg-[var(--color-surface)]/92 px-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2 backdrop-blur md:hidden">
      <ul
        className="grid gap-1"
        style={{ gridTemplateColumns: `repeat(${primaryNav.length}, minmax(0, 1fr))` }}
      >
        {primaryNav.map((item) => {
          const active = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  "flex min-h-11 flex-col items-center justify-center rounded-lg text-[11px] font-medium transition-all duration-200",
                  active
                    ? "bg-[var(--color-primary-50)] text-[var(--color-primary)] shadow-sm"
                    : "text-[var(--color-muted)] hover:-translate-y-0.5 hover:bg-[var(--color-surface-2)] hover:text-[var(--color-text)]",
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
