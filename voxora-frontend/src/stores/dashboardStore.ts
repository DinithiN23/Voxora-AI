/**
 * Voxora Dashboard Store.
 *
 * Zustand store for managing executive dashboard state including
 * KPI cards, chart widgets, loading, and error states.
 */

import { create } from "zustand";
import { api } from "@/lib/api";

/* ── Types ──────────────────────────────────────────────────── */

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
  data: DashboardData | null;
  isLoading: boolean;
  error: string | null;
  lastFetched: number | null;

  fetchDashboard: () => Promise<void>;
  refreshDashboard: () => Promise<void>;
}

/* ── Store ──────────────────────────────────────────────────── */

export const useDashboardStore = create<DashboardState>((set, get) => ({
  data: null,
  isLoading: false,
  error: null,
  lastFetched: null,

  fetchDashboard: async () => {
    // Skip if data was fetched in the last 30 seconds
    const { lastFetched, isLoading } = get();
    if (isLoading) return;
    if (lastFetched && Date.now() - lastFetched < 30_000) return;

    set({ isLoading: true, error: null });

    try {
      const data = await api.get<DashboardData>("/api/v1/dashboards/executive");
      set({ data, isLoading: false, lastFetched: Date.now() });
    } catch (err: any) {
      set({
        error: err?.detail || err?.message || "Failed to load dashboard",
        isLoading: false,
      });
    }
  },

  refreshDashboard: async () => {
    // Force refetch regardless of cache
    set({ isLoading: true, error: null, lastFetched: null });

    try {
      const data = await api.get<DashboardData>("/api/v1/dashboards/executive");
      set({ data, isLoading: false, lastFetched: Date.now() });
    } catch (err: any) {
      set({
        error: err?.detail || err?.message || "Failed to load dashboard",
        isLoading: false,
      });
    }
  },
}));
