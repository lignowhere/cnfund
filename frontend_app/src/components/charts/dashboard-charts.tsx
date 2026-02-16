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
          contentStyle={{
            backgroundColor: "var(--color-surface)",
            borderColor: "var(--color-border)",
            color: "var(--color-text)",
          }}
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

export function DashboardTxTypePieChart({
  data,
}: {
  data: Array<{ name: string; value: number; color: string }>;
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
        >
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: "var(--color-surface)",
            borderColor: "var(--color-border)",
            color: "var(--color-text)",
          }}
        />
      </PieChart>
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
          contentStyle={{
            backgroundColor: "var(--color-surface)",
            borderColor: "var(--color-border)",
            color: "var(--color-text)",
          }}
        />
        <Bar dataKey="balance" fill="var(--chart-2)" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
