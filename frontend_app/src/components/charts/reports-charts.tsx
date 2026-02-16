"use client";

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

import { formatCurrency } from "@/lib/utils";

export function ReportsTxTypePieChart({
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
          innerRadius={52}
          outerRadius={86}
          paddingAngle={3}
        >
          {data.map((item) => (
            <Cell key={item.name} fill={item.color} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value) => Number(value)}
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

export function ReportsInvestorTxBarChart({
  data,
  formatCompactMoney,
}: {
  data: Array<{ time: string; amount: number }>;
  formatCompactMoney: (value: number) => string;
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
        <XAxis dataKey="time" tick={{ fontSize: 12, fill: "var(--color-muted)" }} />
        <YAxis tickFormatter={formatCompactMoney} tick={{ fontSize: 12, fill: "var(--color-muted)" }} />
        <Tooltip
          formatter={(value) => formatCurrency(Number(value))}
          contentStyle={{
            backgroundColor: "var(--color-surface)",
            borderColor: "var(--color-border)",
            color: "var(--color-text)",
          }}
        />
        <Bar dataKey="amount" fill="var(--chart-2)" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
