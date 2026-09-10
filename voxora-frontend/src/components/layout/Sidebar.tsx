"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useConversationStore } from "@/stores/conversationStore";
import { useAuthStore } from "@/stores/authStore";
import styles from "./Sidebar.module.css";

export default function Sidebar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();

  const currentId = searchParams.get("id");
  const { conversations, isLoading, fetchConversations, deleteConversation, setActiveConversationId } =
    useConversationStore();
  const { user, logout } = useAuthStore();

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const navItems = [
    {
      href: "/ask",
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      ),
      label: "Ask Voxora",
      badge: null,
    },
    {
      href: "/dashboards",
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect width="7" height="9" x="3" y="3" rx="1" />
          <rect width="7" height="5" x="14" y="3" rx="1" />
          <rect width="7" height="9" x="14" y="12" rx="1" />
          <rect width="7" height="5" x="3" y="16" rx="1" />
        </svg>
      ),
      label: "Dashboards",
      badge: "Live",
    },
    {
      href: "/studio",
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="4" y1="21" x2="4" y2="14" />
          <line x1="4" y1="10" x2="4" y2="3" />
          <line x1="12" y1="21" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12" y2="3" />
          <line x1="20" y1="21" x2="20" y2="16" />
          <line x1="20" y1="12" x2="20" y2="3" />
          <line x1="1" y1="14" x2="7" y2="14" />
          <line x1="9" y1="8" x2="15" y2="8" />
          <line x1="17" y1="16" x2="23" y2="16" />
        </svg>
      ),
      label: "Agent Studio",
      badge: "Live",
    },
  ];

  const handleNewChat = () => {
    setActiveConversationId(null);
    router.push("/ask");
  };

  const handleDeleteConversation = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    await deleteConversation(id);
    if (currentId === id) {
      router.push("/ask");
    }
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : user?.email ? user.email.charAt(0).toUpperCase() : "U";
  const userName = user?.name || "Dinithi";
  const userRole = user?.tenant_name || user?.role || "Workspace";

  return (
    <aside className={styles.sidebar}>
      {/* ── Brand Header ──────────────────────────────────── */}
      <Link href="/ask" className={styles.sidebarHeader} onClick={handleNewChat}>
        <div className={styles.sidebarLogo}>V</div>
        <span className={styles.sidebarTitle}>Voxora</span>
      </Link>

      <nav className={styles.nav}>
        {/* ── New Conversation Button ─────────────────────── */}
        <button type="button" onClick={handleNewChat} className={styles.newChatBtn}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span>New Conversation</span>
        </button>

        {/* ── Main Navigation ─────────────────────────────── */}
        {navItems.map((item) => {
          const isActive = pathname === item.href && (!currentId || item.href !== "/ask");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`${styles.navItem} ${isActive ? styles.navItemActive : ""}`}
            >
              <span className={styles.navIcon}>{item.icon}</span>
              <span>{item.label}</span>
              {item.badge && <span className={styles.navBadge}>{item.badge}</span>}
            </Link>
          );
        })}

        {/* ── Real Conversation History ───────────────────── */}
        <div className={styles.navSection}>
          <div className={styles.navSectionHeader}>
            <span className={styles.navSectionTitle}>Recent Conversations</span>
            {conversations.length > 0 && (
              <span className={styles.conversationCount}>{conversations.length}</span>
            )}
          </div>

          <div className={styles.conversationsList}>
            {isLoading && conversations.length === 0 ? (
              <div className={styles.emptyConversations}>Loading threads...</div>
            ) : conversations.length === 0 ? (
              <div className={styles.emptyConversations}>
                No past conversations.
                <br />
                Ask a question to start one!
              </div>
            ) : (
              conversations.map((conv) => {
                const isSelected = currentId === conv.id;
                const displayTitle = conv.title || "Conversation";

                return (
                  <Link
                    key={conv.id}
                    href={`/ask?id=${conv.id}`}
                    className={`${styles.conversationItem} ${
                      isSelected ? styles.conversationItemActive : ""
                    }`}
                    title={displayTitle}
                  >
                    <div className={styles.conversationContent}>
                      <span className={styles.recentDot} />
                      <span className={styles.conversationTitle}>{displayTitle}</span>
                    </div>

                    <button
                      type="button"
                      className={styles.deleteBtn}
                      title="Archive thread"
                      onClick={(e) => handleDeleteConversation(e, conv.id)}
                    >
                      ✕
                    </button>
                  </Link>
                );
              })
            )}
          </div>
        </div>
      </nav>

      {/* ── User Profile & Logout ─────────────────────────── */}
      <div className={styles.sidebarFooter}>
        <div className={styles.userInfo}>
          <div className={styles.userAvatar}>{userInitial}</div>
          <div className={styles.userDetails}>
            <div className={styles.userName}>{userName}</div>
            <div className={styles.userRole}>{userRole}</div>
          </div>
          <button
            type="button"
            className={styles.logoutBtn}
            onClick={handleLogout}
            title="Sign out"
          >
            ↪
          </button>
        </div>
      </div>
    </aside>
  );
}
