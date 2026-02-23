"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { LogOut, Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { ThemeToggle } from "@/components/layout/theme-toggle";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";

import { getDrawerNav } from "./nav-config";

export function SideDrawer() {
  const pathname = usePathname();
  const router = useRouter();
  const logout = useAuthStore((state) => state.logout);
  const user = useAuthStore((state) => state.user);
  const drawerNav = getDrawerNav(user?.role);
  const [confirmLogoutOpen, setConfirmLogoutOpen] = useState(false);

  return (
    <>
      <Dialog.Root>
        <Dialog.Trigger asChild>
          <Button variant="secondary" className="h-11 w-11 rounded-xl p-0 md:h-10 md:w-10" aria-label="Mở menu">
            <Menu className="h-5 w-5" />
          </Button>
        </Dialog.Trigger>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-black/35 data-[state=open]:animate-[overlay-in_160ms_ease-out]" />
          <Dialog.Content className="fixed inset-y-0 left-0 z-50 w-[85vw] max-w-[340px] border-r border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-2xl focus:outline-none data-[state=open]:animate-[drawer-in_220ms_ease-out]">
            <Dialog.Title className="sr-only">Menu điều hướng</Dialog.Title>
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--color-muted)]">CNFund Mobile</p>
                <p className="text-base font-semibold text-[var(--color-text)]">{user?.username || "Khách"}</p>
              </div>
              <Dialog.Close asChild>
                <Button variant="secondary" className="h-10 w-10 rounded-xl p-0" aria-label="Đóng menu">
                  <X className="h-5 w-5" />
                </Button>
              </Dialog.Close>
            </div>

            <div className="mb-4">
              <ThemeToggle className="w-full justify-between" />
            </div>

            <ul className="space-y-1">
              {drawerNav.map((item) => {
                const active = pathname.startsWith(item.href);
                const Icon = item.icon;
                return (
                  <li key={item.href}>
                    <Dialog.Close asChild>
                      <Link
                        href={item.href}
                        className={cn(
                          "flex min-h-11 items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-all duration-200",
                          active
                            ? "bg-[var(--color-primary-50)] text-[var(--color-primary)]"
                            : "text-[var(--color-text)] hover:translate-x-0.5 hover:bg-[var(--color-surface-2)]",
                        )}
                      >
                        <Icon className="h-4 w-4" />
                        <span>{item.label}</span>
                      </Link>
                    </Dialog.Close>
                  </li>
                );
              })}
            </ul>

            <div className="mt-6 border-t border-[var(--color-border)] pt-4">
              <Dialog.Close asChild>
                <Button
                  variant="danger"
                  className="w-full justify-start gap-2"
                  onClick={() => setConfirmLogoutOpen(true)}
                >
                  <LogOut className="h-4 w-4" />
                  Đăng xuất
                </Button>
              </Dialog.Close>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
      <ConfirmDialog
        open={confirmLogoutOpen}
        onOpenChange={setConfirmLogoutOpen}
        title="Xác nhận đăng xuất"
        description="Bạn có chắc muốn đăng xuất khỏi hệ thống?"
        confirmLabel="Đăng xuất"
        confirmVariant="danger"
        onConfirm={async () => {
          await logout();
          setConfirmLogoutOpen(false);
          router.push("/login");
        }}
      />
    </>
  );
}
