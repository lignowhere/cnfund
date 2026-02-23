"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { ThemeToggle } from "@/components/layout/theme-toggle";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/auth-store";
import { useApplyTheme } from "@/store/theme-store";

function resolveHomeRoute(role?: string | null) {
  return role === "investor" ? "/reports" : "/dashboard";
}

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  const token = useAuthStore((state) => state.accessToken);
  const isHydrated = useAuthStore((state) => state.isHydrated);

  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("1997");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useApplyTheme();

  useEffect(() => {
    if (isHydrated && token) {
      const role = useAuthStore.getState().user?.role;
      router.replace(resolveHomeRoute(role));
    }
  }, [isHydrated, token, router]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username.trim(), password);
      const role = useAuthStore.getState().user?.role;
      router.replace(resolveHomeRoute(role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng nhập thất bại");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center px-4 py-10">
      <ThemeToggle compact className="fixed right-4 top-4 z-50" />
      <Card className="w-full max-w-md space-y-6 border-none bg-[var(--color-surface)]/90 p-6 shadow-2xl backdrop-blur">
        <header className="space-y-2 text-center">
          <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-muted)]">CNFund</p>
          <h1 className="text-2xl font-semibold">Đăng nhập hệ thống</h1>
          <p className="text-sm text-[var(--color-muted)]">Nền tảng quản lý quỹ đầu tư, tối ưu cho mobile</p>
        </header>

        <form className="space-y-4" onSubmit={onSubmit}>
          <div className="space-y-1">
            <label htmlFor="username" className="text-sm font-medium">
              Tên đăng nhập
            </label>
            <Input
              id="username"
              placeholder="Nhập tên đăng nhập"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="password" className="text-sm font-medium">
              Mật khẩu
            </label>
            <Input
              id="password"
              type="password"
              placeholder="Nhập mật khẩu"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error ? (
            <p className="rounded-xl border border-[var(--color-danger-border)] bg-[var(--color-danger-bg)] px-3 py-2 text-sm text-[var(--color-danger-text)]">
              {error}
            </p>
          ) : null}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Đăng nhập
          </Button>
        </form>
      </Card>
    </main>
  );
}
