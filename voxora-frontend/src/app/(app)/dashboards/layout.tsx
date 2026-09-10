"use client";

import React from "react";
import AgentStudioFloatingWidget from "@/components/studio/AgentStudioFloatingWidget";

/**
 * Voxora AI — Dashboards Layout
 *
 * Wraps all dashboard pages (/dashboards/executive, /dashboards/sales, /dashboards/customers)
 * and mounts the draggable, maximizable Agent Studio floating copilot.
 */
export default function DashboardsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      {children}
      <AgentStudioFloatingWidget />
    </>
  );
}
