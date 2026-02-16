"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { InvestorCombobox } from "@/components/form/investor-combobox";
import { MoneyInput } from "@/components/form/money-input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { apiClient } from "@/lib/api";
import { digitsToNumber } from "@/lib/number-input";
import { queryKeys } from "@/lib/query-keys";
import type { InvestorSelectOption } from "@/lib/types";
import { formatCurrency, formatDateTime, formatPercent } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";

const ReportsTxTypePieChart = dynamic(
  () => import("@/components/charts/reports-charts").then((module) => module.ReportsTxTypePieChart),
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

  const [txPage, setTxPage] = useState(1);
  const [txTypeFilter, setTxTypeFilter] = useState("");
  const [investorFilter, setInvestorFilter] = useState<InvestorSelectOption | null>(null);
  const [reportInvestorId, setReportInvestorId] = useState<number | null>(null);
  const [reportNavDigits, setReportNavDigits] = useState("");
  const [reportNavOverflow, setReportNavOverflow] = useState(false);

  const reportNav = digitsToNumber(reportNavDigits);

  const investorsQuery = useQuery({
    queryKey: queryKeys.investorOptions(safeToken),
    queryFn: async () => {
      const investors = await apiClient.investorCards(safeToken);
      return investors.map((item) => toInvestorOption(item.display_name, item.id));
    },
    enabled: !!token,
  });

  const effectiveInvestorId = reportInvestorId ?? investorsQuery.data?.[0]?.id ?? 0;

  const txReportQuery = useQuery({
    queryKey: queryKeys.transactionsReport(safeToken, {
      page: txPage,
      pageSize: 20,
      txType: txTypeFilter || undefined,
      investorId: investorFilter?.id,
    }),
    queryFn: () =>
      apiClient.transactionsReport(safeToken, {
        page: txPage,
        page_size: 20,
        tx_type: txTypeFilter || undefined,
        investor_id: investorFilter?.id,
      }),
    enabled: !!token,
  });

  const investorReportQuery = useQuery({
    queryKey: queryKeys.investorReport(safeToken, effectiveInvestorId, reportNav || undefined),
    queryFn: () => apiClient.investorReport(safeToken, effectiveInvestorId, reportNav || undefined),
    enabled: !!token && effectiveInvestorId > 0,
  });

  const txTotalPages = useMemo(() => {
    if (!txReportQuery.data) return 1;
    return Math.max(1, Math.ceil(txReportQuery.data.total / txReportQuery.data.page_size));
  }, [txReportQuery.data]);

  const txTypeChartData = useMemo(() => {
    if (!txReportQuery.data) return [];
    return Object.entries(txReportQuery.data.summary.by_type).map(([name, value], index) => ({
      name,
      value,
      color: COLORS[index % COLORS.length],
    }));
  }, [txReportQuery.data]);

  const investorTxBars = useMemo(() => {
    if (!investorReportQuery.data) return [];
    return investorReportQuery.data.transactions.slice(0, 12).map((row) => ({
      time: new Date(row.date).toLocaleDateString("vi-VN"),
      amount: row.amount,
    }));
  }, [investorReportQuery.data]);

  return (
    <div className="app-page">
      <Card className="space-y-3">
        <div className="flex items-center justify-between gap-2">
          <h2 className="section-title">Báo cáo giao dịch</h2>
          <p className="section-note">
            Trang {txPage}/{txTotalPages}
          </p>
        </div>

        <div className="grid gap-2 sm:grid-cols-3">
          <Input
            placeholder="Lọc theo loại (deposit, withdraw, fee...)"
            value={txTypeFilter}
            onChange={(e) => {
              setTxPage(1);
              setTxTypeFilter(e.target.value);
            }}
          />
          <InvestorCombobox
            options={investorsQuery.data ?? []}
            value={investorFilter?.id ?? null}
            onChange={(option) => {
              setTxPage(1);
              setInvestorFilter(option);
            }}
            placeholder="Lọc nhà đầu tư theo tên hoặc ID"
            allowClear
          />
          <Button variant="secondary" onClick={() => txReportQuery.refetch()} disabled={txReportQuery.isFetching}>
            Làm mới
          </Button>
        </div>

        {txReportQuery.isLoading ? (
          <LoadingState label="Đang tải báo cáo giao dịch..." />
        ) : txReportQuery.isError ? (
          <ErrorState message="Không tải được báo cáo giao dịch." />
        ) : txReportQuery.data ? (
          <div className="space-y-3">
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-4">
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2">
                <p className="kpi-label">Tổng giao dịch</p>
                <p className="kpi-value">{txReportQuery.data.summary.total_count}</p>
              </div>
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2">
                <p className="kpi-label">Tổng giá trị</p>
                <p className="kpi-value">{formatCurrency(txReportQuery.data.summary.total_volume)}</p>
              </div>
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2">
                <p className="kpi-label">Dòng tiền ròng</p>
                <p className="kpi-value">{formatCurrency(txReportQuery.data.summary.net_cash_flow)}</p>
              </div>
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2">
                <p className="kpi-label">Số loại giao dịch</p>
                <p className="kpi-value">{txTypeChartData.length}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              <div className="h-64 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-2">
                <ReportsTxTypePieChart data={txTypeChartData} />
              </div>

              <div className="list-stagger space-y-2">
                {txReportQuery.data.items.length ? (
                  txReportQuery.data.items.slice(0, 6).map((tx) => (
                    <article
                      key={tx.id}
                      className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-semibold">{tx.investor_name}</p>
                        <p className="text-xs text-[var(--color-muted)]">#{tx.id}</p>
                      </div>
                      <p className="text-xs text-[var(--color-muted)]">
                        {tx.type} | {formatDateTime(tx.date)}
                      </p>
                      <p className="mt-1 text-sm">
                        {formatCurrency(tx.amount)} | NAV: {formatCurrency(tx.nav)}
                      </p>
                    </article>
                  ))
                ) : (
                  <EmptyState title="Không có giao dịch phù hợp bộ lọc." />
                )}
              </div>
            </div>

            <div className="flex items-center justify-between gap-2">
              <Button
                variant="secondary"
                className="flex-1"
                onClick={() => setTxPage((prev) => Math.max(1, prev - 1))}
                disabled={txPage <= 1}
              >
                Trang trước
              </Button>
              <Button
                variant="secondary"
                className="flex-1"
                onClick={() => setTxPage((prev) => Math.min(txTotalPages, prev + 1))}
                disabled={txPage >= txTotalPages}
              >
                Trang sau
              </Button>
            </div>
          </div>
        ) : null}
      </Card>

      <Card className="space-y-3">
        <h2 className="section-title">Báo cáo nhà đầu tư</h2>
        <div className="grid gap-2 sm:grid-cols-3">
          <InvestorCombobox
            options={investorsQuery.data ?? []}
            value={reportInvestorId ?? investorsQuery.data?.[0]?.id ?? null}
            onChange={(option) => setReportInvestorId(option?.id ?? null)}
            placeholder="Chọn nhà đầu tư theo tên hoặc ID"
          />
          <div>
            <MoneyInput
              value={reportNavDigits}
              onValueChange={(value) => {
                setReportNavDigits(value.rawDigits);
                setReportNavOverflow(value.isOverflow);
              }}
              placeholder="NAV tùy chọn"
            />
            <p className="input-helper">
              NAV dùng tính thử: {reportNav ? formatCurrency(reportNav) : "Theo NAV hiện tại"}
            </p>
            {reportNavOverflow ? <p className="inline-error">NAV quá lớn (tối đa 15 chữ số).</p> : null}
          </div>
          <Button
            variant="secondary"
            onClick={() => investorReportQuery.refetch()}
            disabled={investorReportQuery.isFetching || effectiveInvestorId <= 0 || reportNavOverflow}
          >
            Tải báo cáo
          </Button>
        </div>

        {investorReportQuery.isLoading ? (
          <LoadingState label="Đang tải báo cáo nhà đầu tư..." />
        ) : investorReportQuery.isError ? (
          <ErrorState message="Không tải được báo cáo nhà đầu tư." />
        ) : investorReportQuery.data ? (
          <div className="space-y-3">
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3">
              <p className="text-sm font-semibold">{investorReportQuery.data.investor.name}</p>
              <p className="text-xs text-[var(--color-muted)]">
                Ngày tham gia: {investorReportQuery.data.investor.join_date}
              </p>
            </div>

            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2">
                <p className="text-xs text-[var(--color-muted)]">Giá trị hiện tại</p>
                <p className="text-sm font-semibold">{formatCurrency(investorReportQuery.data.current_balance)}</p>
              </div>
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2">
                <p className="text-xs text-[var(--color-muted)]">Lãi/lỗ hiện tại</p>
                <p className="text-sm font-semibold">
                  {formatCurrency(investorReportQuery.data.current_profit)} (
                  {formatPercent(investorReportQuery.data.current_profit_perc)})
                </p>
              </div>
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2">
                <p className="text-xs text-[var(--color-muted)]">Tỷ suất lợi nhuận gộp</p>
                <p className="text-sm font-semibold">
                  {formatPercent(investorReportQuery.data.lifetime_performance.gross_return)}
                </p>
              </div>
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2">
                <p className="text-xs text-[var(--color-muted)]">Tỷ suất lợi nhuận ròng</p>
                <p className="text-sm font-semibold">
                  {formatPercent(investorReportQuery.data.lifetime_performance.net_return)}
                </p>
              </div>
            </div>

            <div className="h-64 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-2">
              <ReportsInvestorTxBarChart data={investorTxBars} formatCompactMoney={formatCompactMoney} />
            </div>

            <div className="list-stagger space-y-2">
              <p className="text-sm font-semibold">Lịch sử phí gần đây</p>
              {investorReportQuery.data.fee_history.length ? (
                investorReportQuery.data.fee_history.slice(0, 5).map((item) => (
                  <article
                    key={item.id}
                    className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3"
                  >
                    <p className="text-sm font-semibold">
                      {item.period} | {formatCurrency(item.fee_amount)}
                    </p>
                    <p className="text-xs text-[var(--color-muted)]">{item.calculation_date}</p>
                  </article>
                ))
              ) : (
                <EmptyState title="Nhà đầu tư chưa có lịch sử phí." />
              )}
            </div>
          </div>
        ) : (
          <EmptyState title="Chọn nhà đầu tư để xem báo cáo." />
        )}
      </Card>
    </div>
  );
}
