"use client";

import {
  Area,
  AreaChart,
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

import { formatCurrency } from "@/lib/utils";

/**
 * Common Tooltip style for all charts to ensure readability in Dark Mode
 */
const tooltipStyle = {
  backgroundColor: "var(--color-surface)",
  borderColor: "var(--color-border)",
  borderRadius: "12px",
  boxShadow: "var(--shadow-card)",
};

const tooltipLabelStyle = {
  color: "var(--color-text)",
  fontWeight: "bold",
  marginBottom: "4px",
};

const tooltipItemStyle = {
  color: "var(--color-text)",
  fontSize: "12px",
};

export function DashboardNavAreaChart({
  data,
  formatCompactMoney,
}: {
  data: Array<{ label: string; nav: number }>;
  formatCompactMoney: (value: number) => string;
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data}>
        <defs>
          <linearGradient id="navGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--chart-1)" stopOpacity={0.35} />
            <stop offset="95%" stopColor="var(--chart-1)" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
        <XAxis dataKey="label" tick={{ fontSize: 12, fill: "var(--color-muted)" }} />
        <YAxis tickFormatter={formatCompactMoney} tick={{ fontSize: 12, fill: "var(--color-muted)" }} />
        <Tooltip
          formatter={(value) => formatCurrency(Number(value))}
          contentStyle={tooltipStyle}
          labelStyle={tooltipLabelStyle}
          itemStyle={tooltipItemStyle}
        />
        <Area
          type="monotone"
          dataKey="nav"
          stroke="var(--chart-1)"
          strokeWidth={2}
          fillOpacity={1}
          fill="url(#navGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function DashboardInvestorConcentrationChart({
  data,
}: {
  data: Array<{ name: string; value: number; color: string; percent: number }>;
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          innerRadius={56}
          outerRadius={90}
          paddingAngle={3}
          stroke="none"
        >
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value, name, props) => [
            `${formatCurrency(Number(value))} (${props.payload.percent.toFixed(1)}%)`,
            name,
          ]}
          contentStyle={tooltipStyle}
          labelStyle={tooltipLabelStyle}
          itemStyle={tooltipItemStyle}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function DashboardMonthlyFlowChart({
  data,
}: {
  data: Array<{ month: string; deposit: number; withdraw: number }>;
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" vertical={false} />
        <XAxis
          dataKey="month"
          tick={{ fontSize: 11, fill: "var(--color-muted)" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis hide />
        <Tooltip
          formatter={(value) => formatCurrency(Number(value))}
          contentStyle={tooltipStyle}
          labelStyle={tooltipLabelStyle}
          itemStyle={tooltipItemStyle}
        />
        <Bar dataKey="deposit" name="Nạp tiền" fill="var(--color-success)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="withdraw" name="Rút tiền" fill="var(--color-danger)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DashboardTopInvestorsBarChart({
  data,
  formatCompactMoney,
}: {
  data: Array<{ name: string; balance: number; profit: number }>;
  formatCompactMoney: (value: number) => string;
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 12, fill: "var(--color-muted)" }}
          interval={0}
          angle={-10}
          height={48}
        />
        <YAxis tickFormatter={formatCompactMoney} tick={{ fontSize: 12, fill: "var(--color-muted)" }} />
        <Tooltip
          formatter={(value) => formatCurrency(Number(value))}
          contentStyle={tooltipStyle}
          labelStyle={tooltipLabelStyle}
          itemStyle={tooltipItemStyle}
        />
        <Bar dataKey="balance" fill="var(--chart-2)" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
