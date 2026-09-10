"use client";

import React from "react";
import { useAgentStudioStore } from "@/stores/agentStudioStore";
import styles from "@/app/(app)/studio/studio.module.css";

const VOICE_OPTIONS = [
  {
    id: "en-US-Journey-F",
    name: "Journey F (Executive Female)",
    description: "Warm, natural, confident, and authoritative executive cadence.",
    gender: "Female",
    tier: "Journey",
  },
  {
    id: "en-US-Journey-D",
    name: "Journey D (Executive Male)",
    description: "Deep, polished, resonant, and measured business briefing voice.",
    gender: "Male",
    tier: "Journey",
  },
  {
    id: "en-US-Neural2-F",
    name: "Neural2 F (Analytical Female)",
    description: "Crisp, clear, highly articulated data presentation tone.",
    gender: "Female",
    tier: "Neural2",
  },
  {
    id: "en-US-Neural2-D",
    name: "Neural2 D (Strategic Male)",
    description: "Firm, direct, articulate operational leader voice.",
    gender: "Male",
    tier: "Neural2",
  },
  {
    id: "en-US-Studio-O",
    name: "Studio O (Modern Studio)",
    description: "Conversational, modern, friendly, and adaptive.",
    gender: "Neutral",
    tier: "Studio",
  },
];

export default function VoiceTab() {
  const { draft, updateDraft, previewVoice, isPlayingVoice } = useAgentStudioStore();

  if (!draft) return null;

  return (
    <div>
      <h2 className={styles.panelTitle}>🎙️ Voice & Speech Synthesis</h2>
      <p className={styles.panelDescription}>
        Configure Google Cloud Neural2 / Journey TTS speech acoustics, cadence, and pitch for real-time voice mode.
      </p>

      {/* Voice Selection Cards */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>Selected Voice Model</label>
        <div className={styles.voiceGrid}>
          {VOICE_OPTIONS.map((voice) => (
            <div
              key={voice.id}
              className={`${styles.voiceCard} ${draft.voice_id === voice.id ? styles.voiceSelected : ""}`}
              onClick={() => updateDraft({ voice_id: voice.id })}
            >
              <div>
                <p className={styles.voiceName}>{voice.name}</p>
                <p className={styles.voiceTag}>{voice.description}</p>
              </div>
              <button
                type="button"
                className={styles.playVoiceBtn}
                title="Preview this voice"
                onClick={(e) => {
                  e.stopPropagation();
                  updateDraft({ voice_id: voice.id });
                  previewVoice();
                }}
              >
                {isPlayingVoice && draft.voice_id === voice.id ? "⏸" : "▶"}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Speaking Rate Slider */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>
          Speaking Speed ({draft.voice_speed.toFixed(2)}x)
        </label>
        <div className={styles.sliderWrapper}>
          <input
            type="range"
            min="0.75"
            max="1.50"
            step="0.05"
            className={styles.rangeSlider}
            value={draft.voice_speed}
            onChange={(e) => updateDraft({ voice_speed: parseFloat(e.target.value) })}
          />
          <span className={styles.sliderValue}>{draft.voice_speed.toFixed(2)}x</span>
        </div>
        <div className={styles.sliderLabels}>
          <span>0.75x — Deliberate</span>
          <span>1.0x — Standard Business</span>
          <span>1.5x — Fast Briefing</span>
        </div>
      </div>

      {/* Voice Pitch Slider */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>
          Vocal Pitch ({draft.voice_pitch >= 0 ? `+${draft.voice_pitch.toFixed(1)}` : draft.voice_pitch.toFixed(1)} semitones)
        </label>
        <div className={styles.sliderWrapper}>
          <input
            type="range"
            min="-6.0"
            max="6.0"
            step="0.5"
            className={styles.rangeSlider}
            value={draft.voice_pitch}
            onChange={(e) => updateDraft({ voice_pitch: parseFloat(e.target.value) })}
          />
          <span className={styles.sliderValue}>
            {draft.voice_pitch >= 0 ? `+${draft.voice_pitch.toFixed(1)}` : draft.voice_pitch.toFixed(1)}
          </span>
        </div>
        <div className={styles.sliderLabels}>
          <span>-6.0st — Deep Resonance</span>
          <span>0.0st — Natural</span>
          <span>+6.0st — Lighter Cadence</span>
        </div>
      </div>

      {/* Quick Test Voice Button */}
      <div style={{ marginTop: "2rem" }}>
        <button
          type="button"
          className={`${styles.actionBtn} ${styles.btnPrimary}`}
          onClick={() => previewVoice()}
          disabled={isPlayingVoice}
        >
          {isPlayingVoice ? "🔊 Playing Audio..." : "▶ Test Audio Synthesis"}
        </button>
      </div>
    </div>
  );
}
