"use client";

import { ErrorBoundary } from "@/components/error-boundary";
import { AppShell } from "@/components/layout/app-shell";
import { AuthGuard } from "@/components/layout/auth-guard";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <ErrorBoundary>
        <AppShell>{children}</AppShell>
      </ErrorBoundary>
    </AuthGuard>
  );
}

