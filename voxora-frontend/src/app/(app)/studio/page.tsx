"use client";

import React, { useEffect, useState } from "react";
import { useAgentStudioStore } from "@/stores/agentStudioStore";
import PersonaTab from "@/components/studio/PersonaTab";
import VoiceTab from "@/components/studio/VoiceTab";
import PromptTab from "@/components/studio/PromptTab";
import GlossaryTab from "@/components/studio/GlossaryTab";
import DataAccessTab from "@/components/studio/DataAccessTab";
import TestBenchTab from "@/components/studio/TestBenchTab";
import styles from "./studio.module.css";

export default function StudioPage() {
  const {
    draft,
    presets,
    isLoading,
    isSaving,
    isDirty,
    statusMessage,
    activeTab,
    fetchAgentConfig,
    fetchPresets,
    setActiveTab,
    applyPreset,
    saveConfig,
    discardChanges,
    resetToFactoryDefault,
    clearStatusMessage,
  } = useAgentStudioStore();

  const [selectedPresetId, setSelectedPresetId] = useState("");

  useEffect(() => {
    fetchAgentConfig();
    fetchPresets();
  }, [fetchAgentConfig, fetchPresets]);

  const handleSelectPreset = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedPresetId(val);
    if (val) {
      applyPreset(val);
    }
  };

  const navItems = [
    {
      id: "persona" as const,
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      ),
      label: "Persona & Identity",
    },
    {
      id: "voice" as const,
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="22" />
        </svg>
      ),
      label: "Voice & Speech",
    },
    {
      id: "prompt" as const,
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
      ),
      label: "System Prompt",
    },
    {
      id: "glossary" as const,
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z" />
          <path d="M6 6h10" />
          <path d="M6 10h10" />
        </svg>
      ),
      label: "Knowledge Glossary",
      badge: draft?.knowledge_glossary?.length ? `${draft.knowledge_glossary.length}` : undefined,
    },
    {
      id: "data" as const,
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect width="18" height="18" x="3" y="3" rx="2" />
          <path d="m9 12 2 2 4-4" />
        </svg>
      ),
      label: "Data Access",
    },
    {
      id: "sandbox" as const,
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="5 3 19 12 5 21 5 3" />
        </svg>
      ),
      label: "Test Bench",
      badge: "Live",
    },
  ];

  if (isLoading && !draft) {
    return (
      <div className={styles.studioContainer} style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ textAlign: "center", color: "#94a3b8" }}>
          <p>Loading Agent Studio configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.studioContainer}>
      {/* Top Header & Control Strip */}
      <header className={styles.studioHeader}>
        <div className={styles.headerLeft}>
          <div className={styles.agentAvatarBadge}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect width="18" height="18" x="3" y="3" rx="2" />
              <circle cx="12" cy="10" r="3" />
              <path d="M7 21v-2a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2" />
            </svg>
          </div>
          <div className={styles.headerInfo}>
            <h1>
              {draft?.name || "Voxora Agent Studio"}
              <span className={styles.roleBadge}>{draft?.role_title || "Chief Analytics Officer"}</span>
              <span className={styles.livePill}>
                <span className={styles.liveDot} />
                Live Agent
              </span>
            </h1>
            <p className={styles.headerSubtitle}>
              Configure and test your AI business intelligence persona, tone, BigQuery data access, and voice synthesis.
            </p>
          </div>
        </div>

        <div className={styles.headerActions}>
          {/* Preset Selector */}
          <select
            className={styles.presetSelect}
            value={selectedPresetId}
            onChange={handleSelectPreset}
          >
            <option value="">Load Persona Template...</option>
            {presets.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>

          {/* Discard Changes */}
          {isDirty && (
            <button
              type="button"
              className={`${styles.actionBtn} ${styles.btnDiscard}`}
              onClick={discardChanges}
              disabled={isSaving}
            >
              Discard Changes
            </button>
          )}

          {/* Reset to Factory Default */}
          <button
            type="button"
            className={`${styles.actionBtn} ${styles.btnSecondary}`}
            onClick={resetToFactoryDefault}
            disabled={isSaving}
            title="Reset configuration to factory standard"
          >
            Factory Reset
          </button>

          {/* Save & Publish */}
          <button
            type="button"
            className={`${styles.actionBtn} ${styles.btnPrimary} ${isDirty ? styles.btnPrimaryPulse : ""}`}
            onClick={saveConfig}
            disabled={isSaving}
          >
            {isSaving ? "Publishing..." : isDirty ? "Save & Publish Changes" : "Published"}
          </button>
        </div>
      </header>

      {/* Status Notification Banner */}
      {statusMessage && (
        <div
          className={`${styles.statusBanner} ${
            statusMessage.type === "success"
              ? styles.statusSuccess
              : statusMessage.type === "error"
              ? styles.statusError
              : styles.statusInfo
          }`}
        >
          <span>{statusMessage.text}</span>
          <button
            type="button"
            className={styles.closeBanner}
            onClick={clearStatusMessage}
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Grid: Nav Tabs on Left, Content Panel on Right */}
      <div className={styles.studioLayout}>
        {/* Navigation Sidebar Tabs */}
        <nav className={styles.tabNav}>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                className={`${styles.tabBtn} ${isActive ? styles.tabActive : ""}`}
                onClick={() => setActiveTab(item.id)}
              >
                <span className={styles.tabIcon}>{item.icon}</span>
                <span>{item.label}</span>
                {item.badge && <span className={styles.tabBadge}>{item.badge}</span>}
              </button>
            );
          })}
        </nav>

        {/* Tab Content Panel */}
        <main className={styles.contentPanel}>
          {activeTab === "persona" && <PersonaTab />}
          {activeTab === "voice" && <VoiceTab />}
          {activeTab === "prompt" && <PromptTab />}
          {activeTab === "glossary" && <GlossaryTab />}
          {activeTab === "data" && <DataAccessTab />}
          {activeTab === "sandbox" && <TestBenchTab />}
        </main>
      </div>
    </div>
  );
}
