"use client";

/**
 * Voxora AI — Executive Dashboards Page.
 *
 * Phase 4: Live BigQuery-powered dashboard with KPI scorecards,
 * revenue trends, regional breakdowns, segment analysis,
 * top products, and channel performance.
 */

import { useEffect } from "react";
import { useDashboardStore } from "@/stores/dashboardStore";
import DashboardChart from "@/components/dashboard/DashboardChart";
import styles from "./dashboards.module.css";


/* ── Format last-updated timestamp ────────────────────────── */

function formatTimestamp(iso: string | null): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

/* ── Trend arrow helper ───────────────────────────────────── */

function getTrendArrow(trend: string): string {
  switch (trend) {
    case "up":
      return "↑";
    case "down":
      return "↓";
    default:
      return "→";
  }
}

function getTrendClass(trend: string): string {
  switch (trend) {
    case "up":
      return styles.kpiTrendUp;
    case "down":
      return styles.kpiTrendDown;
    default:
      return styles.kpiTrendNeutral;
  }
}

/* ══════════════════════════════════════════════════════════════
   Dashboard Page Component
   ══════════════════════════════════════════════════════════════ */

export default function DashboardsPage() {
  const { data, isLoading, error, fetchDashboard, refreshDashboard } =
    useDashboardStore();

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  /* ── Loading skeleton ─────────────────────────────────── */
  if (isLoading && !data) {
    return (
      <div className={styles.dashboardPage}>
        <div className={styles.dashboardHeader}>
          <div className={styles.headerLeft}>
            <h1 className={styles.pageTitle}>Executive Dashboard</h1>
            <p className={styles.pageSubtitle}>Loading your analytics...</p>
          </div>
        </div>

        {/* KPI Skeletons */}
        <div className={styles.skeletonKpiGrid}>
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className={styles.skeletonKpi} />
          ))}
        </div>

        {/* Chart Skeletons */}
        <div className={styles.skeletonChartsGrid}>
          <div className={`${styles.skeletonChart} ${styles.skeletonChartWide}`} />
          <div className={styles.skeletonChart} />
          <div className={styles.skeletonChart} />
          <div className={styles.skeletonChart} />
          <div className={styles.skeletonChart} />
        </div>
      </div>
    );
  }

  /* ── Error state ──────────────────────────────────────── */
  if (error && !data) {
    return (
      <div className={styles.dashboardPage}>
        <div className={styles.errorState}>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" style={{ marginBottom: "0.5rem" }}>
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <h2 className={styles.errorTitle}>Dashboard Unavailable</h2>
          <p className={styles.errorMessage}>{error}</p>
          <button
            type="button"
            className={styles.retryBtn}
            onClick={refreshDashboard}
            style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M23 4v6h-6M1 20v-6h6" />
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
            </svg>
            <span>Retry</span>
          </button>
        </div>
      </div>
    );
  }

  const kpis = data?.kpis ?? [];
  const charts = data?.charts ?? [];

  return (
    <div className={styles.dashboardPage}>
      {/* ── Header ──────────────────────────────────────── */}
      <div className={styles.dashboardHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.pageTitle}>Executive Dashboard</h1>
          <p className={styles.pageSubtitle}>
            Real-time business intelligence from BigQuery
          </p>
        </div>

        <div className={styles.headerActions}>
          {data?.data_range && (
            <span className={styles.dataRangePill}>
              {data.data_range}
            </span>
          )}

          <span className={styles.lastUpdated}>
            <span className={styles.liveDot} />
            Updated {formatTimestamp(data?.last_updated ?? null)}
          </span>

          <button
            type="button"
            className={styles.refreshBtn}
            onClick={refreshDashboard}
            disabled={isLoading}
          >
            <span
              className={`${styles.refreshIcon} ${
                isLoading ? styles.refreshSpinning : ""
              }`}
            >
              ↻
            </span>
            {isLoading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      {/* ── KPI Scorecards ──────────────────────────────── */}
      <div className={styles.kpiGrid}>
        {kpis.map((kpi) => (
          <div key={kpi.id} className={styles.kpiCard}>
            {/* Top accent line */}
            <div
              className={styles.kpiGlow}
              style={{ background: kpi.color }}
            />

            <div className={styles.kpiTop}>
              <span className={styles.kpiLabel}>{kpi.label}</span>
              <span
                className={`${styles.kpiTrend} ${getTrendClass(kpi.trend)}`}
              >
                {getTrendArrow(kpi.trend)}
              </span>
            </div>

            <div className={styles.kpiBottom}>
              <span className={styles.kpiValue}>{kpi.formatted_value}</span>
            </div>
          </div>
        ))}
      </div>

      {/* ── Chart Widgets ───────────────────────────────── */}
      <div className={styles.chartsGrid}>
        {charts.map((chart, index) => {
          // First chart (revenue trend) spans full width
          const isWide = index === 0;

          return (
            <div
              key={chart.id}
              className={`${styles.chartCard} ${
                isWide ? styles.chartCardWide : ""
              }`}
            >
              <div className={styles.chartHeader}>
                <span className={styles.chartTitle}>
                  {chart.title}
                </span>
                <span className={styles.chartBadge}>{chart.chart_type}</span>
              </div>

              <div className={styles.chartBody}>
                <DashboardChart
                  chartType={chart.chart_type}
                  chartConfig={chart.chart_config}
                  dataPayload={chart.data_payload}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
