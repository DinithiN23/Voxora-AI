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
    { href: "/ask", icon: "💬", label: "Ask Voxora", badge: null },
    { href: "/dashboards", icon: "📊", label: "Dashboards", badge: null },
    { href: "/studio", icon: "🤖", label: "Agent Studio", badge: "Soon" },
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
          <span>✨</span>
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
