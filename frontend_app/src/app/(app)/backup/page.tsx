"use client";

import { Loader2 } from "lucide-react";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";

export default function BackupPage() {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.accessToken);
  const [restoreTargetId, setRestoreTargetId] = useState<string | null>(null);
  const [confirmPhrase, setConfirmPhrase] = useState("");
  const [createSafetyBackup, setCreateSafetyBackup] = useState(true);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const flagsQuery = useQuery({
    queryKey: ["feature-flags"],
    queryFn: () => apiClient.featureFlags(token || ""),
    enabled: !!token,
  });

  const backupsQuery = useQuery({
    queryKey: ["backups"],
    queryFn: () => apiClient.backups(token || ""),
    enabled: !!token,
  });

  const manualMutation = useMutation({
    mutationFn: () => apiClient.manualBackup(token || ""),
    onSuccess: (result) => {
      setStatusMessage(`Đã tạo bản sao lưu thành công: ${result.backup_id}`);
      queryClient.invalidateQueries({ queryKey: ["backups"] });
    },
    onError: () => setStatusMessage(null),
  });

  const restoreMutation = useMutation({
    mutationFn: (backupId: string) =>
      apiClient.restoreBackup(token || "", {
        backup_id: backupId,
        confirm_phrase: confirmPhrase,
        create_safety_backup: createSafetyBackup,
      }),
    onSuccess: () => {
      setStatusMessage("Khôi phục dữ liệu thành công.");
      setRestoreTargetId(null);
      setConfirmPhrase("");
      queryClient.invalidateQueries({ queryKey: ["backups"] });
    },
    onError: () => setStatusMessage(null),
  });

  const restoreEnabled = flagsQuery.data?.backup_restore ?? true;
  const actionError = useMemo(() => {
    if (manualMutation.error instanceof Error) return manualMutation.error.message;
    if (restoreMutation.error instanceof Error) return restoreMutation.error.message;
    return null;
  }, [manualMutation.error, restoreMutation.error]);

  return (
    <div className="app-page">
      <Card className="space-y-3">
        <h2 className="section-title">Quản lý sao lưu</h2>
        <Button onClick={() => manualMutation.mutate()} disabled={manualMutation.isPending}>
          {manualMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          Tạo sao lưu thủ công
        </Button>
        {statusMessage ? <p className="status-success">{statusMessage}</p> : null}
        {actionError ? <ErrorState message={actionError} /> : null}
      </Card>

      <Card className="space-y-3">
        <h2 className="section-title">Danh sách bản sao lưu</h2>
        {!restoreEnabled ? (
          <p className="status-warning">Chức năng khôi phục đang được tắt bởi feature flag.</p>
        ) : null}

        {backupsQuery.isLoading ? (
          <LoadingState label="Đang tải danh sách sao lưu..." />
        ) : backupsQuery.isError ? (
          <ErrorState message="Không tải được danh sách sao lưu." />
        ) : backupsQuery.data?.length ? (
          <div className="list-stagger space-y-2">
            {backupsQuery.data.map((item) => (
              <article
                key={`${item.backup_id}-${item.created_at}`}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3"
              >
                <p className="text-sm font-semibold">{item.backup_type}</p>
                <p className="text-xs text-[var(--color-muted)] break-all">ID: {item.backup_id || "N/A"}</p>
                <p className="text-xs text-[var(--color-muted)]">Tạo lúc: {item.created_at || "N/A"}</p>

                {item.backup_id && restoreEnabled ? (
                  <Button
                    variant="secondary"
                    className="mt-2"
                    onClick={() => setRestoreTargetId((current) => (current === item.backup_id ? null : item.backup_id))}
                    disabled={restoreMutation.isPending}
                  >
                    {restoreTargetId === item.backup_id ? "Đóng xác nhận" : "Khôi phục"}
                  </Button>
                ) : null}

                {restoreTargetId === item.backup_id ? (
                  <div className="mt-3 space-y-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-3">
                    <p className="text-xs text-[var(--color-muted)]">
                      Nhập <span className="font-semibold text-[var(--color-text)]">RESTORE</span> để xác nhận khôi phục dữ liệu.
                    </p>
                    <Input value={confirmPhrase} onChange={(e) => setConfirmPhrase(e.target.value)} placeholder="Nhập RESTORE" />
                    <label className="flex cursor-pointer items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={createSafetyBackup}
                        onChange={(e) => setCreateSafetyBackup(e.target.checked)}
                        className="h-4 w-4 accent-[var(--color-primary)]"
                      />
                      Tạo sao lưu an toàn trước khi khôi phục
                    </label>
                    <div className="flex gap-2">
                      <Button
                        variant="danger"
                        className="flex-1"
                        onClick={() => restoreMutation.mutate(item.backup_id)}
                        disabled={restoreMutation.isPending || confirmPhrase.trim().toUpperCase() !== "RESTORE"}
                      >
                        {restoreMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                        Xác nhận khôi phục
                      </Button>
                      <Button
                        variant="secondary"
                        className="flex-1"
                        onClick={() => {
                          setRestoreTargetId(null);
                          setConfirmPhrase("");
                        }}
                        disabled={restoreMutation.isPending}
                      >
                        Huỷ
                      </Button>
                    </div>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <EmptyState title="Chưa có bản sao lưu." />
        )}
      </Card>
    </div>
  );
}
