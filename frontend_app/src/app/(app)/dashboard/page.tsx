"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { Card } from "@/components/ui/card";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { apiClient } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import { formatCurrency, formatPercent } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";

const CHART_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "var(--chart-6)",
];

const DashboardNavAreaChart = dynamic(
  () => import("@/components/charts/dashboard-charts").then((module) => module.DashboardNavAreaChart),
  { ssr: false },
);

const DashboardTxTypePieChart = dynamic(
  () => import("@/components/charts/dashboard-charts").then((module) => module.DashboardTxTypePieChart),
  { ssr: false },
);

const DashboardTopInvestorsBarChart = dynamic(
  () =>
    import("@/components/charts/dashboard-charts").then((module) => module.DashboardTopInvestorsBarChart),
  { ssr: false },
);

function formatCompactMoney(value: number) {
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`;
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  return `${Math.round(value / 1_000)}K`;
}

function DashboardSkeleton() {
  return (
    <div className="app-page animate-pulse">
      <div className="h-36 rounded-[var(--radius-card)] bg-[var(--color-surface-3)]" />
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, idx) => (
          <div key={idx} className="h-24 rounded-[var(--radius-card)] bg-[var(--color-surface-3)]" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="h-72 rounded-[var(--radius-card)] bg-[var(--color-surface-3)]" />
        <div className="h-72 rounded-[var(--radius-card)] bg-[var(--color-surface-3)]" />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const token = useAuthStore((state) => state.accessToken);
  const safeToken = token || "";

  const dashboardQuery = useQuery({
    queryKey: queryKeys.dashboard(safeToken),
    queryFn: () => apiClient.dashboard(safeToken),
    enabled: !!token,
  });

  const navHistoryQuery = useQuery({
    queryKey: queryKeys.navHistory(safeToken),
    queryFn: () => apiClient.navHistory(safeToken),
    enabled: !!token,
  });

  const txSummaryQuery = useQuery({
    queryKey: queryKeys.dashboardTransactionsSummary(safeToken),
    queryFn: () => apiClient.transactionsReport(safeToken, { page: 1, page_size: 120 }),
    enabled: !!token,
  });

  const navSeries = useMemo(() => {
    if (!navHistoryQuery.data) return [];
    return navHistoryQuery.data
      .slice()
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .map((item) => ({
        label: new Date(item.date).toLocaleDateString("vi-VN"),
        nav: item.nav,
      }));
  }, [navHistoryQuery.data]);

  const topInvestorsChart = useMemo(() => {
    if (!dashboardQuery.data) return [];
    return dashboardQuery.data.top_investors.slice(0, 6).map((item) => ({
      name: item.investor_name,
      balance: item.balance,
      profit: item.profit,
    }));
  }, [dashboardQuery.data]);

  const txTypeSeries = useMemo(() => {
    if (!txSummaryQuery.data) return [];
    return Object.entries(txSummaryQuery.data.summary.by_type).map(([type, count], index) => ({
      name: type,
      value: count,
      color: CHART_COLORS[index % CHART_COLORS.length],
    }));
  }, [txSummaryQuery.data]);

  if (dashboardQuery.isLoading) {
    return <DashboardSkeleton />;
  }

  if (dashboardQuery.isError || !dashboardQuery.data) {
    return <ErrorState message="Không tải được dữ liệu bảng điều khiển." />;
  }

  const { kpis, top_investors } = dashboardQuery.data;

  return (
    <div className="app-page">
      <Card className="relative overflow-hidden border-none bg-gradient-to-r from-[var(--hero-start)] via-[var(--hero-mid)] to-[var(--hero-end)] text-[var(--color-text-inverse)] shadow-xl">
        <div className="absolute -right-12 -top-14 h-40 w-40 rounded-full bg-[var(--hero-orb-a)]" />
        <div className="absolute -bottom-10 left-8 h-28 w-28 rounded-full bg-[var(--hero-orb-b)]" />
        <div className="relative space-y-2">
          <p className="text-xs uppercase tracking-[0.2em] text-[var(--hero-text-muted)]">Tổng quan quỹ</p>
          <h2 className="text-2xl font-semibold">{formatCurrency(kpis.total_nav)}</h2>
          <p className="text-sm text-[var(--hero-text-muted)]">
            Hiệu suất gộp: <span className="font-semibold">{formatPercent(kpis.gross_return)}</span>
          </p>
        </div>
      </Card>

      <section className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <Card>
          <p className="kpi-label">Nhà đầu tư</p>
          <p className="kpi-value">{kpis.total_investors}</p>
        </Card>
        <Card>
          <p className="kpi-label">Tổng đơn vị quỹ</p>
          <p className="kpi-value">{kpis.total_units.toFixed(2)}</p>
        </Card>
        <Card>
          <p className="kpi-label">Tổng phí đã thu</p>
          <p className="kpi-value">{formatCurrency(kpis.total_fees_paid)}</p>
        </Card>
        <Card>
          <p className="kpi-label">Giá trị Fund Manager</p>
          <p className="kpi-value">{formatCurrency(kpis.fund_manager_value)}</p>
        </Card>
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="space-y-3">
          <h3 className="section-title">Diễn biến NAV</h3>
          {navSeries.length ? (
            <div className="h-64">
              <DashboardNavAreaChart data={navSeries} formatCompactMoney={formatCompactMoney} />
            </div>
          ) : (
            <LoadingState label="Chưa có lịch sử NAV để hiển thị biểu đồ." />
          )}
        </Card>

        <Card className="space-y-3">
          <h3 className="section-title">Cơ cấu loại giao dịch</h3>
          {txSummaryQuery.isLoading ? (
            <LoadingState label="Đang tải cơ cấu giao dịch..." />
          ) : txTypeSeries.length ? (
            <div className="h-64">
              <DashboardTxTypePieChart data={txTypeSeries} />
            </div>
          ) : (
            <LoadingState label="Chưa có dữ liệu giao dịch." />
          )}
        </Card>
      </section>

      <Card className="space-y-3">
        <h3 className="section-title">Top nhà đầu tư theo giá trị</h3>
        {topInvestorsChart.length ? (
          <div className="h-72">
            <DashboardTopInvestorsBarChart data={topInvestorsChart} formatCompactMoney={formatCompactMoney} />
          </div>
        ) : (
          <p className="text-sm text-[var(--color-muted)]">Chưa có dữ liệu nhà đầu tư.</p>
        )}

        <div className="list-stagger space-y-2">
          {top_investors.slice(0, 4).map((investor) => (
            <article
              key={investor.investor_id}
              className="flex items-center justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-3"
            >
              <div>
                <p className="text-sm font-medium">{investor.investor_name}</p>
                <p className="text-xs text-[var(--color-muted)]">
                  Lãi/lỗ: {formatCurrency(investor.profit)} ({formatPercent(investor.profit_percent)})
                </p>
              </div>
              <p className="text-sm font-semibold">{formatCurrency(investor.balance)}</p>
            </article>
          ))}
        </div>
      </Card>
    </div>
  );
}
