"use client";

/**
 * DashboardChart — Reusable chart renderer for dashboard widgets.
 *
 * Supports bar, line, area, and pie chart types using Recharts,
 * styled consistently with the Voxora design system.
 */

import React from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import styles from "./DashboardChart.module.css";

const PALETTE = [
  "#8b5cf6", // Purple
  "#38bdf8", // Sky Blue
  "#10b981", // Emerald
  "#f59e0b", // Amber
  "#ec4899", // Pink
  "#6366f1", // Indigo
  "#14b8a6", // Teal
];

function formatValue(val: any): string {
  if (typeof val !== "number") return String(val ?? "");
  if (Math.abs(val) >= 1_000_000) {
    return `$${(val / 1_000_000).toFixed(2)}M`;
  }
  if (Math.abs(val) >= 1_000) {
    return `$${(val / 1_000).toFixed(1)}K`;
  }
  return val.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

interface ChartProps {
  chartType: string;
  chartConfig: Record<string, any>;
  dataPayload: Record<string, any>;
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;

  return (
    <div className={styles.tooltip}>
      <div className={styles.tooltipLabel}>{label}</div>
      {payload.map((entry: any, idx: number) => (
        <div key={idx} className={styles.tooltipItem}>
          <span
            className={styles.tooltipDot}
            style={{ background: entry.color }}
          />
          <span className={styles.tooltipName}>{entry.name}:</span>
          <span className={styles.tooltipValue}>
            {formatValue(entry.value)}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function DashboardChart({
  chartType,
  chartConfig,
  dataPayload,
}: ChartProps) {
  const rows: Record<string, any>[] = Array.isArray(dataPayload.rows)
    ? dataPayload.rows
    : [];

  if (!rows.length) {
    return (
      <div className={styles.empty}>
        <span className={styles.emptyIcon}>📭</span>
        <span>No data available</span>
      </div>
    );
  }

  const colors = chartConfig.colors || PALETTE;
  const firstRow = rows[0] || {};
  const defaultKeys = Object.keys(firstRow);
  const xKey = chartConfig.x_key || defaultKeys[0] || "name";
  const yKeys: string[] = Array.isArray(chartConfig.y_keys)
    ? chartConfig.y_keys
    : [defaultKeys[1] || "value"];

  if (chartType === "area") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={rows} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
          <defs>
            {yKeys.map((key, idx) => (
              <linearGradient
                key={key}
                id={`gradient-${key}`}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="5%"
                  stopColor={colors[idx % colors.length]}
                  stopOpacity={0.3}
                />
                <stop
                  offset="95%"
                  stopColor={colors[idx % colors.length]}
                  stopOpacity={0.02}
                />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis
            dataKey={xKey}
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            tickFormatter={formatValue}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: 11, color: "#94a3b8", paddingTop: 8 }}
          />
          {yKeys.map((key, idx) => (
            <Area
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[idx % colors.length]}
              strokeWidth={2.5}
              fill={`url(#gradient-${key})`}
              dot={false}
              activeDot={{ r: 5, strokeWidth: 0 }}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "line") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis
            dataKey={xKey}
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            tickFormatter={formatValue}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8", paddingTop: 8 }} />
          {yKeys.map((key, idx) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[idx % colors.length]}
              strokeWidth={2.5}
              dot={{ r: 3, fill: colors[idx % colors.length] }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "pie") {
    const nameKey = chartConfig.name_key || defaultKeys[0] || "name";
    const valueKey = chartConfig.value_key || defaultKeys[1] || "value";

    return (
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Tooltip
            formatter={(val: any) => formatValue(val)}
            contentStyle={{
              backgroundColor: "rgba(15,23,42,0.95)",
              borderColor: "rgba(255,255,255,0.1)",
              borderRadius: 8,
              fontSize: 12,
              backdropFilter: "blur(12px)",
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, color: "#94a3b8" }}
            layout="vertical"
            align="right"
            verticalAlign="middle"
          />
          <Pie
            data={rows}
            dataKey={valueKey}
            nameKey={nameKey}
            cx="40%"
            cy="50%"
            innerRadius={55}
            outerRadius={90}
            paddingAngle={3}
            strokeWidth={0}
          >
            {rows.map((_: any, index: number) => (
              <Cell
                key={`cell-${index}`}
                fill={colors[index % colors.length]}
              />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    );
  }

  // Default: Bar Chart
  const layout = chartConfig.layout === "horizontal" ? "vertical" : "horizontal";

  if (layout === "vertical") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={rows}
          layout="vertical"
          margin={{ top: 10, right: 20, left: 10, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
          <XAxis
            type="number"
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            tickFormatter={formatValue}
          />
          <YAxis
            type="category"
            dataKey={xKey}
            stroke="#64748b"
            fontSize={10}
            tickLine={false}
            axisLine={false}
            width={120}
          />
          <Tooltip content={<CustomTooltip />} />
          {yKeys.map((key, idx) => (
            <Bar
              key={key}
              dataKey={key}
              fill={colors[idx % colors.length]}
              radius={[0, 4, 4, 0]}
              maxBarSize={28}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={rows} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
        <XAxis
          dataKey={xKey}
          stroke="#64748b"
          fontSize={11}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="#64748b"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          tickFormatter={formatValue}
        />
        <Tooltip content={<CustomTooltip />} />
        {yKeys.map((key, idx) => (
          <Bar
            key={key}
            dataKey={key}
            fill={colors[idx % colors.length]}
            radius={[4, 4, 0, 0]}
            maxBarSize={45}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
