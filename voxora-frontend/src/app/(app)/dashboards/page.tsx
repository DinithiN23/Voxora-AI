import { redirect } from "next/navigation";

/**
 * Voxora AI — Dashboards Root Redirect.
 *
 * Redirects to the first primary dashboard: /dashboards/executive.
 */
export default function DashboardsIndexPage() {
  redirect("/dashboards/executive");
}
