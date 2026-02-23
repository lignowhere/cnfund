"use client";

import dynamic from "next/dynamic";
import {
  BarChart3,
  CircleDollarSign,
  Landmark,
  Wallet,
  type LucideIcon,
} from "lucide-react";
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

const DashboardInvestorConcentrationChart = dynamic(
  () => import("@/components/charts/dashboard-charts").then((module) => module.DashboardInvestorConcentrationChart),
  { ssr: false },
);

const DashboardMonthlyFlowChart = dynamic(
  () => import("@/components/charts/dashboard-charts").then((module) => module.DashboardMonthlyFlowChart),
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

  const concentrationSeries = useMemo(() => {
    if (!dashboardQuery.data) return [];
    const { top_investors, kpis } = dashboardQuery.data;
    const totalNav = kpis.total_nav;

    if (totalNav <= 0) return [];

    const top5 = top_investors.slice(0, 5).map((inv, idx) => ({
      name: inv.investor_name,
      value: inv.balance,
      percent: (inv.balance / totalNav) * 100,
      color: CHART_COLORS[idx % CHART_COLORS.length],
    }));

    const topSum = top5.reduce((sum, item) => sum + item.value, 0);
    const othersValue = Math.max(0, totalNav - topSum);

    if (othersValue > 0) {
      top5.push({
        name: "Khác",
        value: othersValue,
        percent: (othersValue / totalNav) * 100,
        color: "var(--color-surface-3)",
      });
    }

    return top5;
  }, [dashboardQuery.data]);

  const monthlyFlowSeries = useMemo(() => {
    if (!txSummaryQuery.data) return [];
    const items = txSummaryQuery.data.items;

    const groups: Record<string, { deposit: number; withdraw: number }> = {};

    items.forEach((item) => {
      const d = new Date(item.date);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
      if (!groups[key]) groups[key] = { deposit: 0, withdraw: 0 };

      if (item.type.toLowerCase().includes("deposit") || item.type.toLowerCase().includes("nạp")) {
        groups[key].deposit += item.amount;
      } else if (item.type.toLowerCase().includes("withdraw") || item.type.toLowerCase().includes("rút")) {
        groups[key].withdraw += item.amount;
      }
    });

    return Object.entries(groups)
      .map(([key, vals]) => ({
        month: key.split("-")[1] + "/" + key.split("-")[0].slice(2),
        ...vals,
      }))
      .sort((a, b) => {
        const [am, ay] = a.month.split("/");
        const [bm, by] = b.month.split("/");
        return Number(ay + am) - Number(by + bm);
      })
      .slice(-6);
  }, [txSummaryQuery.data]);

  if (dashboardQuery.isLoading) {
    return <DashboardSkeleton />;
  }

  if (dashboardQuery.isError || !dashboardQuery.data) {
    return <ErrorState message="Không tải được dữ liệu bảng điều khiển." />;
  }

  const { kpis, top_investors } = dashboardQuery.data;
  const kpiCards: Array<{
    label: string;
    value: string;
    icon: LucideIcon;
  }> = [
      {
        label: "Nhà đầu tư",
        value: String(kpis.total_investors),
        icon: Landmark,
      },
      {
        label: "Tổng đơn vị quỹ",
        value: kpis.total_units.toFixed(2),
        icon: BarChart3,
      },
      {
        label: "Tổng phí đã thu",
        value: formatCurrency(kpis.total_fees_paid),
        icon: CircleDollarSign,
      },
      {
        label: "Giá trị Fund Manager",
        value: formatCurrency(kpis.fund_manager_value),
        icon: Wallet,
      },
    ];

  return (
    <div className="app-page">
      <Card className="relative overflow-hidden border-none bg-gradient-to-r from-[var(--hero-start)] via-[var(--hero-mid)] to-[var(--hero-end)] py-4 text-[var(--color-text-inverse)] shadow-xl sm:py-5">
        <div className="absolute -right-12 -top-14 h-40 w-40 rounded-full bg-[var(--hero-orb-a)]" />
        <div className="absolute -bottom-10 left-8 h-28 w-28 rounded-full bg-[var(--hero-orb-b)]" />
        <div className="relative space-y-2">
          <p className="hidden text-xs uppercase tracking-[0.2em] text-[var(--hero-text-muted)] sm:block">Tổng quan quỹ</p>
          <h2 className="text-xl font-semibold sm:text-2xl">{formatCurrency(kpis.total_nav)}</h2>
          <p className="text-sm text-[var(--hero-text-muted)]">
            Hiệu suất gộp:{" "}
            <span
              className={`font-semibold ${kpis.gross_return >= 0 ? "text-[var(--hero-success)]" : "text-[var(--hero-danger)]"
                }`}
            >
              {formatPercent(kpis.gross_return)}
            </span>
          </p>
        </div>
      </Card>

      <section className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        {kpiCards.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.label} className="space-y-1">
              <div className="flex items-center justify-between gap-2">
                <p className="kpi-label">{item.label}</p>
                <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--color-primary-50)] text-[var(--color-primary)]">
                  <Icon className="h-4 w-4" />
                </span>
              </div>
              <p className="kpi-value">{item.value}</p>
            </Card>
          );
        })}
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
          <h3 className="section-title">Tỉ trọng nhà đầu tư</h3>
          {concentrationSeries.length ? (
            <div className="h-64">
              <DashboardInvestorConcentrationChart data={concentrationSeries} />
            </div>
          ) : (
            <LoadingState label="Chưa có dữ liệu tỉ trọng." />
          )}
        </Card>
      </section>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="space-y-3 lg:col-span-2">
          <h3 className="section-title">Dòng tiền nạp/rút hàng tháng</h3>
          {monthlyFlowSeries.length ? (
            <div className="h-72">
              <DashboardMonthlyFlowChart data={monthlyFlowSeries} />
            </div>
          ) : (
            <LoadingState label="Chưa có dữ liệu dòng tiền." />
          )}
        </Card>

        <Card className="space-y-3">
          <h3 className="section-title">Hiệu quả Nhà đầu tư (Top)</h3>
          <div className="list-stagger space-y-2">
            {top_investors.slice(0, 4).map((investor) => (
              <article
                key={investor.investor_id}
                className="flex items-center justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-3"
              >
                <div>
                  <p className="text-sm font-medium">{investor.investor_name}</p>
                  <p className="text-xs text-[var(--color-muted)]">
                    Lãi/lỗ:{" "}
                    <span
                      className={
                        investor.profit >= 0 ? "text-[var(--color-success)]" : "text-[var(--color-danger)]"
                      }
                    >
                      {formatCurrency(investor.profit)} ({formatPercent(investor.profit_percent)})
                    </span>
                  </p>
                </div>
                <p className="text-sm font-semibold">{formatCurrency(investor.balance)}</p>
              </article>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
