"use client";

/**
 * Voxora AI — Floating Agent Studio Copilot Widget
 *
 * Appears as a sleek floating trigger on every dashboard page.
 * Features:
 * 1. Minimizable / Collapsible to a small floating badge.
 * 2. Draggable anywhere across the viewport via header drag handle.
 * 3. Maximizable: expands from compact floating mode (440px) to wide studio mode (860px).
 * 4. Interactive Test Bench: real-time dashboard analytical queries with latency tags.
 * 5. Instant Agent Tuning: Tone & Temperature adjustments with instant preview.
 */

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useAgentStudioStore } from "@/stores/agentStudioStore";
import styles from "./AgentStudioFloatingWidget.module.css";

const DASHBOARD_QUICK_PROMPTS = [
  "Summarize 2025 vs 2026 revenue trends",
  "Which region drives the highest margin?",
  "Identify top customer retention risks",
  "Top 3 revenue products in 2025",
];

const TONE_CHOICES = [
  { id: "executive", title: "Executive", desc: "Decisive takeaways & revenue bullets" },
  { id: "analytical", title: "Analytical", desc: "Cohorts, variance & margins" },
  { id: "strategic", title: "Strategic", desc: "Growth vectors & market ROI" },
  { id: "technical", title: "Technical", desc: "SQL structures & column logic" },
];

export default function AgentStudioFloatingWidget() {
  const {
    draft,
    fetchAgentConfig,
    updateDraft,
    saveConfig,
    isSaving,
    sandboxMessages,
    isTesting,
    runSandboxTest,
    clearSandboxChat,
  } = useAgentStudioStore();

  const [isOpen, setIsOpen] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [activeTab, setActiveTab] = useState<"chat" | "tuning">("chat");
  const [inputQuery, setInputQuery] = useState("");

  // Draggable window coordinates
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef<{ mouseX: number; mouseY: number; startX: number; startY: number }>({
    mouseX: 0,
    mouseY: 0,
    startX: 0,
    startY: 0,
  });

  const widgetRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize draft on mount
  useEffect(() => {
    if (!draft) {
      fetchAgentConfig();
    }
  }, [draft, fetchAgentConfig]);

  // Scroll messages to bottom on new reply
  useEffect(() => {
    if (isOpen && activeTab === "chat") {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [sandboxMessages, isOpen, activeTab, isTesting]);

  // Mouse drag handling
  const handleMouseDown = (e: React.MouseEvent) => {
    // Only left click, not clicking child buttons/links, and not dragging when maximized
    if (e.button !== 0) return;
    if ((e.target as HTMLElement).closest("button") || (e.target as HTMLElement).closest("a")) return;
    if (isMaximized) return;

    const rect = widgetRef.current?.getBoundingClientRect();
    if (!rect) return;

    setIsDragging(true);
    dragStartRef.current = {
      mouseX: e.clientX,
      mouseY: e.clientY,
      startX: rect.left,
      startY: rect.top,
    };
  };

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - dragStartRef.current.mouseX;
      const deltaY = e.clientY - dragStartRef.current.mouseY;

      const currentWidth = isMaximized ? 860 : 440;
      const currentHeight = isMaximized ? 720 : 590;

      const newX = Math.max(12, Math.min(window.innerWidth - currentWidth - 12, dragStartRef.current.startX + deltaX));
      const newY = Math.max(12, Math.min(window.innerHeight - currentHeight - 12, dragStartRef.current.startY + deltaY));

      setPosition({ x: newX, y: newY });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, isMaximized]);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputQuery.trim() || isTesting) return;

    const query = inputQuery.trim();
    setInputQuery("");
    await runSandboxTest(query);
  };

  const handleQuickPrompt = async (prompt: string) => {
    if (isTesting) return;
    await runSandboxTest(prompt);
  };

  // Toggle maximize
  const handleToggleMaximize = () => {
    setIsMaximized(!isMaximized);
    // If maximizing, center position or reset bounds
    if (!isMaximized) {
      setPosition(null);
    }
  };

  // Calculate window style based on dragged position vs default docking
  const getWindowStyle = (): React.CSSProperties => {
    if (isMaximized) {
      return {
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
      };
    }
    if (position) {
      return {
        left: `${position.x}px`,
        top: `${position.y}px`,
        right: "auto",
        bottom: "auto",
      };
    }
    return {
      bottom: "24px",
      right: "24px",
    };
  };

  // ── 1. Collapsed Floating Trigger (Small Icon) ───────────
  if (!isOpen) {
    return (
      <button
        type="button"
        className={styles.launcherButton}
        onClick={() => setIsOpen(true)}
        title="Open Agent Studio Copilot"
        aria-label="Open Agent Studio Copilot"
      >
        <div className={styles.launcherIconWrap}>
          <span className={styles.pulsingDot} />
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
        </div>
        <div className={styles.launcherLabel}>
          <span>Agent Studio</span>
          <span className={styles.liveBadge}>Live</span>
        </div>
      </button>
    );
  }

  // ── 2. Expanded Floating Draggable Window ─────────────────
  return (
    <div
      ref={widgetRef}
      className={`${styles.windowContainer} ${
        isMaximized ? styles.windowMaximized : styles.windowCompact
      }`}
      style={getWindowStyle()}
    >
      {/* ── Window Header (Drag Handle) ────────────────────── */}
      <div
        className={styles.windowHeader}
        onMouseDown={handleMouseDown}
        title={isMaximized ? "Maximized Mode" : "Drag to move across the screen"}
      >
        <div className={styles.headerLeft}>
          <span className={styles.dragHandle}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="9" cy="6" r="2" />
              <circle cx="9" cy="12" r="2" />
              <circle cx="9" cy="18" r="2" />
              <circle cx="15" cy="6" r="2" />
              <circle cx="15" cy="12" r="2" />
              <circle cx="15" cy="18" r="2" />
            </svg>
          </span>

          <div className={styles.headerIcon}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="10" rx="2" />
              <circle cx="12" cy="5" r="2" />
              <path d="M12 7v4" />
              <line x1="8" y1="16" x2="8.01" y2="16" />
              <line x1="16" y1="16" x2="16.01" y2="16" />
            </svg>
          </div>

          <div className={styles.headerTitleGroup}>
            <div className={styles.headerTitle}>
              <span>{draft?.name || "Agent Studio"}</span>
              <span className={styles.liveBadge}>Active</span>
            </div>
            <span className={styles.headerSubtitle}>
              Tone: {draft?.tone?.toUpperCase()} • Temp: {draft?.temperature}
            </span>
          </div>
        </div>

        {/* Controls: Maximize, Minimize, Close */}
        <div className={styles.windowControls}>
          {/* Maximize / Range Toggle */}
          <button
            type="button"
            className={styles.controlBtn}
            onClick={handleToggleMaximize}
            title={isMaximized ? "Restore compact window" : "Maximize window range"}
          >
            {isMaximized ? (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="4" y="8" width="12" height="12" rx="1" />
                <path d="M8 4h12v12" />
              </svg>
            ) : (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" />
              </svg>
            )}
          </button>

          {/* Minimize */}
          <button
            type="button"
            className={styles.controlBtn}
            onClick={() => setIsOpen(false)}
            title="Minimize to floating button"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>

          {/* Close */}
          <button
            type="button"
            className={`${styles.controlBtn} ${styles.controlBtnClose}`}
            onClick={() => setIsOpen(false)}
            title="Close"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </div>

      {/* ── Sub Navigation Bar ─────────────────────────────── */}
      <div className={styles.tabBar}>
        <div className={styles.tabsLeft}>
          <button
            type="button"
            className={`${styles.tabBtn} ${activeTab === "chat" ? styles.tabBtnActive : ""}`}
            onClick={() => setActiveTab("chat")}
          >
            Interactive Chat
          </button>
          <button
            type="button"
            className={`${styles.tabBtn} ${activeTab === "tuning" ? styles.tabBtnActive : ""}`}
            onClick={() => setActiveTab("tuning")}
          >
            Agent Tuning
          </button>
        </div>

        <Link href="/studio" className={styles.fullStudioLink} target="_blank">
          Full Studio ↗
        </Link>
      </div>

      {/* ── Window Content Body ─────────────────────────────── */}
      <div className={styles.windowBody}>
        {isMaximized ? (
          /* Maximized Split View: Left column Tuning, Right column Chat */
          <div className={styles.maximizedSplit}>
            <div className={styles.leftColumnPanel}>
              <TuningPanel
                draft={draft}
                updateDraft={updateDraft}
                saveConfig={saveConfig}
                isSaving={isSaving}
              />
            </div>
            <div className={styles.rightColumnPanel}>
              <ChatPanel
                sandboxMessages={sandboxMessages}
                isTesting={isTesting}
                inputQuery={inputQuery}
                setInputQuery={setInputQuery}
                handleSend={handleSend}
                handleQuickPrompt={handleQuickPrompt}
                clearSandboxChat={clearSandboxChat}
                messagesEndRef={messagesEndRef}
              />
            </div>
          </div>
        ) : activeTab === "chat" ? (
          /* Compact View: Chat Tab */
          <ChatPanel
            sandboxMessages={sandboxMessages}
            isTesting={isTesting}
            inputQuery={inputQuery}
            setInputQuery={setInputQuery}
            handleSend={handleSend}
            handleQuickPrompt={handleQuickPrompt}
            clearSandboxChat={clearSandboxChat}
            messagesEndRef={messagesEndRef}
          />
        ) : (
          /* Compact View: Tuning Tab */
          <TuningPanel
            draft={draft}
            updateDraft={updateDraft}
            saveConfig={saveConfig}
            isSaving={isSaving}
          />
        )}
      </div>
    </div>
  );
}

// ── Sub-Component: Chat & Test Bench Panel ───────────────────

interface ChatPanelProps {
  sandboxMessages: Array<{ id: string; role: "user" | "assistant"; content: string; latency_ms?: number; timestamp: string }>;
  isTesting: boolean;
  inputQuery: string;
  setInputQuery: (v: string) => void;
  handleSend: (e?: React.FormEvent) => void;
  handleQuickPrompt: (p: string) => void;
  clearSandboxChat: () => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
}

function ChatPanel({
  sandboxMessages,
  isTesting,
  inputQuery,
  setInputQuery,
  handleSend,
  handleQuickPrompt,
  clearSandboxChat,
  messagesEndRef,
}: ChatPanelProps) {
  return (
    <>
      <div className={styles.chatMessages}>
        {sandboxMessages.map((msg) => {
          const isUser = msg.role === "user";
          return (
            <div
              key={msg.id}
              className={`${styles.messageRow} ${
                isUser ? styles.messageUser : styles.messageAssistant
              }`}
            >
              <div className={styles.messageMeta}>
                <span>{isUser ? "You" : "Voxora Agent"}</span>
                <span>•</span>
                <span>{msg.timestamp}</span>
                {msg.latency_ms && (
                  <>
                    <span>•</span>
                    <span className={styles.latencyTag}>{msg.latency_ms}ms</span>
                  </>
                )}
              </div>
              <div
                className={`${styles.bubble} ${
                  isUser ? styles.bubbleUser : styles.bubbleAssistant
                }`}
              >
                {msg.content}
              </div>
            </div>
          );
        })}

        {isTesting && (
          <div className={styles.typingIndicator}>
            <span className={styles.typingDot} />
            <span className={styles.typingDot} />
            <span className={styles.typingDot} />
            <span>Analyzing BigQuery schema & formulating reply...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div className={styles.suggestionsRow}>
        {DASHBOARD_QUICK_PROMPTS.map((prompt, i) => (
          <button
            key={i}
            type="button"
            className={styles.suggestionChip}
            onClick={() => handleQuickPrompt(prompt)}
            disabled={isTesting}
          >
            <span>{prompt}</span>
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <form className={styles.inputBar} onSubmit={handleSend}>
        <input
          type="text"
          className={styles.inputField}
          placeholder="Ask Agent Studio about this dashboard..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          disabled={isTesting}
        />
        <button
          type="submit"
          className={styles.sendBtn}
          disabled={!inputQuery.trim() || isTesting}
          title="Send query"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </form>
    </>
  );
}

// ── Sub-Component: Agent Tuning Panel ─────────────────────────

interface TuningPanelProps {
  draft: any;
  updateDraft: (changes: any) => void;
  saveConfig: () => Promise<void>;
  isSaving: boolean;
}

function TuningPanel({ draft, updateDraft, saveConfig, isSaving }: TuningPanelProps) {
  if (!draft) return null;

  return (
    <div className={styles.tuningContainer}>
      {/* Tone Selection */}
      <div className={styles.tuningSection}>
        <label className={styles.sectionLabel}>Executive Response Tone</label>
        <div className={styles.toneGrid}>
          {TONE_CHOICES.map((t) => (
            <button
              key={t.id}
              type="button"
              className={`${styles.toneOption} ${
                draft.tone === t.id ? styles.toneOptionActive : ""
              }`}
              onClick={() => updateDraft({ tone: t.id })}
            >
              <span className={styles.toneTitle}>{t.title}</span>
              <span className={styles.toneDesc}>{t.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Temperature */}
      <div className={styles.tuningSection}>
        <div className={styles.sliderGroup}>
          <div className={styles.sliderHeader}>
            <label className={styles.sectionLabel}>Creativity (Temperature)</label>
            <span className={styles.sliderValue}>{draft.temperature}</span>
          </div>
          <input
            type="range"
            className={styles.rangeInput}
            min="0"
            max="1"
            step="0.05"
            value={draft.temperature}
            onChange={(e) => updateDraft({ temperature: parseFloat(e.target.value) })}
          />
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "#64748b" }}>
            <span>0.0 Precise SQL</span>
            <span>0.5 Balanced</span>
            <span>1.0 Exploratory</span>
          </div>
        </div>
      </div>

      {/* System Directives */}
      <div className={styles.tuningSection}>
        <label className={styles.sectionLabel}>Agent Directives Prompt</label>
        <textarea
          className={styles.textareaPrompt}
          value={draft.system_prompt || ""}
          onChange={(e) => updateDraft({ system_prompt: e.target.value })}
          placeholder="Enter custom business rules or persona directives..."
        />
      </div>

      {/* Save Button */}
      <button
        type="button"
        className={styles.saveTuningBtn}
        onClick={saveConfig}
        disabled={isSaving}
      >
        {isSaving ? "Publishing Changes..." : "Publish Agent Updates"}
      </button>
    </div>
  );
}
