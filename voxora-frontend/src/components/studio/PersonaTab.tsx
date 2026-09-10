"use client";

import React from "react";
import { useAgentStudioStore } from "@/stores/agentStudioStore";
import styles from "@/app/(app)/studio/studio.module.css";

const AVATAR_CHOICES = ["🤖", "👔", "⚡", "🎯", "🧠", "💼", "📈", "🏛️", "💻", "💎"];

const TONE_OPTIONS = [
  {
    id: "executive",
    title: "👔 Executive & Decisive",
    description: "Leads with bottom-line revenue/profit conclusions in bold. Sharp, brief, C-suite orientation.",
  },
  {
    id: "analytical",
    title: "🔬 Deep Analytical",
    description: "Detailed variance analysis, basis points, margin breakdown, risk attribution, and precision.",
  },
  {
    id: "strategic",
    title: "⚡ Strategic & Growth",
    description: "Focuses on market opportunities, growth vectors, customer expansion, and ROI recommendations.",
  },
  {
    id: "technical",
    title: "💻 Data Engineering & SQL",
    description: "Provides BigQuery SQL queries, schema mappings, table partitioning, and query optimization.",
  },
];

export default function PersonaTab() {
  const { draft, updateDraft } = useAgentStudioStore();

  if (!draft) return null;

  return (
    <div>
      <h2 className={styles.panelTitle}>🎭 Persona & Identity</h2>
      <p className={styles.panelDescription}>
        Configure how Voxora presents itself to your executive team. Select its avatar, title, decision tone, and reasoning temperature.
      </p>

      {/* Avatar Picker */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>Agent Avatar</label>
        <div className={styles.avatarRow}>
          {AVATAR_CHOICES.map((emoji) => (
            <button
              key={emoji}
              type="button"
              className={`${styles.avatarOption} ${draft.avatar === emoji ? styles.avatarSelected : ""}`}
              onClick={() => updateDraft({ avatar: emoji })}
            >
              {emoji}
            </button>
          ))}
        </div>
      </div>

      {/* Name & Role Title Grid */}
      <div className={styles.inputGrid}>
        <div className={styles.formGroup}>
          <label className={styles.formLabel}>Agent Name</label>
          <input
            type="text"
            className={styles.formInput}
            value={draft.name}
            onChange={(e) => updateDraft({ name: e.target.value })}
            placeholder="e.g. Voxora Executive Copilot"
          />
        </div>

        <div className={styles.formGroup}>
          <label className={styles.formLabel}>Role Title</label>
          <input
            type="text"
            className={styles.formInput}
            value={draft.role_title}
            onChange={(e) => updateDraft({ role_title: e.target.value })}
            placeholder="e.g. Chief Analytics Officer"
          />
        </div>
      </div>

      {/* Description */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>Mission / Executive Scope</label>
        <textarea
          className={styles.formTextarea}
          style={{ minHeight: "80px" }}
          value={draft.description}
          onChange={(e) => updateDraft({ description: e.target.value })}
          placeholder="Brief description of this agent's strategic responsibility."
        />
      </div>

      {/* Tone Selection */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>Conversational Tone & Reasoning Style</label>
        <div className={styles.toneGrid}>
          {TONE_OPTIONS.map((tone) => (
            <div
              key={tone.id}
              className={`${styles.toneCard} ${draft.tone === tone.id ? styles.toneSelected : ""}`}
              onClick={() => updateDraft({ tone: tone.id })}
            >
              <div className={styles.toneHeader}>
                <span className={styles.toneTitle}>{tone.title}</span>
                {draft.tone === tone.id && <span>✓</span>}
              </div>
              <p className={styles.toneDesc}>{tone.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Temperature / Creativity Slider */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>
          Creativity & Analytical Precision (Temperature: {draft.temperature.toFixed(2)})
        </label>
        <div className={styles.sliderWrapper}>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            className={styles.rangeSlider}
            value={draft.temperature}
            onChange={(e) => updateDraft({ temperature: parseFloat(e.target.value) })}
          />
          <span className={styles.sliderValue}>{draft.temperature.toFixed(2)}</span>
        </div>
        <div className={styles.sliderLabels}>
          <span>0.0 — Deterministic & Precise</span>
          <span>0.5 — Balanced Advisory</span>
          <span>1.0 — Creative & Exploratory</span>
        </div>
      </div>
    </div>
  );
}
