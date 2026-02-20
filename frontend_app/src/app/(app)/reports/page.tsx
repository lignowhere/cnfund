"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { DateRangePicker } from "@/components/form/date-range-picker";
import { InvestorCombobox } from "@/components/form/investor-combobox";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { apiClient } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import type { InvestorSelectOption } from "@/lib/types";
import { formatCurrency, formatDateTime, formatPercent } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";
import { useToastStore } from "@/store/toast-store";

const ReportsTxTypeBarChart = dynamic(
  () => import("@/components/charts/reports-charts").then((module) => module.ReportsTxTypeBarChart),
  { ssr: false },
);

const ReportsTxTypeStackedBarChart = dynamic(
  () =>
    import("@/components/charts/reports-charts").then((module) => module.ReportsTxTypeStackedBarChart),
  { ssr: false },
);

const ReportsInvestorTxBarChart = dynamic(
  () => import("@/components/charts/reports-charts").then((module) => module.ReportsInvestorTxBarChart),
  { ssr: false },
);

const COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "var(--chart-6)",
];

function toInvestorOption(displayName: string, id: number): InvestorSelectOption {
  const plainName = displayName.replace(/\s*\(ID:\s*\d+\)\s*$/i, "").trim();
  const label = `${plainName || displayName} · ID ${id}`;
  return {
    id,
    displayName: label,
    searchText: `${displayName} ${plainName} ${id}`,
  };
}

function formatCompactMoney(value: number) {
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`;
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  return `${Math.round(value / 1_000)}K`;
}

export default function ReportsPage() {
  const token = useAuthStore((state) => state.accessToken);
  const safeToken = token || "";
  const pushToast = useToastStore((state) => state.push);

  const [txPage, setTxPage] = useState(1);
  const [txTypeFilter, setTxTypeFilter] = useState("");
  const [investorFilter, setInvestorFilter] = useState<InvestorSelectOption | null>(null);
  const [dateRange, setDateRange] = useState<{ startDate: string; endDate: string }>({
    startDate: "",
    endDate: "",
  });
  const [isExporting, setIsExporting] = useState(false);

  const investorsQuery = useQuery({
    queryKey: queryKeys.investorOptions(safeToken),
    queryFn: async () => {
      const investors = await apiClient.investorCards(safeToken);
      return investors.map((item) => toInvestorOption(item.display_name, item.id));
    },
    enabled: !!token,
  });

  const effectiveInvestorId = investorFilter?.id ?? 0;

  const txReportQuery = useQuery({
    queryKey: queryKeys.transactionsReport(safeToken, {
      page: txPage,
      pageSize: 20,
      txType: txTypeFilter || undefined,
      investorId: investorFilter?.id,
      startDate: dateRange.startDate || undefined,
      endDate: dateRange.endDate || undefined,
    }),
    queryFn: () =>
      apiClient.transactionsReport(safeToken, {
        page: txPage,
        page_size: 20,
        tx_type: txTypeFilter || undefined,
        investor_id: investorFilter?.id,
        start_date: dateRange.startDate || undefined,
        end_date: dateRange.endDate || undefined,
      }),
    enabled: !!token,
  });

  const investorReportQuery = useQuery({
    queryKey: queryKeys.investorReport(safeToken, effectiveInvestorId),
    queryFn: () => apiClient.investorReport(safeToken, effectiveInvestorId),
    enabled: !!token && !!investorFilter?.id,
  });

  const navHistoryQuery = useQuery({
    queryKey: ["navHistory", safeToken],
    queryFn: () => apiClient.navHistory(safeToken),
    enabled: !!token && !investorFilter,
  });

  const txTotalPages = useMemo(() => {
    if (!txReportQuery.data) return 1;
    return Math.max(1, Math.ceil(txReportQuery.data.total / txReportQuery.data.page_size));
  }, [txReportQuery.data]);

  const txTypeChartData = useMemo(() => {
    if (!txReportQuery.data) return { simple: [], stacked: [], colors: {} };

    const valueByType: Record<string, number> = {};
    for (const tx of txReportQuery.data.items) {
      valueByType[tx.type] = (valueByType[tx.type] || 0) + tx.amount;
    }

    const simple = Object.entries(valueByType)
      .map(([name, value], index) => {
        const normalized = name.toLowerCase();
        let color = COLORS[index % COLORS.length];
        if (normalized.includes("nap") || normalized.includes("deposit")) {
          color = "var(--color-success)";
        } else if (
          normalized.includes("rut") ||
          normalized.includes("withdraw") ||
          normalized.includes("rat")
        ) {
          color = "var(--color-danger)";
        }
        return { name, value, color };
      })
      .sort((a, b) => Math.abs(b.value) - Math.abs(a.value));

    const stacked: Array<{ name: string;[key: string]: number | string }> = [];
    const investorColors: Record<string, string> = {};

    if (!investorFilter && txReportQuery.data.items.length > 0) {
      const depositByInvestor: Record<string, number> = {};
      const withdrawByInvestor: Record<string, number> = {};

      for (const tx of txReportQuery.data.items) {
        const normalizedType = tx.type.toLowerCase();
        const isDeposit = normalizedType.includes("nap") || normalizedType.includes("deposit");
        const isWithdraw =
          normalizedType.includes("rut") ||
          normalizedType.includes("withdraw") ||
          normalizedType.includes("rat");

        if (isDeposit) {
          depositByInvestor[tx.investor_name] = (depositByInvestor[tx.investor_name] || 0) + tx.amount;
        }
        if (isWithdraw) {
          withdrawByInvestor[tx.investor_name] = (withdrawByInvestor[tx.investor_name] || 0) + tx.amount;
        }
      }

      const allInvestors = new Set([
        ...Object.keys(depositByInvestor),
        ...Object.keys(withdrawByInvestor),
      ]);

      const investorList = Array.from(allInvestors).slice(0, 6);
      investorList.forEach((investor, index) => {
        investorColors[investor] = COLORS[index % COLORS.length];
      });

      if (Object.keys(depositByInvestor).length > 0) {
        const depositRow: { name: string;[key: string]: number | string } = { name: "Nạp tiền" };
        for (const investor of investorList) {
          depositRow[investor] = depositByInvestor[investor] || 0;
        }
        stacked.push(depositRow);
      }

      if (Object.keys(withdrawByInvestor).length > 0) {
        const withdrawRow: { name: string;[key: string]: number | string } = { name: "Rút tiền" };
        for (const investor of investorList) {
          withdrawRow[investor] = withdrawByInvestor[investor] || 0;
        }
        stacked.push(withdrawRow);
      }
    }

    return { simple, stacked, colors: investorColors };
  }, [txReportQuery.data, investorFilter]);

  const investorTxBars = useMemo(() => {
    if (!investorReportQuery.data) return [];
    return investorReportQuery.data.transactions
      .slice(0, 12)
      .reverse()
      .map((row) => ({
        time: new Date(row.date).toLocaleDateString("vi-VN"),
        amount: row.amount,
      }));
  }, [investorReportQuery.data]);

  const endAUM = useMemo(() => {
    if (investorFilter) return null;
    if (dateRange.endDate && navHistoryQuery.data) {
      const sorted = [...navHistoryQuery.data].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
      const found = sorted.find(p => p.date <= dateRange.endDate);
      if (found) return found.nav;
    }
    if (txReportQuery.data?.items?.[0]) {
      return txReportQuery.data.items[0].nav;
    }
    return 0;
  }, [dateRange.endDate, navHistoryQuery.data, txReportQuery.data, investorFilter]);

  async function handleExport(format: "csv" | "pdf") {
    if (!token || isExporting) {
      return;
    }
    setIsExporting(true);
    try {
      const blob = await apiClient.exportTransactions(token, {
        start_date: dateRange.startDate || undefined,
        end_date: dateRange.endDate || undefined,
        investor_id: investorFilter?.id,
        tx_type: txTypeFilter || undefined,
        format,
      });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `cnfund-report-${new Date().toISOString().split("T")[0]}.${format}`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
      pushToast({
        title: `Đã xuất file ${format.toUpperCase()}`,
        variant: "success",
      });
    } catch (error) {
      pushToast({
        title: "Không thể xuất báo cáo",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      });
    } finally {
      setIsExporting(false);
    }
  }

  const showInvestorDetail = !!investorFilter?.id;

  return (
    <div className="app-page">
      <Card className="space-y-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="section-title">
              {showInvestorDetail ? "Chi tiết Nhà đầu tư" : "Báo cáo Tổng hợp"}
            </h2>
            <p className="section-note">
              {showInvestorDetail
                ? `Đang xem dữ liệu của: ${investorFilter?.displayName.split("·")[0]}`
                : "Tổng quan giao dịch toàn quỹ"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              onClick={() => handleExport("csv")}
              disabled={txReportQuery.isFetching || isExporting}
            >
              Xuất CSV
            </Button>
            <Button
              variant="secondary"
              onClick={() => handleExport("pdf")}
              disabled={txReportQuery.isFetching || isExporting}
            >
              Xuất PDF
            </Button>
          </div>
        </div>

        {/* Global Filters */}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <InvestorCombobox
            options={investorsQuery.data ?? []}
            value={investorFilter?.id ?? null}
            onChange={(option) => {
              setTxPage(1);
              setInvestorFilter(option);
            }}
            placeholder="Chọn nhà đầu tư..."
            allowClear
          />
          <Select
            value={txTypeFilter}
            onChange={(e) => {
              setTxPage(1);
              setTxTypeFilter(e.target.value);
            }}
          >
            <option value="">Tất cả loại giao dịch</option>
            <option value="deposit">Nạp tiền (Deposit)</option>
            <option value="withdraw">Rút tiền (Withdraw)</option>
            <option value="fee">Thu phí (Fee)</option>
            <option value="nav_update">Cập nhật NAV (NAV Update)</option>
          </Select>
          <div className="sm:col-span-2 lg:col-span-2">
            <DateRangePicker
              startDate={dateRange.startDate}
              endDate={dateRange.endDate}
              onChange={(nextValue) => {
                setTxPage(1);
                setDateRange(nextValue);
              }}
              disabled={txReportQuery.isFetching || isExporting}
            />
          </div>
        </div>

        {/* Dynamic Content Area */}
        {txReportQuery.isLoading ? (
          <LoadingState label="Đang tải dữ liệu báo cáo..." />
        ) : txReportQuery.isError ? (
          <ErrorState message="Không tải được dữ liệu báo cáo." />
        ) : txReportQuery.data ? (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2">

            {/* KPI Metrics - ALWAYS PERIOD AWARE */}
            <div className={`grid grid-cols-1 gap-3 sm:grid-cols-2 ${showInvestorDetail ? "lg:grid-cols-4" : "xl:grid-cols-6"}`}>

              {/* ASSET KPI */}
              <div className="rounded-xl bg-[var(--color-surface-2)] px-4 py-3">
                <p className="kpi-label">{showInvestorDetail ? "Tài sản (Cuối kỳ)" : "Tổng tài sản (AUM kỳ)"}</p>
                <p className="kpi-value">
                  {showInvestorDetail
                    ? formatCurrency(investorReportQuery.data?.current_balance || 0)
                    : formatCurrency(endAUM || 0)
                  }
                </p>
                {!dateRange.endDate && <p className="text-[10px] text-[var(--color-muted)] mt-1">* Theo NAV mới nhất</p>}
              </div>

              {/* PROFIT KPI - PERIOD AWARE */}
              <div className="rounded-xl bg-[var(--color-surface-2)] px-4 py-3">
                <p className="kpi-label">Lãi/Lỗ ròng (Kỳ chọn)</p>
                <div className={`kpi-value ${txReportQuery.data.summary.gross_profit_loss >= 0 ? "text-[var(--color-success)]" : "text-[var(--color-danger)]"}`}>
                  {formatCurrency(txReportQuery.data.summary.gross_profit_loss)}
                </div>
              </div>

              {/* PERFORMANCE KPI - PERIOD AWARE */}
              <div className="rounded-xl bg-[var(--color-surface-2)] px-4 py-3">
                <p className="kpi-label">Hiệu suất (Kỳ chọn)</p>
                <div className={`kpi-value ${txReportQuery.data.summary.gross_profit_loss_percent >= 0 ? "text-[var(--color-success)]" : "text-[var(--color-danger)]"}`}>
                  {formatPercent(txReportQuery.data.summary.gross_profit_loss_percent)}
                </div>
              </div>

              {/* DEPOSIT KPI */}
              <div className="rounded-xl bg-[var(--color-surface-2)] px-4 py-3">
                <p className="kpi-label">Tổng nạp (Kỳ chọn)</p>
                <p className="kpi-value text-[var(--color-success)]">
                  {formatCurrency(txReportQuery.data.summary.total_deposits)}
                </p>
              </div>

              {/* CONDITIONAL KPIS */}
              {!showInvestorDetail && (
                <>
                  <div className="rounded-xl bg-[var(--color-surface-2)] px-4 py-3">
                    <p className="kpi-label">Tổng rút (Kỳ chọn)</p>
                    <p className="kpi-value text-[var(--color-danger)]">
                      {formatCurrency(txReportQuery.data.summary.total_withdrawals)}
                    </p>
                  </div>
                  <div className="rounded-xl bg-[var(--color-surface-2)] px-4 py-3">
                    <p className="kpi-label">Tổng giao dịch</p>
                    <p className="kpi-value">{txReportQuery.data.summary.total_count}</p>
                  </div>
                </>
              )}

              {showInvestorDetail && (
                <div className="rounded-xl bg-[var(--color-surface-2)] px-4 py-3 border border-[var(--color-border)]">
                  <p className="kpi-label">Lãi/Lỗ trọn đời</p>
                  <p className={`kpi-value ${investorReportQuery.data?.current_profit && investorReportQuery.data.current_profit >= 0 ? "text-[var(--color-success)]" : "text-[var(--color-danger)]"}`}>
                    {investorReportQuery.data ? formatCurrency(investorReportQuery.data.current_profit) : "---"}
                  </p>
                </div>
              )}
            </div>

            {/* CHARTS AREA */}
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <div className="h-72 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-2">
                <h3 className="mb-2 px-2 text-sm font-semibold">
                  {showInvestorDetail ? "Biến động tài sản" : "Phân bổ loại giao dịch"}
                </h3>
                {showInvestorDetail ? (
                  <ReportsInvestorTxBarChart data={investorTxBars} formatCompactMoney={formatCompactMoney} />
                ) : (
                  !investorFilter && txTypeChartData.stacked.length > 0 ? (
                    <ReportsTxTypeStackedBarChart data={txTypeChartData.stacked} colors={txTypeChartData.colors} />
                  ) : (
                    <ReportsTxTypeBarChart data={txTypeChartData.simple} />
                  )
                )}
              </div>

              {/* CONTEXT AREA (Fees or Transactions Summary) */}
              <div className="flex flex-col gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-4">
                {showInvestorDetail ? (
                  <>
                    <h3 className="text-sm font-semibold">Lịch sử phí gần nhất</h3>
                    {investorReportQuery.data?.fee_history && investorReportQuery.data.fee_history.length > 0 ? (
                      <div className="space-y-2">
                        {investorReportQuery.data.fee_history.slice(0, 5).map((item) => (
                          <div key={item.id} className="flex justify-between border-b border-[var(--color-border)] pb-2 last:border-0 last:pb-0">
                            <div>
                              <p className="text-sm">{item.period}</p>
                              <p className="text-xs text-[var(--color-muted)]">{item.calculation_date}</p>
                            </div>
                            <p className="font-medium">{formatCurrency(item.fee_amount)}</p>
                          </div>
                        ))}
                      </div>
                    ) : <p className="text-sm text-[var(--color-muted)] pt-2">Chưa có dữ liệu phí.</p>}
                  </>
                ) : (
                  <>
                    <h3 className="text-sm font-semibold">Tóm tắt phân bổ</h3>
                    <div className="space-y-2 pt-2">
                      {txTypeChartData.simple.map((t, idx) => (
                        <div key={idx} className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <div className="h-3 w-3 rounded-full" style={{ backgroundColor: t.color }} />
                            <span>{t.name}</span>
                          </div>
                          <span className="font-medium">{formatCurrency(t.value)}</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* LỊCH SỬ CHI TIẾT */}
            <div className="pt-4 border-t border-[var(--color-border)]">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-base font-semibold">Lịch sử giao dịch chi tiết</h3>
                <span className="text-xs text-[var(--color-muted)]">Trang {txPage}/{txTotalPages}</span>
              </div>

              {txReportQuery.data.items.length ? (
                <div className="space-y-2">
                  {txReportQuery.data.items.map((tx) => (
                    <div
                      key={tx.id}
                      className="flex items-center justify-between rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3 transition-colors hover:bg-[var(--color-surface-3)]"
                    >
                      <div className="space-y-1">
                        <p className="text-sm font-medium">{tx.investor_name}</p>
                        <div className="flex items-center gap-2 text-xs text-[var(--color-muted)]">
                          <span className={`font-semibold ${tx.type.toLowerCase().includes("deposit") || tx.type.toLowerCase().includes("nạp")
                            ? "text-[var(--color-success)]"
                            : tx.type.toLowerCase().includes("withdraw") || tx.type.toLowerCase().includes("rút")
                              ? "text-[var(--color-danger)]"
                              : ""
                            }`}>
                            {tx.type}
                          </span>
                          <span>•</span>
                          <span>{formatDateTime(tx.date)}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`text-sm font-semibold ${tx.type.toLowerCase().includes("deposit") || tx.type.toLowerCase().includes("nạp")
                          ? "text-[var(--color-success)]"
                          : tx.type.toLowerCase().includes("withdraw") || tx.type.toLowerCase().includes("rút")
                            ? "text-[var(--color-danger)]"
                            : ""
                          }`}>
                          {formatCurrency(tx.amount)}
                        </p>
                        <p className="text-xs text-[var(--color-muted)]">NAV: {formatCurrency(tx.nav)}</p>
                      </div>
                    </div>
                  ))}

                  <div className="mt-4 flex gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setTxPage((prev) => Math.max(1, prev - 1))}
                      disabled={txPage <= 1}
                    >
                      Trước
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setTxPage((prev) => Math.min(txTotalPages, prev + 1))}
                      disabled={txPage >= txTotalPages}
                      className="ml-auto"
                    >
                      Sau
                    </Button>
                  </div>
                </div>
              ) : (
                <EmptyState title="Không tìm thấy giao dịch nào." />
              )}
            </div>
          </div>
        ) : null}
      </Card>
    </div>
  );
}
