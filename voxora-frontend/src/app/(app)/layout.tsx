"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import styles from "./app.module.css";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const navItems = [
    { href: "/ask", icon: "💬", label: "Ask Voxora", badge: null },
    { href: "/dashboards", icon: "📊", label: "Dashboards", badge: null },
    { href: "/studio", icon: "🤖", label: "Agent Studio", badge: "Soon" },
  ];

  const recentConversations = [
    "September sales analysis",
    "Top products Q3 2026",
    "Western region performance",
    "Customer churn analysis",
  ];

  return (
    <div className={styles.appLayout}>
      {/* ── Sidebar ──────────────────────────────────────── */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <div className={styles.sidebarLogo}>V</div>
          <span className={styles.sidebarTitle}>Voxora</span>
        </div>

        <nav className={styles.nav}>
          {/* New Chat */}
          <Link href="/ask" className={styles.newChatBtn}>
            <span>✨</span>
            New Conversation
          </Link>

          {/* Main Nav */}
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`${styles.navItem} ${
                pathname.startsWith(item.href) ? styles.navItemActive : ""
              }`}
            >
              <span className={styles.navIcon}>{item.icon}</span>
              {item.label}
              {item.badge && (
                <span className={styles.navBadge}>{item.badge}</span>
              )}
            </Link>
          ))}

          {/* Recent Conversations */}
          <div className={styles.navSection}>
            <div className={styles.navSectionTitle}>Recent</div>
            {recentConversations.map((conv, i) => (
              <div key={i} className={styles.recentItem}>
                <span className={styles.recentDot} />
                {conv}
              </div>
            ))}
          </div>
        </nav>

        {/* User Info */}
        <div className={styles.sidebarFooter}>
          <div className={styles.userInfo}>
            <div className={styles.userAvatar}>D</div>
            <div className={styles.userDetails}>
              <div className={styles.userName}>Dinithi</div>
              <div className={styles.userRole}>Admin</div>
            </div>
          </div>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────── */}
      <main className={styles.mainContent}>{children}</main>
    </div>
  );
}
