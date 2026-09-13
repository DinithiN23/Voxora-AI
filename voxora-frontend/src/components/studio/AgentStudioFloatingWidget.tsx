"use client";

import React, { useState, useEffect, useRef } from "react";
import UniversalChat from "@/components/chat/UniversalChat";
import { useConversationStore } from "@/stores/conversationStore";
import styles from "./AgentStudioFloatingWidget.module.css";

export default function AssistantWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef<{ mouseX: number; mouseY: number; startX: number; startY: number }>({
    mouseX: 0,
    mouseY: 0,
    startX: 0,
    startY: 0,
  });

  const widgetRef = useRef<HTMLDivElement>(null);

  // Mouse drag handling
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    if ((e.target as HTMLElement).closest("button") || (e.target as HTMLElement).closest("a") || (e.target as HTMLElement).closest("input")) return;

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

      const currentWidth = 440;
      const currentHeight = 590;

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
  }, [isDragging]);

  const { activeConversationId } = useConversationStore();

  const handleToggleMaximize = () => {
    if (typeof window !== "undefined") {
      const url = activeConversationId ? `/ask?id=${activeConversationId}` : "/ask";
      window.open(url, "_blank");
    }
  };

  const getWindowStyle = (): React.CSSProperties => {
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

  if (!isOpen) {
    return (
      <button
        type="button"
        className={styles.launcherButton}
        onClick={() => setIsOpen(true)}
        title="Ask Voxora"
        aria-label="Ask Voxora"
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
          <span>Ask Voxora</span>
          <span className={styles.liveBadge}>Live</span>
        </div>
      </button>
    );
  }

  return (
    <div
      ref={widgetRef}
      className={`${styles.windowContainer} ${styles.windowCompact}`}
      style={getWindowStyle()}
    >
      <div
        className={styles.windowHeader}
        onMouseDown={handleMouseDown}
        title="Drag to move across the screen"
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
              <span>Ask Voxora</span>
              <span className={styles.liveBadge}>Active</span>
            </div>
          </div>
        </div>

        <div className={styles.windowControls}>
          <button
            type="button"
            className={styles.controlBtn}
            onClick={handleToggleMaximize}
            title="Open in full screen (New Tab)"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" />
            </svg>
          </button>

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

      <div className={styles.windowBody}>
        <UniversalChat isWidget={true} />
      </div>
    </div>
  );
}
