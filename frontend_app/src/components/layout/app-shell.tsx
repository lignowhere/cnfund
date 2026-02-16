"use client";

import { usePathname } from "next/navigation";

import { BottomNav } from "@/components/layout/bottom-nav";
import { SideDrawer } from "@/components/layout/side-drawer";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { ToastViewport } from "@/components/ui/toast-viewport";
import { useAuthStore } from "@/store/auth-store";
import { useApplyTheme } from "@/store/theme-store";

const titles: Record<string, string> = {
  "/dashboard": "Tổng quan",
  "/transactions": "Giao dịch",
  "/investors": "Nhà đầu tư",
  "/fees": "Tính phí",
  "/reports": "Báo cáo",
  "/backup": "Sao lưu",
};

const roleLabel: Record<string, string> = {
  viewer: "Người xem",
  admin: "Quản trị viên",
  fund_manager: "Quản lý quỹ",
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const user = useAuthStore((state) => state.user);

  useApplyTheme();

  return (
    <div className="min-h-screen bg-[var(--color-surface-2)] text-[var(--color-text)]">
      <header className="sticky top-0 z-30 border-b border-[var(--color-border)] bg-[var(--color-surface)]/90 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 md:px-6">
          <div className="flex items-center gap-3">
            <SideDrawer />
            <ThemeToggle compact className="md:hidden" />
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-muted)]">CNFund</p>
              <h1 className="sr-only md:not-sr-only md:text-base md:font-semibold">
                {titles[pathname] || "CNFund"}
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="hidden md:block">
              <ThemeToggle />
            </div>
            <div className="hidden rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1 text-xs text-[var(--color-muted)] md:block">
              {user?.role ? roleLabel[user.role] || user.role : roleLabel.viewer}
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 pb-[calc(6.4rem+env(safe-area-inset-bottom))] pt-6 md:px-6 md:pb-10 md:pt-7">
        {children}
      </main>
      <BottomNav />
      <ToastViewport />
    </div>
  );
}
