"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuthStore } from "@/store/auth-store";

export default function HomePage() {
  const router = useRouter();
  const token = useAuthStore((state) => state.accessToken);
  const isHydrated = useAuthStore((state) => state.isHydrated);

  useEffect(() => {
    if (!isHydrated) return;
    router.replace(token ? "/dashboard" : "/login");
  }, [isHydrated, token, router]);

  return (
    <main className="grid min-h-screen place-items-center">
      <p className="text-sm text-[var(--color-muted)]">Đang khởi tạo...</p>
    </main>
  );
}
