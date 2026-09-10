"use client";

/**
 * Voxora AI — Multi-Dashboard Intelligence Hub.
 *
 * Provides three specialized BigQuery analytics views:
 * 1. Executive Overview — Macro corporate KPIs, profit margins, 2-year trajectory.
 * 2. Sales & Regional — Territory breakdown, channel attribution, volume metrics.
 * 3. Customer Intelligence — Tier segmentation (Enterprise vs Mid vs SMB), retention, top accounts.
 *
 * Supports dynamic 2-year time range filtering ("2y", "1y", "90d", "30d").
 */

import { useEffect } from "react";
import {
  useDashboardStore,
  DashboardTab,
  TimeRange,
} from "@/stores/dashboardStore";
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

/* ── Tab Metadata ─────────────────────────────────────────── */

const TAB_META: Record<
  DashboardTab,
  { title: string; subtitle: string; label: string }
> = {
  executive: {
    title: "Executive Overview",
    subtitle: "High-level business health, 2-year profit margins, and macro corporate trajectory",
    label: "Executive",
  },
  sales: {
    title: "Sales & Regional Performance",
    subtitle: "Territory analysis, sales channel attributions, and volume delivery metrics",
    label: "Sales & Regional",
  },
  customers: {
    title: "Customer Intelligence & LTV",
    subtitle: "Customer tier segmentation, retention health, account leaderboard, and CLV",
    label: "Customer Intelligence",
  },
};

const TIME_RANGES: { id: TimeRange; label: string }[] = [
  { id: "2y", label: "Past 2 Years" },
  { id: "1y", label: "12 Months" },
  { id: "90d", label: "90 Days" },
  { id: "30d", label: "30 Days" },
];

/* ══════════════════════════════════════════════════════════════
   Dashboard Page Component
   ══════════════════════════════════════════════════════════════ */

export default function DashboardsPage() {
  const {
    activeTab,
    activeTimeRange,
    data,
    isLoading,
    error,
    setActiveTab,
    setActiveTimeRange,
    fetchDashboard,
    refreshDashboard,
  } = useDashboardStore();

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const currentMeta = TAB_META[activeTab] || TAB_META.executive;
  const kpis = data?.kpis ?? [];
  const charts = data?.charts ?? [];

  return (
    <div className={styles.dashboardPage}>
      {/* ── Header ──────────────────────────────────────── */}
      <div className={styles.dashboardHeader}>
        <div className={styles.headerLeft}>
          <h1 className={styles.pageTitle}>{currentMeta.title}</h1>
          <p className={styles.pageSubtitle}>{currentMeta.subtitle}</p>
        </div>

        <div className={styles.headerActions}>
          <span className={styles.lastUpdated}>
            <span className={styles.liveDot} />
            Updated {formatTimestamp(data?.last_updated ?? null)}
          </span>

          <button
            type="button"
            className={styles.refreshBtn}
            onClick={refreshDashboard}
            disabled={isLoading}
            title="Refresh dashboard metrics"
          >
            <span
              className={`${styles.refreshIcon} ${
                isLoading ? styles.refreshSpinning : ""
              }`}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <path d="M23 4v6h-6M1 20v-6h6" />
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
              </svg>
            </span>
            <span>{isLoading ? "Syncing..." : "Sync"}</span>
          </button>
        </div>
      </div>

      {/* ── Multi-Dashboard Controls Bar ─────────────────── */}
      <div className={styles.controlsBar}>
        {/* Dashboard Switcher Tabs */}
        <div className={styles.tabGroup}>
          <button
            type="button"
            className={`${styles.tabBtn} ${
              activeTab === "executive" ? styles.tabBtnActive : ""
            }`}
            onClick={() => setActiveTab("executive")}
          >
            <span className={styles.tabIcon}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="14" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
              </svg>
            </span>
            <span>Executive Overview</span>
          </button>

          <button
            type="button"
            className={`${styles.tabBtn} ${
              activeTab === "sales" ? styles.tabBtnActive : ""
            }`}
            onClick={() => setActiveTab("sales")}
          >
            <span className={styles.tabIcon}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
                <polyline points="16 7 22 7 22 13" />
              </svg>
            </span>
            <span>Sales & Regional</span>
          </button>

          <button
            type="button"
            className={`${styles.tabBtn} ${
              activeTab === "customers" ? styles.tabBtnActive : ""
            }`}
            onClick={() => setActiveTab("customers")}
          >
            <span className={styles.tabIcon}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
            </span>
            <span>Customer Intelligence</span>
          </button>
        </div>

        {/* Time Range Filter Pills */}
        <div className={styles.timeRangeGroup}>
          <span className={styles.timeRangeLabel}>Timeline</span>
          {TIME_RANGES.map((range) => (
            <button
              key={range.id}
              type="button"
              className={`${styles.timePill} ${
                activeTimeRange === range.id ? styles.timePillActive : ""
              }`}
              onClick={() => setActiveTimeRange(range.id)}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Error State ──────────────────────────────────── */}
      {error && !data && (
        <div className={styles.errorState}>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2">
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
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* ── Initial Loading Skeletons ────────────────────── */}
      {isLoading && !data && (
        <div className={styles.contentArea}>
          <div className={styles.skeletonKpiGrid}>
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className={styles.skeletonKpi} />
            ))}
          </div>
          <div className={styles.skeletonChartsGrid}>
            <div className={`${styles.skeletonChart} ${styles.skeletonChartWide}`} />
            <div className={styles.skeletonChart} />
            <div className={styles.skeletonChart} />
            <div className={styles.skeletonChart} />
            <div className={styles.skeletonChart} />
          </div>
        </div>
      )}

      {/* ── Active Dashboard Content ─────────────────────── */}
      {data && (
        <div
          className={`${styles.contentArea} ${
            isLoading ? styles.contentAreaLoading : ""
          }`}
        >
          {/* KPI Scorecards */}
          <div className={styles.kpiGrid}>
            {kpis.map((kpi) => (
              <div key={kpi.id} className={styles.kpiCard}>
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
                  <span className={styles.kpiValue}>
                    {kpi.formatted_value}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Chart Widgets */}
          <div className={styles.chartsGrid}>
            {charts.map((chart, index) => {
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
                    <span className={styles.chartBadge}>
                      {chart.chart_type}
                    </span>
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
      )}
    </div>
  );
}
