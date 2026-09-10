"use client";

import React from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
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
import styles from "./VisualizationViewer.module.css";

const PALETTE = [
  "#10b981", // Primary Emerald
  "#6366f1", // Indigo
  "#38bdf8", // Sky Blue
  "#34d399", // Mint
  "#f59e0b", // Amber
  "#06b6d4", // Cyan
  "#8b5cf6", // Violet
];

function formatCurrencyOrNumber(val: any): string {
  if (typeof val !== "number") return String(val ?? "");
  if (Math.abs(val) >= 1_000_000) {
    return `$${(val / 1_000_000).toFixed(2)}M`;
  }
  if (Math.abs(val) >= 1_000) {
    return `$${(val / 1_000).toFixed(1)}K`;
  }
  return val.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

interface VisualizationViewerProps {
  viz: {
    id?: string;
    chart_type: string;
    title?: string | null;
    chart_config?: Record<string, any>;
    data_payload?: Record<string, any>;
  };
}

export default function VisualizationViewer({ viz }: VisualizationViewerProps) {
  const chart_type = viz.chart_type;
  const title = viz.title;
  const config: Record<string, any> = viz.chart_config || {};
  const payload: Record<string, any> = viz.data_payload || {};

  if (chart_type === "kpi") {
    const row: Record<string, any> = payload.row || {};
    const primaryKey = config.primary_key || Object.keys(row)[0] || "metric";
    const secondaryKey = config.secondary_key;

    const primaryVal = row[primaryKey];
    const secondaryVal = secondaryKey ? row[secondaryKey] : null;

    return (
      <div className={styles.vizCard}>
        <div className={styles.vizHeader}>
          <span className={styles.vizTitle}>
            <span>{String(title || config.primary_label || "Key Metric")}</span>
          </span>
          <span className={styles.vizBadge}>KPI Summary</span>
        </div>
        <div className={styles.kpiContainer}>
          <div className={styles.kpiPrimaryValue}>
            {formatCurrencyOrNumber(primaryVal)}
          </div>
          {secondaryVal !== null && secondaryVal !== undefined && (
            <div className={styles.kpiDetails}>
              <span className={styles.kpiLabel}>{String(config.secondary_label || "Secondary")}</span>
              <span className={styles.kpiSecondaryValue}>
                {formatCurrencyOrNumber(secondaryVal)}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  }

  const rows: Record<string, any>[] = Array.isArray(payload.rows) ? payload.rows : [];
  if (!rows || rows.length === 0) return null;

  const firstRow = rows[0] || {};
  const defaultKeys = Object.keys(firstRow);
  const xKey = config.x_key || defaultKeys[0] || "name";
  const yKeys: string[] = Array.isArray(config.y_keys)
    ? config.y_keys
    : [defaultKeys[1] || "value"];

  return (
    <div className={styles.vizCard}>
      <div className={styles.vizHeader}>
        <span className={styles.vizTitle}>
          <span>{title || "Data Visualization"}</span>
        </span>
        <span className={styles.vizBadge}>{chart_type}</span>
      </div>

      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          {chart_type === "line" ? (
            <LineChart data={rows} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis
                dataKey={xKey}
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
              />
              <YAxis
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                tickFormatter={formatCurrencyOrNumber}
              />
              <Tooltip
                content={({ active, payload: tPayload, label }) => {
                  if (active && tPayload && tPayload.length) {
                    return (
                      <div className={styles.customTooltip}>
                        <div className={styles.tooltipLabel}>{label}</div>
                        {tPayload.map((entry: any, idx: number) => (
                          <div key={idx} className={styles.tooltipItem} style={{ color: entry.color }}>
                            {entry.name}: {formatCurrencyOrNumber(entry.value)}
                          </div>
                        ))}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              {yKeys.map((key: string, idx: number) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={PALETTE[idx % PALETTE.length]}
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: PALETTE[idx % PALETTE.length] }}
                  activeDot={{ r: 6 }}
                />
              ))}
            </LineChart>
          ) : chart_type === "pie" ? (
            <PieChart>
              <Tooltip
                formatter={(val: any) => formatCurrencyOrNumber(val)}
                contentStyle={{
                  backgroundColor: "rgba(15,23,42,0.95)",
                  borderColor: "rgba(255,255,255,0.1)",
                  borderRadius: 6,
                  fontSize: 12,
                }}
              />
              <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
              <Pie
                data={rows}
                dataKey={config.value_key || defaultKeys[1] || "value"}
                nameKey={config.name_key || defaultKeys[0] || "name"}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={85}
                paddingAngle={4}
              >
                {rows.map((_: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={PALETTE[index % PALETTE.length]} />
                ))}
              </Pie>
            </PieChart>
          ) : (
            /* Bar Chart */
            <BarChart data={rows} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis
                dataKey={xKey}
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
              />
              <YAxis
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                tickFormatter={formatCurrencyOrNumber}
              />
              <Tooltip
                content={({ active, payload: tPayload, label }) => {
                  if (active && tPayload && tPayload.length) {
                    return (
                      <div className={styles.customTooltip}>
                        <div className={styles.tooltipLabel}>{label}</div>
                        {tPayload.map((entry: any, idx: number) => (
                          <div key={idx} className={styles.tooltipItem} style={{ color: entry.color }}>
                            {entry.name}: {formatCurrencyOrNumber(entry.value)}
                          </div>
                        ))}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              {yKeys.map((key: string, idx: number) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={PALETTE[idx % PALETTE.length]}
                  radius={[4, 4, 0, 0]}
                  maxBarSize={50}
                />
              ))}
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
