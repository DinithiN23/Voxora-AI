"use client";

import { useEffect, Suspense } from "react";
import Sidebar from "@/components/layout/Sidebar";
import { useAuthStore } from "@/stores/authStore";
import styles from "./app.module.css";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { loadUser } = useAuthStore();

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  return (
    <div className={styles.appLayout}>
      <Suspense fallback={<aside className={styles.sidebar} />}>
        <Sidebar />
      </Suspense>

      <main className={styles.mainContent}>{children}</main>
    </div>
  );
}
