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
    { id: "persona" as const, icon: "🎭", label: "Persona & Identity" },
    { id: "voice" as const, icon: "🎙️", label: "Voice & Speech" },
    { id: "prompt" as const, icon: "📜", label: "System Prompt" },
    {
      id: "glossary" as const,
      icon: "📚",
      label: "Knowledge Glossary",
      badge: draft?.knowledge_glossary?.length ? `${draft.knowledge_glossary.length}` : undefined,
    },
    { id: "data" as const, icon: "🔒", label: "Data Access" },
    { id: "sandbox" as const, icon: "🧪", label: "Test Bench", badge: "Live" },
  ];

  if (isLoading && !draft) {
    return (
      <div className={styles.studioContainer} style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ textAlign: "center", color: "#94a3b8" }}>
          <div style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>🤖</div>
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
            {draft?.avatar || "🤖"}
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
            <option value="">⚙️ Load Persona Template...</option>
            {presets.map((p) => (
              <option key={p.id} value={p.id}>
                {p.avatar} {p.name}
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
            {isSaving ? "Publishing..." : isDirty ? "💾 Save & Publish Changes *" : "✓ Published"}
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
