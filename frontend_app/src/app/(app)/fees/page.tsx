"use client";

import { Loader2 } from "lucide-react";
import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { MoneyInput } from "@/components/form/money-input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { apiClient } from "@/lib/api";
import { digitsToNumber } from "@/lib/number-input";
import { formatCurrency } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";

export default function FeesPage() {
  const token = useAuthStore((state) => state.accessToken);
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [totalNavDigits, setTotalNavDigits] = useState("");
  const [totalNavOverflow, setTotalNavOverflow] = useState(false);
  const [previewSnapshot, setPreviewSnapshot] = useState<{
    endDate: string;
    totalNavDigits: string;
  } | null>(null);
  const [acknowledgeRisk, setAcknowledgeRisk] = useState(false);
  const [acknowledgeBackup, setAcknowledgeBackup] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const totalNav = digitsToNumber(totalNavDigits);

  const flagsQuery = useQuery({
    queryKey: ["feature-flags"],
    queryFn: () => apiClient.featureFlags(token || ""),
    enabled: !!token,
  });

  const safetyEnabled = flagsQuery.data?.fee_safety ?? true;

  const historyQuery = useQuery({
    queryKey: ["fee-history"],
    queryFn: () => apiClient.feeHistory(token || ""),
    enabled: !!token,
  });

  const previewMutation = useMutation({
    mutationFn: () =>
      apiClient.previewFees(token || "", {
        end_date: endDate,
        total_nav: totalNav || 0,
      }),
    onSuccess: () => {
      setPreviewSnapshot({ endDate, totalNavDigits });
      setStatusMessage("Đã cập nhật bản xem trước phí.");
    },
    onError: () => setStatusMessage(null),
  });

  const applyMutation = useMutation({
    mutationFn: () => {
      const previewData = previewMutation.data;
      if (!previewData) {
        throw new Error("Cần xem trước trước khi áp dụng phí.");
      }
      return apiClient.applyFees(token || "", {
        year: Number(year),
        end_date: endDate,
        total_nav: totalNav || 0,
        confirm_token: previewData.confirm_token,
        acknowledge_risk: safetyEnabled ? acknowledgeRisk : true,
        acknowledge_backup: safetyEnabled ? acknowledgeBackup : true,
      });
    },
    onSuccess: () => {
      setStatusMessage("Đã áp dụng phí thành công.");
      historyQuery.refetch();
    },
    onError: () => setStatusMessage(null),
  });

  const hasPreview = Boolean(previewMutation.data);
  const previewMatchesInput =
    previewSnapshot?.endDate === endDate && previewSnapshot?.totalNavDigits === totalNavDigits;

  const canApply =
    !!totalNav &&
    totalNav > 0 &&
    !totalNavOverflow &&
    hasPreview &&
    previewMatchesInput &&
    !applyMutation.isPending &&
    (!safetyEnabled || (acknowledgeRisk && acknowledgeBackup));

  const canPreview = !!totalNav && totalNav > 0 && !totalNavOverflow && !previewMutation.isPending;

  const mutationError = useMemo(() => {
    if (applyMutation.error instanceof Error) return applyMutation.error.message;
    if (previewMutation.error instanceof Error) return previewMutation.error.message;
    return null;
  }, [applyMutation.error, previewMutation.error]);

  return (
    <div className="app-page">
      <Card className="space-y-3">
        <h2 className="section-title">Xem trước và áp dụng phí</h2>
        <div className="grid gap-2 sm:grid-cols-3">
          <Input value={year} onChange={(e) => setYear(e.target.value)} placeholder="Năm" />
          <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          <MoneyInput
            value={totalNavDigits}
            onValueChange={(value) => {
              setTotalNavDigits(value.rawDigits);
              setTotalNavOverflow(value.isOverflow);
            }}
            placeholder="2,500,000,000"
            aria-invalid={!totalNav || totalNav <= 0 || totalNavOverflow}
          />
        </div>
        <p className="input-helper">
          Giá trị NAV gửi tính phí: {totalNav ? formatCurrency(totalNav) : "Chưa có"}
        </p>
        {totalNavOverflow ? <p className="inline-error">Tổng NAV quá lớn (tối đa 15 chữ số).</p> : null}
        {!previewMatchesInput && hasPreview ? (
          <p className="status-warning">
            Dữ liệu đã thay đổi sau lần xem trước gần nhất. Bấm xem trước lại để đồng bộ mã xác nhận.
          </p>
        ) : null}

        {safetyEnabled ? (
          <div className="space-y-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-3">
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={acknowledgeRisk}
                onChange={(e) => setAcknowledgeRisk(e.target.checked)}
                className="h-4 w-4 accent-[var(--color-primary)]"
              />
              Tôi đã kiểm tra bản xem trước và chấp nhận rủi ro ghi phí.
            </label>
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={acknowledgeBackup}
                onChange={(e) => setAcknowledgeBackup(e.target.checked)}
                className="h-4 w-4 accent-[var(--color-primary)]"
              />
              Tôi đã đảm bảo có bản sao lưu trước khi áp dụng phí.
            </label>
          </div>
        ) : null}

        {mutationError ? <ErrorState message={mutationError} /> : null}
        {statusMessage ? <p className="status-success">{statusMessage}</p> : null}

        <div className="grid grid-cols-2 gap-2">
          <Button variant="secondary" onClick={() => previewMutation.mutate()} disabled={!canPreview}>
            {previewMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Xem trước
          </Button>
          <Button onClick={() => applyMutation.mutate()} disabled={!canApply}>
            {applyMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Áp dụng phí
          </Button>
        </div>
      </Card>

      <Card className="space-y-3">
        <h3 className="section-title">Kết quả xem trước</h3>
        {previewMutation.isPending ? (
          <LoadingState label="Đang tạo bản xem trước phí..." />
        ) : previewMutation.data?.items.length ? (
          <div className="list-stagger space-y-2">
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2 text-sm">
                <p className="text-xs text-[var(--color-muted)]">Tổng phí</p>
                <p className="font-semibold">{formatCurrency(previewMutation.data.summary.total_fee_amount)}</p>
              </div>
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2 text-sm">
                <p className="text-xs text-[var(--color-muted)]">Tổng units chuyển</p>
                <p className="font-semibold">{previewMutation.data.summary.total_units_to_transfer.toFixed(6)}</p>
              </div>
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2 text-sm">
                <p className="text-xs text-[var(--color-muted)]">Số nhà đầu tư</p>
                <p className="font-semibold">{previewMutation.data.summary.investor_count}</p>
              </div>
            </div>
            {previewMutation.data.items.map((fee) => (
              <article
                key={fee.investor_id}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-3"
              >
                <p className="text-sm font-semibold">{fee.investor_name}</p>
                <p className="text-xs text-[var(--color-muted)]">
                  Phí: {formatCurrency(fee.fee_amount)} | Lợi nhuận vượt: {formatCurrency(fee.excess_profit)}
                </p>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            title="Chưa có bản xem trước phí."
            description="Nhập thông tin NAV rồi bấm Xem trước để xem kết quả tính phí."
          />
        )}
      </Card>

      <Card className="space-y-3">
        <h3 className="section-title">Lịch sử phí</h3>
        {historyQuery.isLoading ? (
          <LoadingState label="Đang tải lịch sử phí..." />
        ) : historyQuery.isError ? (
          <ErrorState message="Không tải được lịch sử phí." />
        ) : historyQuery.data?.length ? (
          <div className="list-stagger space-y-2">
            {historyQuery.data.map((row) => (
              <article
                key={row.id}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-3"
              >
                <p className="text-sm font-semibold">#{row.id} - nhà đầu tư {row.investor_id}</p>
                <p className="text-xs text-[var(--color-muted)]">
                  {row.period} | {formatCurrency(row.fee_amount)} | {row.calculation_date}
                </p>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState title="Chưa có dữ liệu phí." />
        )}
      </Card>
    </div>
  );
}
