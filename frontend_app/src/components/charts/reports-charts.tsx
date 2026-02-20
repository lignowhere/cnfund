"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatCurrency } from "@/lib/utils";

export function ReportsTxTypeBarChart({
  data,
}: {
  data: Array<{ name: string; value: number; color: string }>;
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 5, right: 60, left: 10, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" horizontal={false} />
        <XAxis
          type="number"
          tickFormatter={(value) => {
            if (Math.abs(value) >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`;
            if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
            if (Math.abs(value) >= 1_000) return `${Math.round(value / 1_000)}K`;
            return value.toString();
          }}
          tick={{ fontSize: 12, fill: "var(--color-muted)" }}
          axisLine={{ stroke: "var(--color-border)" }}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fontSize: 12, fill: "var(--color-text)" }}
          axisLine={{ stroke: "var(--color-border)" }}
          width={80}
        />
        <Tooltip
          formatter={(value: number | undefined) => [value !== undefined ? formatCurrency(value) : "0", "Giá trị"]}
          contentStyle={{
            backgroundColor: "var(--color-surface)",
            borderColor: "var(--color-border)",
            borderRadius: "12px",
            boxShadow: "var(--shadow-card)",
          }}
          itemStyle={{ color: "var(--color-text)", fontSize: "12px" }}
          labelStyle={{ color: "var(--color-text)", fontWeight: "bold", marginBottom: "4px" }}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={24}>
          {data.map((item) => (
            <Cell key={item.name} fill={item.color} />
          ))}
          <LabelList
            dataKey="value"
            position="right"
            formatter={(value: number | undefined) => (value !== undefined ? formatCurrency(value) : "0")}
            style={{ fontSize: 11, fill: "var(--color-muted)" }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export type StackedBarDataItem = {
  name: string;
  [key: string]: number | string;
};

export function ReportsTxTypeStackedBarChart({
  data,
  colors,
}: {
  data: StackedBarDataItem[];
  colors: Record<string, string>;
}) {
  const dataKeys = Object.keys(colors);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 5, right: 80, left: 10, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" horizontal={false} />
        <XAxis
          type="number"
          tickFormatter={(value) => {
            if (Math.abs(value) >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`;
            if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
            if (Math.abs(value) >= 1_000) return `${Math.round(value / 1_000)}K`;
            return value.toString();
          }}
          tick={{ fontSize: 12, fill: "var(--color-muted)" }}
          axisLine={{ stroke: "var(--color-border)" }}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fontSize: 12, fill: "var(--color-text)" }}
          axisLine={{ stroke: "var(--color-border)" }}
          width={80}
        />
        <Tooltip
          formatter={(value: number | undefined, name: string) => [value !== undefined ? formatCurrency(value) : "0", name]}
          contentStyle={{
            backgroundColor: "var(--color-surface)",
            borderColor: "var(--color-border)",
            borderRadius: "12px",
            boxShadow: "var(--shadow-card)",
          }}
          itemStyle={{ color: "var(--color-text)", fontSize: "12px" }}
          labelStyle={{ color: "var(--color-text)", fontWeight: "bold", marginBottom: "4px" }}
        />
        {dataKeys.map((key) => (
          <Bar
            key={key}
            dataKey={key}
            stackId="a"
            fill={colors[key]}
            radius={key === dataKeys[dataKeys.length - 1] ? [0, 4, 4, 0] : [0, 0, 0, 0]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

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
            borderRadius: "12px",
            boxShadow: "var(--shadow-card)",
          }}
          itemStyle={{ color: "var(--color-text)", fontSize: "12px" }}
          labelStyle={{ color: "var(--color-text)", fontWeight: "bold", marginBottom: "4px" }}
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
            borderRadius: "12px",
            boxShadow: "var(--shadow-card)",
          }}
          itemStyle={{ color: "var(--color-text)", fontSize: "12px" }}
          labelStyle={{ color: "var(--color-text)", fontWeight: "bold", marginBottom: "4px" }}
        />
        <Bar dataKey="amount" radius={[8, 8, 0, 0]}>
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={entry.amount >= 0 ? "var(--color-success)" : "var(--color-danger)"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
