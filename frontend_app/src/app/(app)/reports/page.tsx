"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { apiClient } from "@/lib/api";
import { formatCurrency, formatDateTime, formatPercent } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";

const COLORS = ["#0f4c81", "#1b6ca8", "#2f86c4", "#5ba5d5", "#8dc3e4", "#b8daef"];

function formatCompactMoney(value: number) {
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`;
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  return `${Math.round(value / 1_000)}K`;
}

export default function ReportsPage() {
  const token = useAuthStore((state) => state.accessToken);
  const [txPage, setTxPage] = useState(1);
  const [txTypeFilter, setTxTypeFilter] = useState("");
  const [investorFilter, setInvestorFilter] = useState("");
  const [reportInvestorId, setReportInvestorId] = useState("");
  const [reportNav, setReportNav] = useState("");

  const investorsQuery = useQuery({
    queryKey: ["report-investor-options"],
    queryFn: () => apiClient.investorCards(token || ""),
    enabled: !!token,
  });

  const effectiveInvestorId = useMemo(() => {
    if (reportInvestorId) return Number(reportInvestorId);
    return investorsQuery.data?.[0]?.id ?? 0;
  }, [investorsQuery.data, reportInvestorId]);

  const txReportQuery = useQuery({
    queryKey: ["transactions-report", txPage, txTypeFilter, investorFilter],
    queryFn: () =>
      apiClient.transactionsReport(token || "", {
        page: txPage,
        page_size: 20,
        tx_type: txTypeFilter || undefined,
        investor_id: investorFilter ? Number(investorFilter) : undefined,
      }),
    enabled: !!token,
  });

  const investorReportQuery = useQuery({
    queryKey: ["investor-report", effectiveInvestorId, reportNav],
    queryFn: () =>
      apiClient.investorReport(
        token || "",
        effectiveInvestorId,
        reportNav.trim() ? Number(reportNav) : undefined,
      ),
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
          <p className="section-note">Trang {txPage}/{txTotalPages}</p>
        </div>
        <div className="grid gap-2 sm:grid-cols-3">
          <Input
            placeholder="Lọc theo loại (nạp, rút, phí...)"
            value={txTypeFilter}
            onChange={(e) => {
              setTxPage(1);
              setTxTypeFilter(e.target.value);
            }}
          />
          <select
            className="control-select"
            value={investorFilter}
            onChange={(e) => {
              setTxPage(1);
              setInvestorFilter(e.target.value);
            }}
          >
            <option value="">Tất cả nhà đầu tư</option>
            {investorsQuery.data?.map((item) => (
              <option key={item.id} value={item.id}>
                {item.display_name}
              </option>
            ))}
          </select>
          <Button
            variant="secondary"
            onClick={() => txReportQuery.refetch()}
            disabled={txReportQuery.isFetching}
          >
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
                <p className="kpi-value">
                  {formatCurrency(txReportQuery.data.summary.total_volume)}
                </p>
              </div>
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2">
                <p className="kpi-label">Dòng tiền ròng</p>
                <p className="kpi-value">
                  {formatCurrency(txReportQuery.data.summary.net_cash_flow)}
                </p>
              </div>
              <div className="rounded-xl bg-[var(--color-surface-2)] px-3 py-2">
                <p className="kpi-label">Số loại giao dịch</p>
                <p className="kpi-value">{txTypeChartData.length}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              <div className="h-64 rounded-xl border border-[var(--color-border)] bg-white p-2">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={txTypeChartData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={52}
                      outerRadius={86}
                      paddingAngle={3}
                    >
                      {txTypeChartData.map((item) => (
                        <Cell key={item.name} fill={item.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
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
          <select
            className="control-select"
            value={reportInvestorId || (effectiveInvestorId ? String(effectiveInvestorId) : "")}
            onChange={(e) => setReportInvestorId(e.target.value)}
          >
            {investorsQuery.data?.map((item) => (
              <option key={item.id} value={item.id}>
                {item.display_name}
              </option>
            ))}
          </select>
          <Input
            placeholder="NAV (tuỳ chọn)"
            value={reportNav}
            onChange={(e) => setReportNav(e.target.value)}
          />
          <Button
            variant="secondary"
            onClick={() => investorReportQuery.refetch()}
            disabled={investorReportQuery.isFetching || effectiveInvestorId <= 0}
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
                <p className="text-sm font-semibold">
                  {formatCurrency(investorReportQuery.data.current_balance)}
                </p>
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

            <div className="h-64 rounded-xl border border-[var(--color-border)] bg-white p-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={investorTxBars}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#dbe8f2" />
                  <XAxis dataKey="time" tick={{ fontSize: 12 }} />
                  <YAxis tickFormatter={formatCompactMoney} tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                  <Bar dataKey="amount" fill="#1b6ca8" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
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
