/**
 * Voxora Dashboard Store.
 *
 * State management for multi-page dashboards:
 * - /dashboards/executive
 * - /dashboards/sales
 * - /dashboards/customers
 *
 * Supports Daily, Monthly, Yearly granularity and Calendar/Year filtering (2024–2026).
 */

import { create } from "zustand";
import { api } from "@/lib/api";

/* ── Types ──────────────────────────────────────────────────── */

export type DashboardPageType = "executive" | "sales" | "customers";
export type Granularity = "daily" | "monthly" | "yearly";

export interface KPICard {
  id: string;
  label: string;
  value: number;
  formatted_value: string;
  delta_pct?: number | null;
  delta_label?: string | null;
  trend: "up" | "down" | "neutral";
  icon: string;
  color: string;
  period_label?: string;
}

export interface ChartWidget {
  id: string;
  title: string;
  chart_type: "bar" | "line" | "pie" | "area" | "table" | "kpi";
  chart_config: Record<string, any>;
  data_payload: Record<string, any>;
}

export interface DashboardData {
  kpis: KPICard[];
  charts: ChartWidget[];
  last_updated: string | null;
  data_range: string | null;
}

interface DashboardState {
  currentPage: DashboardPageType;
  granularity: Granularity;
  timeRange: string;
  selectedDate: string; // e.g. "2026-09-10"
  selectedMonth: { year: number; month: number }; // 0-indexed month (8 = September)
  selectedYear: number; // e.g. 2026
  startDate: string | null;
  endDate: string | null;
  data: DashboardData | null;
  isLoading: boolean;
  error: string | null;

  selectDaily: (dateStr?: string) => Promise<void>;
  selectMonthly: (year?: number, month?: number) => Promise<void>;
  selectYearly: (year?: number) => Promise<void>;
  setGranularity: (granularity: Granularity) => Promise<void>;
  setTimeRange: (timeRange: string) => Promise<void>;
  setCustomDates: (startDate: string | null, endDate: string | null) => Promise<void>;
  resetToDefaultRange: () => Promise<void>;
  fetchDashboard: (page?: DashboardPageType) => Promise<void>;
  refreshDashboard: () => Promise<void>;
}

/* ── Store ──────────────────────────────────────────────────── */

const getTodayDateStr = () => {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

export const useDashboardStore = create<DashboardState>((set, get) => {
  const todayStr = getTodayDateStr();
  return {
    currentPage: "executive",
    granularity: "yearly",
    timeRange: "2026",
    selectedDate: todayStr,
    selectedMonth: { year: 2026, month: 8 },
    selectedYear: 2026,
    startDate: "2026-01-01",
    endDate: "2026-12-31",
    data: null,
    isLoading: false,
    error: null,

    selectDaily: async (dateStr?: string) => {
      const targetDate = dateStr || get().selectedDate || getTodayDateStr();
      set({
        granularity: "daily",
        selectedDate: targetDate,
        startDate: targetDate,
        endDate: targetDate,
        timeRange: "daily",
      });
      await get().fetchDashboard();
    },

  selectMonthly: async (year?: number, month?: number) => {
    const targetYear = year ?? get().selectedMonth.year ?? 2026;
    const targetMonth = month ?? get().selectedMonth.month ?? 8;
    const lastDay = new Date(targetYear, targetMonth + 1, 0).getDate();
    const monthStr = String(targetMonth + 1).padStart(2, "0");
    const start = `${targetYear}-${monthStr}-01`;
    const end = `${targetYear}-${monthStr}-${String(lastDay).padStart(2, "0")}`;

    set({
      granularity: "monthly",
      selectedMonth: { year: targetYear, month: targetMonth },
      startDate: start,
      endDate: end,
      timeRange: "monthly",
    });
    await get().fetchDashboard();
  },

  selectYearly: async (year?: number) => {
    const targetYear = year ?? get().selectedYear ?? 2026;
    const start = `${targetYear}-01-01`;
    const end = `${targetYear}-12-31`;

    set({
      granularity: "yearly",
      selectedYear: targetYear,
      startDate: start,
      endDate: end,
      timeRange: String(targetYear),
    });
    await get().fetchDashboard();
  },

  setGranularity: async (granularity: Granularity) => {
    if (granularity === "daily") {
      await get().selectDaily();
    } else if (granularity === "monthly") {
      await get().selectMonthly();
    } else if (granularity === "yearly") {
      await get().selectYearly();
    }
  },

  setTimeRange: async (timeRange: string) => {
    set({ timeRange, startDate: null, endDate: null });
    await get().fetchDashboard();
  },

  setCustomDates: async (startDate: string | null, endDate: string | null) => {
    set({ startDate, endDate, timeRange: "custom" });
    await get().fetchDashboard();
  },

  resetToDefaultRange: async () => {
    const g = get().granularity;
    if (g === "daily") {
      await get().selectDaily(getTodayDateStr());
    } else if (g === "monthly") {
      await get().selectMonthly(2026, 8);
    } else {
      await get().selectYearly(2026);
    }
  },

  fetchDashboard: async (pageOverride?: DashboardPageType) => {
    const { currentPage, granularity, timeRange, startDate, endDate } = get();
    const page = pageOverride || currentPage;
    const isNewPage = pageOverride && pageOverride !== currentPage;

    set({
      currentPage: page,
      isLoading: true,
      error: null,
      ...(isNewPage ? { data: null } : {}),
    });

    let url = `/api/v1/dashboards/${page}?granularity=${granularity}`;
    if (startDate && endDate) {
      url += `&start_date=${startDate}&end_date=${endDate}`;
    } else {
      url += `&time_range=${timeRange}`;
    }

    try {
      const data = await api.get<DashboardData>(url);
      set({ data, isLoading: false });
    } catch (err: any) {
      set({
        error: err?.detail || err?.message || "Failed to load dashboard analytics",
        isLoading: false,
      });
    }
  },

  refreshDashboard: async () => {
    await get().fetchDashboard();
  },
  };
});
