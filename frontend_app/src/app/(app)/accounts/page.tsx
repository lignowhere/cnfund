"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { apiClient } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import { useAuthStore } from "@/store/auth-store";
import { useToastStore } from "@/store/toast-store";

type DraftCredential = {
  username: string;
  password: string;
};

const MIN_PASSWORD_LENGTH = 1;

export default function AccountsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const safeToken = token || "";
  const pushToast = useToastStore((state) => state.push);

  const [createDrafts, setCreateDrafts] = useState<Record<number, DraftCredential>>({});
  const [usernameDrafts, setUsernameDrafts] = useState<Record<number, string>>({});
  const [resetDrafts, setResetDrafts] = useState<Record<number, string>>({});

  const isAdmin = user?.role === "admin";

  const accountsQuery = useQuery({
    queryKey: queryKeys.accountsInvestors(safeToken),
    queryFn: () => apiClient.accountsInvestors(safeToken),
    enabled: !!token && isAdmin,
  });

  const createMutation = useMutation({
    mutationFn: (payload: { investor_id: number; username: string; password: string }) =>
      apiClient.createInvestorAccount(safeToken, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.accountsInvestors(safeToken), exact: true });
      pushToast({ title: "Đã tạo tài khoản nhà đầu tư", variant: "success" });
    },
    onError: (error) => {
      pushToast({
        title: "Không thể tạo tài khoản",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { investorId: number; username?: string; is_active?: boolean }) =>
      apiClient.updateInvestorAccount(safeToken, payload.investorId, {
        username: payload.username,
        is_active: payload.is_active,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.accountsInvestors(safeToken), exact: true });
      pushToast({ title: "Đã cập nhật tài khoản", variant: "success" });
    },
    onError: (error) => {
      pushToast({
        title: "Không thể cập nhật tài khoản",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      });
    },
  });

  const resetMutation = useMutation({
    mutationFn: (payload: { investorId: number; newPassword: string }) =>
      apiClient.resetInvestorAccountPassword(safeToken, payload.investorId, payload.newPassword),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.accountsInvestors(safeToken), exact: true });
      pushToast({ title: "Đã đặt lại mật khẩu", variant: "success" });
    },
    onError: (error) => {
      pushToast({
        title: "Không thể đặt lại mật khẩu",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      });
    },
  });

  const rows = useMemo(() => accountsQuery.data ?? [], [accountsQuery.data]);

  if (!user) {
    return (
      <div className="app-page">
        <LoadingState label="Đang tải thông tin người dùng..." />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="app-page">
        <Card className="space-y-3">
          <h2 className="section-title">Không có quyền truy cập</h2>
          <p className="section-note">Trang này chỉ dành cho quản trị viên.</p>
          <div>
            <Button onClick={() => router.replace(user?.role === "investor" ? "/reports" : "/dashboard")}>
              Quay lại
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (accountsQuery.isLoading) {
    return (
      <div className="app-page">
        <LoadingState label="Đang tải danh sách tài khoản nhà đầu tư..." />
      </div>
    );
  }

  if (accountsQuery.isError) {
    return (
      <div className="app-page">
        <ErrorState message="Không tải được danh sách tài khoản." />
      </div>
    );
  }

  return (
    <div className="app-page">
      <Card className="space-y-4">
        <div className="border-b border-[var(--color-border)] pb-3">
          <h2 className="section-title">Quản lý tài khoản nhà đầu tư</h2>
          <p className="section-note">Tạo tài khoản, cập nhật username, khóa/mở khóa và đặt lại mật khẩu.</p>
        </div>

        <div className="space-y-3">
          {rows.map((row) => {
            const createDraft = createDrafts[row.investor_id] ?? { username: "", password: "" };
            const usernameDraft = usernameDrafts[row.investor_id] ?? row.username ?? "";
            const resetDraft = resetDrafts[row.investor_id] ?? "";

            return (
              <article
                key={row.investor_id}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold">
                      #{row.investor_id} - {row.investor_name}
                    </p>
                    <p className="text-xs text-[var(--color-muted)]">
                      {row.has_account ? `Username: ${row.username}` : "Chưa có tài khoản"}
                    </p>
                  </div>
                  {row.has_account ? (
                    <span
                      className={`rounded-full px-2 py-1 text-xs ${
                        row.is_active
                          ? "bg-[var(--color-success-bg)] text-[var(--color-success-text)]"
                          : "bg-[var(--color-danger-bg)] text-[var(--color-danger-text)]"
                      }`}
                    >
                      {row.is_active ? "Đang hoạt động" : "Đang khóa"}
                    </span>
                  ) : (
                    <span className="rounded-full bg-[var(--color-warning-bg)] px-2 py-1 text-xs text-[var(--color-warning-text)]">
                      Chưa cấp tài khoản
                    </span>
                  )}
                </div>

                {!row.has_account ? (
                  <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
                    <Input
                      placeholder="Username"
                      value={createDraft.username}
                      onChange={(e) =>
                        setCreateDrafts((prev) => ({
                          ...prev,
                          [row.investor_id]: { ...createDraft, username: e.target.value },
                        }))
                      }
                    />
                    <Input
                      placeholder="Mật khẩu ban đầu"
                      type="password"
                      value={createDraft.password}
                      onChange={(e) =>
                        setCreateDrafts((prev) => ({
                          ...prev,
                          [row.investor_id]: { ...createDraft, password: e.target.value },
                        }))
                      }
                    />
                    <Button
                      onClick={() =>
                        createMutation.mutate({
                          investor_id: row.investor_id,
                          username: createDraft.username.trim(),
                          password: createDraft.password,
                        })
                      }
                      disabled={
                        createMutation.isPending ||
                        createDraft.username.trim().length < 3 ||
                        createDraft.password.length < MIN_PASSWORD_LENGTH
                      }
                    >
                      Tạo tài khoản
                    </Button>
                  </div>
                ) : (
                  <div className="mt-3 space-y-2">
                    <div className="grid gap-2 sm:grid-cols-[1fr_auto_auto]">
                      <Input
                        placeholder="Username"
                        value={usernameDraft}
                        onChange={(e) =>
                          setUsernameDrafts((prev) => ({
                            ...prev,
                            [row.investor_id]: e.target.value,
                          }))
                        }
                      />
                      <Button
                        variant="secondary"
                        onClick={() =>
                          updateMutation.mutate({
                            investorId: row.investor_id,
                            username: usernameDraft.trim(),
                          })
                        }
                        disabled={updateMutation.isPending || usernameDraft.trim().length < 3}
                      >
                        Cập nhật username
                      </Button>
                      <Button
                        variant={row.is_active ? "danger" : "secondary"}
                        onClick={() =>
                          updateMutation.mutate({
                            investorId: row.investor_id,
                            is_active: !row.is_active,
                          })
                        }
                        disabled={updateMutation.isPending}
                      >
                        {row.is_active ? "Khóa" : "Mở khóa"}
                      </Button>
                    </div>

                    <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
                      <Input
                        placeholder="Mật khẩu mới"
                        type="password"
                        value={resetDraft}
                        onChange={(e) =>
                          setResetDrafts((prev) => ({
                            ...prev,
                            [row.investor_id]: e.target.value,
                          }))
                        }
                      />
                      <Button
                        variant="secondary"
                        onClick={() =>
                          resetMutation.mutate({
                            investorId: row.investor_id,
                            newPassword: resetDraft,
                          })
                        }
                        disabled={resetMutation.isPending || resetDraft.length < MIN_PASSWORD_LENGTH}
                      >
                        Reset mật khẩu
                      </Button>
                    </div>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
