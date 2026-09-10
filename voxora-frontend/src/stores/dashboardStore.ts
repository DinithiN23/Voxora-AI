/**
 * Voxora Dashboard Store.
 *
 * Zustand store for managing multi-dashboard state:
 * - Executive Overview
 * - Sales & Regional Performance
 * - Customer Intelligence & LTV
 *
 * Supports dynamic 2-year time range filtering ("2y", "1y", "90d", "30d").
 */

import { create } from "zustand";
import { api } from "@/lib/api";

/* ── Types ──────────────────────────────────────────────────── */

export type DashboardTab = "executive" | "sales" | "customers";
export type TimeRange = "2y" | "1y" | "90d" | "30d";

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
  activeTab: DashboardTab;
  activeTimeRange: TimeRange;
  data: DashboardData | null;
  isLoading: boolean;
  error: string | null;
  lastFetchedKey: string | null;

  setActiveTab: (tab: DashboardTab) => Promise<void>;
  setActiveTimeRange: (range: TimeRange) => Promise<void>;
  fetchDashboard: (tab?: DashboardTab, range?: TimeRange) => Promise<void>;
  refreshDashboard: () => Promise<void>;
}

/* ── Store ──────────────────────────────────────────────────── */

export const useDashboardStore = create<DashboardState>((set, get) => ({
  activeTab: "executive",
  activeTimeRange: "2y",
  data: null,
  isLoading: false,
  error: null,
  lastFetchedKey: null,

  setActiveTab: async (tab: DashboardTab) => {
    if (tab === get().activeTab) return;
    set({ activeTab: tab });
    await get().fetchDashboard(tab, get().activeTimeRange);
  },

  setActiveTimeRange: async (range: TimeRange) => {
    if (range === get().activeTimeRange) return;
    set({ activeTimeRange: range });
    await get().fetchDashboard(get().activeTab, range);
  },

  fetchDashboard: async (tabOverride?: DashboardTab, rangeOverride?: TimeRange) => {
    const tab = tabOverride || get().activeTab;
    const range = rangeOverride || get().activeTimeRange;
    const fetchKey = `${tab}:${range}`;

    // Skip if already loading
    if (get().isLoading) return;

    set({ isLoading: true, error: null });

    try {
      const data = await api.get<DashboardData>(
        `/api/v1/dashboards/${tab}?time_range=${range}`
      );
      set({
        data,
        isLoading: false,
        lastFetchedKey: fetchKey,
        activeTab: tab,
        activeTimeRange: range,
      });
    } catch (err: any) {
      set({
        error: err?.detail || err?.message || "Failed to load dashboard analytics",
        isLoading: false,
      });
    }
  },

  refreshDashboard: async () => {
    const { activeTab, activeTimeRange } = get();
    set({ isLoading: true, error: null, lastFetchedKey: null });

    try {
      const data = await api.get<DashboardData>(
        `/api/v1/dashboards/${activeTab}?time_range=${activeTimeRange}`
      );
      set({ data, isLoading: false });
    } catch (err: any) {
      set({
        error: err?.detail || err?.message || "Failed to load dashboard analytics",
        isLoading: false,
      });
    }
  },
}));
