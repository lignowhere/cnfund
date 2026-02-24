"use client";

import { Loader2 } from "lucide-react";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { MoneyInput } from "@/components/form/money-input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { apiClient } from "@/lib/api";
import { digitsToNumber } from "@/lib/number-input";
import { queryKeys } from "@/lib/query-keys";
import { formatCurrency } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";
import { useToastStore } from "@/store/toast-store";

type PreviewSnapshot = {
  endDate: string;
  totalNavDigits: string;
  configDigest: string;
};

function toPercentString(value: number): string {
  const raw = (value * 100).toFixed(2);
  return raw.replace(/\.00$/, "");
}

function parsePercentInput(value: string): number | null {
  const text = value.trim();
  if (!text) return null;
  const normalized = text.replace(",", ".");
  const numeric = Number(normalized);
  if (!Number.isFinite(numeric)) return null;
  if (numeric < 0 || numeric > 100) return null;
  return numeric / 100;
}

function isPercentTextShapeValid(value: string): boolean {
  const text = value.trim();
  if (!text) return false;
  return /^\d{1,3}([.,]\d{1,2})?$/.test(text);
}

function formatRatePercent(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

export default function FeesPage() {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const safeToken = token || "";
  const pushToast = useToastStore((state) => state.push);

  const canEditFeeConfig = user?.role === "admin" || user?.role === "fund_manager";

  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [totalNavDigits, setTotalNavDigits] = useState("");
  const [totalNavOverflow, setTotalNavOverflow] = useState(false);
  const [previewSnapshot, setPreviewSnapshot] = useState<PreviewSnapshot | null>(null);
  const [confirmApplyOpen, setConfirmApplyOpen] = useState(false);
  const [acknowledgeRisk, setAcknowledgeRisk] = useState(false);
  const [acknowledgeBackup, setAcknowledgeBackup] = useState(false);

  const [globalDraft, setGlobalDraft] = useState<{
    performance?: string;
    hurdle?: string;
  }>({});

  const [selectedInvestorId, setSelectedInvestorId] = useState("");
  const [overrideDraft, setOverrideDraft] = useState<{
    performance?: string;
    hurdle?: string;
  }>({});

  const totalNav = digitsToNumber(totalNavDigits);

  const flagsQuery = useQuery({
    queryKey: queryKeys.featureFlags(safeToken),
    queryFn: () => apiClient.featureFlags(safeToken),
    enabled: !!token,
  });

  const safetyEnabled = flagsQuery.data?.fee_safety ?? true;

  const historyQuery = useQuery({
    queryKey: queryKeys.feeHistory(safeToken),
    queryFn: () => apiClient.feeHistory(safeToken),
    enabled: !!token,
  });

  const feeConfigQuery = useQuery({
    queryKey: queryKeys.feeConfig(safeToken),
    queryFn: () => apiClient.feeConfig(safeToken),
    enabled: !!token,
  });

  const investorsQuery = useQuery({
    queryKey: queryKeys.investorOptions(safeToken),
    queryFn: () => apiClient.investorCards(safeToken),
    enabled: !!token,
  });

  const configDigest = useMemo(() => JSON.stringify(feeConfigQuery.data ?? null), [feeConfigQuery.data]);

  const overrideMap = useMemo(() => {
    const map = new Map<number, { performance_fee_rate: number | null; hurdle_rate_annual: number | null }>();
    for (const row of feeConfigQuery.data?.overrides ?? []) {
      map.set(row.investor_id, {
        performance_fee_rate: row.performance_fee_rate,
        hurdle_rate_annual: row.hurdle_rate_annual,
      });
    }
    return map;
  }, [feeConfigQuery.data]);

  const previewMutation = useMutation({
    mutationFn: () =>
      apiClient.previewFees(safeToken, {
        end_date: endDate,
        total_nav: totalNav || 0,
      }),
    onSuccess: () => {
      setPreviewSnapshot({ endDate, totalNavDigits, configDigest });
      pushToast({ title: "Đã cập nhật bản xem trước phí", variant: "success" });
    },
    onError: (error) =>
      pushToast({
        title: "Không thể xem trước phí",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      }),
  });

  const applyMutation = useMutation({
    mutationFn: () => {
      const previewData = previewMutation.data;
      if (!previewData) {
        throw new Error("Cần xem trước trước khi áp dụng phí.");
      }
      return apiClient.applyFees(safeToken, {
        year: Number(year),
        end_date: endDate,
        total_nav: totalNav || 0,
        confirm_token: previewData.confirm_token,
        acknowledge_risk: safetyEnabled ? acknowledgeRisk : true,
        acknowledge_backup: safetyEnabled ? acknowledgeBackup : true,
      });
    },
    onSuccess: async () => {
      setConfirmApplyOpen(false);
      pushToast({ title: "Đã áp dụng phí thành công", variant: "success" });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.feeHistory(safeToken), exact: true }),
        queryClient.invalidateQueries({ queryKey: queryKeys.dashboard(safeToken), exact: true }),
      ]);
    },
    onError: (error) =>
      pushToast({
        title: "Không thể áp dụng phí",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      }),
  });

  const updateGlobalConfigMutation = useMutation({
    mutationFn: (payload: { performance_fee_rate: number; hurdle_rate_annual: number }) =>
      apiClient.updateGlobalFeeConfig(safeToken, payload),
    onSuccess: async () => {
      setPreviewSnapshot(null);
      setGlobalDraft({});
      pushToast({ title: "Đã cập nhật cấu hình phí mặc định", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: queryKeys.feeConfig(safeToken), exact: true });
    },
    onError: (error) =>
      pushToast({
        title: "Không thể cập nhật cấu hình phí",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      }),
  });

  const upsertOverrideMutation = useMutation({
    mutationFn: (payload: {
      investorId: number;
      performance_fee_rate?: number;
      hurdle_rate_annual?: number;
    }) => apiClient.upsertInvestorFeeOverride(safeToken, payload.investorId, payload),
    onSuccess: async () => {
      setPreviewSnapshot(null);
      setOverrideDraft({});
      pushToast({ title: "Đã lưu override phí nhà đầu tư", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: queryKeys.feeConfig(safeToken), exact: true });
    },
    onError: (error) =>
      pushToast({
        title: "Không thể lưu override phí",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      }),
  });

  const deleteOverrideMutation = useMutation({
    mutationFn: (investorId: number) => apiClient.deleteInvestorFeeOverride(safeToken, investorId),
    onSuccess: async () => {
      setPreviewSnapshot(null);
      pushToast({ title: "Đã xóa override phí nhà đầu tư", variant: "success" });
      await queryClient.invalidateQueries({ queryKey: queryKeys.feeConfig(safeToken), exact: true });
    },
    onError: (error) =>
      pushToast({
        title: "Không thể xóa override phí",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      }),
  });

  const hasPreview = Boolean(previewMutation.data);
  const previewMatchesInput =
    previewSnapshot?.endDate === endDate &&
    previewSnapshot?.totalNavDigits === totalNavDigits &&
    previewSnapshot?.configDigest === configDigest;

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

  const selectedInvestorIdNumber = Number(selectedInvestorId);
  const selectedOverride = Number.isFinite(selectedInvestorIdNumber)
    ? overrideMap.get(selectedInvestorIdNumber)
    : undefined;
  const globalPerformancePercent =
    globalDraft.performance ??
    (feeConfigQuery.data ? toPercentString(feeConfigQuery.data.global_config.performance_fee_rate) : "");
  const globalHurdlePercent =
    globalDraft.hurdle ??
    (feeConfigQuery.data ? toPercentString(feeConfigQuery.data.global_config.hurdle_rate_annual) : "");
  const overridePerformancePercent =
    overrideDraft.performance ??
    (selectedOverride?.performance_fee_rate !== null && selectedOverride?.performance_fee_rate !== undefined
      ? toPercentString(selectedOverride.performance_fee_rate)
      : "");
  const overrideHurdlePercent =
    overrideDraft.hurdle ??
    (selectedOverride?.hurdle_rate_annual !== null && selectedOverride?.hurdle_rate_annual !== undefined
      ? toPercentString(selectedOverride.hurdle_rate_annual)
      : "");

  const globalPerfDecimal = parsePercentInput(globalPerformancePercent);
  const globalHurdleDecimal = parsePercentInput(globalHurdlePercent);
  const canSaveGlobal =
    canEditFeeConfig &&
    isPercentTextShapeValid(globalPerformancePercent) &&
    isPercentTextShapeValid(globalHurdlePercent) &&
    globalPerfDecimal !== null &&
    globalHurdleDecimal !== null &&
    !updateGlobalConfigMutation.isPending;

  const hasSelectedInvestor = Number.isFinite(selectedInvestorIdNumber) && selectedInvestorIdNumber > 0;
  const overridePerfProvided = overridePerformancePercent.trim().length > 0;
  const overrideHurdleProvided = overrideHurdlePercent.trim().length > 0;
  const overridePerfDecimal = overridePerfProvided ? parsePercentInput(overridePerformancePercent) : null;
  const overrideHurdleDecimal = overrideHurdleProvided ? parsePercentInput(overrideHurdlePercent) : null;
  const overridePerfValid = !overridePerfProvided || (isPercentTextShapeValid(overridePerformancePercent) && overridePerfDecimal !== null);
  const overrideHurdleValid = !overrideHurdleProvided || (isPercentTextShapeValid(overrideHurdlePercent) && overrideHurdleDecimal !== null);
  const canSaveOverride =
    canEditFeeConfig &&
    hasSelectedInvestor &&
    (overridePerfProvided || overrideHurdleProvided) &&
    overridePerfValid &&
    overrideHurdleValid &&
    !upsertOverrideMutation.isPending;

  const investorNameById = useMemo(() => {
    const map = new Map<number, string>();
    for (const row of investorsQuery.data ?? []) {
      map.set(row.id, row.display_name);
    }
    return map;
  }, [investorsQuery.data]);

  return (
    <div className="app-page">
      <Card className="space-y-3">
        <h2 className="section-title">Cấu hình phí</h2>
        {feeConfigQuery.isLoading ? (
          <LoadingState label="Đang tải cấu hình phí..." />
        ) : feeConfigQuery.isError ? (
          <ErrorState message="Không tải được cấu hình phí." />
        ) : feeConfigQuery.data ? (
          <div className="space-y-3">
            <div className="grid gap-2 sm:grid-cols-2">
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2 text-sm">
                <p className="text-xs text-[var(--color-muted)]">Performance fee mặc định</p>
                <p className="font-semibold">{formatRatePercent(feeConfigQuery.data.global_config.performance_fee_rate)}</p>
              </div>
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2 text-sm">
                <p className="text-xs text-[var(--color-muted)]">Hurdle mặc định / năm</p>
                <p className="font-semibold">{formatRatePercent(feeConfigQuery.data.global_config.hurdle_rate_annual)}</p>
              </div>
            </div>

            {canEditFeeConfig ? (
              <div className="space-y-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3">
                <h3 className="text-sm font-semibold">Cập nhật cấu hình mặc định</h3>
                <div className="grid gap-2 sm:grid-cols-3">
                  <Input
                    value={globalPerformancePercent}
                    onChange={(e) =>
                      setGlobalDraft((prev) => ({
                        ...prev,
                        performance: e.target.value,
                      }))
                    }
                    placeholder="Performance fee %"
                  />
                  <Input
                    value={globalHurdlePercent}
                    onChange={(e) =>
                      setGlobalDraft((prev) => ({
                        ...prev,
                        hurdle: e.target.value,
                      }))
                    }
                    placeholder="Hurdle % / năm"
                  />
                  <Button
                    onClick={() => {
                      if (globalPerfDecimal === null || globalHurdleDecimal === null) return;
                      updateGlobalConfigMutation.mutate({
                        performance_fee_rate: globalPerfDecimal,
                        hurdle_rate_annual: globalHurdleDecimal,
                      });
                    }}
                    disabled={!canSaveGlobal}
                  >
                    Lưu mặc định
                  </Button>
                </div>
                <p className="input-helper">Giá trị nhập theo phần trăm 0..100 (tối đa 2 chữ số thập phân).</p>
              </div>
            ) : null}

            <div className="space-y-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3">
              <h3 className="text-sm font-semibold">Override theo nhà đầu tư</h3>
              {canEditFeeConfig ? (
                <div className="grid gap-2 sm:grid-cols-4">
                  <select
                    value={selectedInvestorId}
                    onChange={(e) => {
                      setSelectedInvestorId(e.target.value);
                      setOverrideDraft({});
                    }}
                    className="min-h-11 rounded-[var(--radius-control)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]"
                  >
                    <option value="">Chọn nhà đầu tư</option>
                    {(investorsQuery.data ?? []).map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.display_name}
                      </option>
                    ))}
                  </select>
                  <Input
                    value={overridePerformancePercent}
                    onChange={(e) =>
                      setOverrideDraft((prev) => ({
                        ...prev,
                        performance: e.target.value,
                      }))
                    }
                    placeholder="Performance fee %"
                  />
                  <Input
                    value={overrideHurdlePercent}
                    onChange={(e) =>
                      setOverrideDraft((prev) => ({
                        ...prev,
                        hurdle: e.target.value,
                      }))
                    }
                    placeholder="Hurdle % / năm"
                  />
                  <Button
                    onClick={() => {
                      if (!hasSelectedInvestor) return;
                      const payload: { performance_fee_rate?: number; hurdle_rate_annual?: number } = {};
                      if (overridePerfProvided && overridePerfDecimal !== null) {
                        payload.performance_fee_rate = overridePerfDecimal;
                      }
                      if (overrideHurdleProvided && overrideHurdleDecimal !== null) {
                        payload.hurdle_rate_annual = overrideHurdleDecimal;
                      }
                      upsertOverrideMutation.mutate({
                        investorId: selectedInvestorIdNumber,
                        ...payload,
                      });
                    }}
                    disabled={!canSaveOverride}
                  >
                    Lưu override
                  </Button>
                </div>
              ) : null}

              {feeConfigQuery.data.overrides.length ? (
                <div className="list-stagger space-y-2">
                  {feeConfigQuery.data.overrides.map((row) => (
                    <article
                      key={row.investor_id}
                      className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-3"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <p className="text-sm font-semibold">
                            {investorNameById.get(row.investor_id) ?? `Nhà đầu tư #${row.investor_id}`}
                          </p>
                          <p className="text-xs text-[var(--color-muted)]">
                            Performance:{" "}
                            {row.performance_fee_rate !== null
                              ? formatRatePercent(row.performance_fee_rate)
                              : "Theo mặc định"}
                            {" | "}
                            Hurdle:{" "}
                            {row.hurdle_rate_annual !== null
                              ? formatRatePercent(row.hurdle_rate_annual)
                              : "Theo mặc định"}
                          </p>
                        </div>
                        {canEditFeeConfig ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteOverrideMutation.mutate(row.investor_id)}
                            disabled={deleteOverrideMutation.isPending}
                          >
                            Xóa
                          </Button>
                        ) : null}
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <EmptyState title="Chưa có override phí." />
              )}
            </div>
          </div>
        ) : null}
      </Card>

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
        <p className="input-helper">Giá trị NAV gửi tính phí: {totalNav ? formatCurrency(totalNav) : "Chưa có"}</p>
        {totalNavOverflow ? <p className="inline-error">Tổng NAV quá lớn (tối đa 15 chữ số).</p> : null}
        {!previewMatchesInput && hasPreview ? (
          <p className="status-warning">
            Dữ liệu đầu vào hoặc cấu hình phí đã thay đổi sau lần xem trước gần nhất. Bấm xem trước lại để đồng bộ mã xác nhận.
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

        <div className="grid grid-cols-2 gap-2">
          <Button variant="secondary" onClick={() => previewMutation.mutate()} disabled={!canPreview}>
            {previewMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Xem trước
          </Button>
          <Button onClick={() => setConfirmApplyOpen(true)} disabled={!canApply}>
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
                <p className="text-xs text-[var(--color-muted)]">
                  Config áp dụng: Perf {formatRatePercent(fee.applied_performance_fee_rate)} | Hurdle{" "}
                  {formatRatePercent(fee.applied_hurdle_rate)} | Nguồn{" "}
                  {fee.fee_source === "override" ? "Override" : "Global"}
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

      <ConfirmDialog
        open={confirmApplyOpen}
        onOpenChange={setConfirmApplyOpen}
        title="Xác nhận áp dụng phí"
        description="Hệ thống sẽ ghi nhận bút toán phí theo dữ liệu xem trước hiện tại. Bạn có chắc muốn tiếp tục?"
        confirmLabel="Áp dụng phí"
        onConfirm={() => applyMutation.mutate()}
        isPending={applyMutation.isPending}
      />
    </div>
  );
}
