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

/* ── Chart type icon mapping ──────────────────────────────── */

function getChartIcon(type: string): string {
  switch (type) {
    case "area":
    case "line":
      return "📈";
    case "pie":
      return "🥧";
    case "bar":
      return "📊";
    default:
      return "📊";
  }
}

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
          <span className={styles.errorIcon}>⚠️</span>
          <h2 className={styles.errorTitle}>Dashboard Unavailable</h2>
          <p className={styles.errorMessage}>{error}</p>
          <button
            type="button"
            className={styles.retryBtn}
            onClick={refreshDashboard}
          >
            🔄 Retry
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
            {/* Top glow bar */}
            <div
              className={styles.kpiGlow}
              style={{ background: kpi.color }}
            />

            <div className={styles.kpiTop}>
              <div className={styles.kpiIconWrapper}>{kpi.icon}</div>
              <span
                className={`${styles.kpiTrend} ${getTrendClass(kpi.trend)}`}
              >
                {getTrendArrow(kpi.trend)}
              </span>
            </div>

            <div className={styles.kpiBottom}>
              <span className={styles.kpiValue}>{kpi.formatted_value}</span>
              <span className={styles.kpiLabel}>{kpi.label}</span>
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
                  <span>{getChartIcon(chart.chart_type)}</span>
                  <span>{chart.title}</span>
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
