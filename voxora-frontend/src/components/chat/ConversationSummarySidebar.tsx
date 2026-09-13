"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useConversationStore } from "@/stores/conversationStore";
import styles from "./ConversationSummarySidebar.module.css";
import MarkdownRenderer from "./MarkdownRenderer";

export default function ConversationSummarySidebar() {
  const searchParams = useSearchParams();
  const urlConvId = searchParams.get("id");
  const { activeConversationId } = useConversationStore();
  const conversationId = activeConversationId || urlConvId;

  const [summary, setSummary] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(true);

  // Clear summary if conversation changes
  useEffect(() => {
    setSummary(null);
  }, [conversationId]);

  const fetchSummary = async () => {
    if (!conversationId) return;
    setIsLoading(true);
    try {
      const response = await api.get<{ summary: string }>(`/api/v1/conversations/${conversationId}/summary`);
      setSummary(response.summary);
    } catch (err) {
      console.error("Failed to fetch conversation summary:", err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!conversationId) {
    return null;
  }

  if (!isOpen) {
    return (
      <div className={styles.sidebarClosed} onClick={() => setIsOpen(true)}>
        <button className={styles.openBtn} title="Open Chat Insights">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
      </div>
    );
  }

  const renderHeader = () => (
    <div className={styles.header}>
      <h3>Chat Insights</h3>
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        {summary && !summary.includes("Not enough conversation") && (
          <>
            <span className={styles.liveIndicator}>
              <span className={styles.pulseDot} /> Auto-generated
            </span>
            <button className={styles.refreshBtn} onClick={fetchSummary} title="Refresh Summary" disabled={isLoading}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M23 4v6h-6" />
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
              </svg>
            </button>
          </>
        )}
        <button className={styles.closeBtn} onClick={() => setIsOpen(false)} title="Close Sidebar">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className={styles.sidebar}>
        {renderHeader()}
        <div className={styles.loading}>Generating summary...</div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className={styles.sidebar}>
        {renderHeader()}
        <div style={{ color: "var(--vx-text-secondary)", fontSize: "0.9rem", padding: "10px 0", flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "20px" }}>
          <p style={{ textAlign: "center", lineHeight: "1.5" }}>
            Need an executive summary of this chat?
          </p>
          <button className={styles.generateBtn} onClick={fetchSummary}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: "8px" }}>
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
            </svg>
            Generate Summary
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.sidebar}>
      {renderHeader()}
      
      <div className={styles.summaryContent} style={{ flex: 1, overflowY: "auto", fontSize: "0.9rem", color: "var(--vx-text-secondary)" }}>
        <MarkdownRenderer content={summary} />
      </div>

      <div className={styles.footer}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
        Summarized context
      </div>
    </div>
  );
}
