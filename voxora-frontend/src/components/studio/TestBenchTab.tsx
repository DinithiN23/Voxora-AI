"use client";

import React, { useState } from "react";
import { useAgentStudioStore } from "@/stores/agentStudioStore";
import styles from "@/app/(app)/studio/studio.module.css";

const QUICK_TEST_QUERIES = [
  "What is our Gross Margin and how do we calculate it?",
  "Summarize our overall revenue performance from BigQuery.",
  "Which customer segment drives the highest volume?",
  "Who are our top 3 products by revenue?",
];

export default function TestBenchTab() {
  const {
    draft,
    sandboxMessages,
    isTesting,
    runSandboxTest,
    clearSandboxChat,
  } = useAgentStudioStore();

  const [inputQuery, setInputQuery] = useState("");

  if (!draft) return null;

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputQuery.trim() || isTesting) return;

    const query = inputQuery.trim();
    setInputQuery("");
    await runSandboxTest(query);
  };

  const handleChipClick = async (chipText: string) => {
    if (isTesting) return;
    await runSandboxTest(chipText);
  };

  return (
    <div>
      <div className={styles.glossaryControls}>
        <div>
          <h2 className={styles.panelTitle}>Interactive Agent Test Bench</h2>
          <p className={styles.panelDescription} style={{ marginBottom: 0 }}>
            Test and evaluate your draft persona, tone ({draft.tone}), system prompt, and glossary definitions in real-time before publishing.
          </p>
        </div>
        <button
          type="button"
          className={`${styles.actionBtn} ${styles.btnSecondary}`}
          onClick={clearSandboxChat}
          style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M23 4v6h-6M1 20v-6h6" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
          <span>Reset Session</span>
        </button>
      </div>

      <div className={styles.sandboxContainer} style={{ marginTop: "1.5rem" }}>
        {/* Sandbox Header */}
        <div className={styles.sandboxHeader}>
          <div className={styles.sandboxTitle}>
            <span style={{ 
              display: "inline-flex", 
              alignItems: "center", 
              justifyContent: "center",
              width: "22px", 
              height: "22px", 
              borderRadius: "4px", 
              background: "rgba(16, 185, 129, 0.15)", 
              color: "var(--vx-brand-primary, #10b981)",
              fontSize: "0.7rem",
              fontWeight: 700
            }}>
              {draft.avatar.length <= 3 ? draft.avatar : draft.name.slice(0, 2).toUpperCase()}
            </span>
            <span>{draft.name}</span>
            <span style={{ fontSize: "0.75rem", color: "#64748b" }}>•</span>
            <span style={{ color: "#a5b4fc", fontSize: "0.75rem", fontWeight: 600 }}>
              Tone: {draft.tone.toUpperCase()}
            </span>
            <span style={{ fontSize: "0.75rem", color: "#64748b" }}>•</span>
            <span style={{ color: "var(--vx-brand-primary, #10b981)", fontSize: "0.75rem" }}>Temp: {draft.temperature}</span>
          </div>
          <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
            Draft Sandbox Environment
          </span>
        </div>

        {/* Message Stream */}
        <div className={styles.sandboxMessages}>
          {sandboxMessages.map((msg) => {
            const isUser = msg.role === "user";
            return (
              <div
                key={msg.id}
                className={`${styles.sandboxBubble} ${isUser ? styles.userBubble : styles.assistantBubble}`}
              >
                <div style={{ whiteSpace: "pre-wrap" }}>{msg.content}</div>
                <div className={styles.bubbleMeta}>
                  <span>{msg.timestamp}</span>
                  {msg.latency_ms !== undefined && (
                    <>
                      <span>•</span>
                      <span style={{ color: "var(--vx-brand-primary, #10b981)", fontWeight: 500 }}>{msg.latency_ms}ms</span>
                    </>
                  )}
                </div>
              </div>
            );
          })}

          {isTesting && (
            <div className={`${styles.sandboxBubble} ${styles.assistantBubble}`}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", color: "#a5b4fc" }}>
                <span>Thinking in {draft.tone} persona...</span>
              </div>
            </div>
          )}
        </div>

        {/* Quick Suggestion Chips */}
        <div className={styles.sandboxPromptChips}>
          {QUICK_TEST_QUERIES.map((q, idx) => (
            <button
              key={idx}
              type="button"
              className={styles.promptChip}
              onClick={() => handleChipClick(q)}
              disabled={isTesting}
            >
              {q}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSend} className={styles.sandboxInputBar}>
          <input
            type="text"
            className={styles.sandboxInput}
            placeholder={`Ask ${draft.name} anything to test tone and instructions...`}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isTesting}
          />
          <button
            type="submit"
            className={styles.sendBtn}
            disabled={!inputQuery.trim() || isTesting}
          >
            {isTesting ? "Evaluating..." : "Send Query"}
          </button>
        </form>
      </div>
    </div>
  );
}
