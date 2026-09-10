"use client";

import React from "react";
import { useAgentStudioStore } from "@/stores/agentStudioStore";
import styles from "@/app/(app)/studio/studio.module.css";

export default function PromptTab() {
  const { draft, updateDraft } = useAgentStudioStore();

  if (!draft) return null;

  const handleInsertVariable = (variable: string) => {
    updateDraft({
      system_prompt: draft.system_prompt + ` ${variable} `,
    });
  };

  return (
    <div>
      <h2 className={styles.panelTitle}>System Prompt & Guardrails</h2>
      <p className={styles.panelDescription}>
        Configure the core foundational instructions, welcome greetings, and boundary guardrails executed by the LLM.
      </p>

      {/* System Prompt */}
      <div className={styles.formGroup}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
          <label className={styles.formLabel} style={{ margin: 0 }}>
            Master System Prompt
          </label>
          <div style={{ display: "flex", gap: "0.4rem" }}>
            <span style={{ fontSize: "0.75rem", color: "#64748b", alignSelf: "center", marginRight: "0.3rem" }}>
              Insert context:
            </span>
            <button
              type="button"
              className={styles.promptChip}
              onClick={() => handleInsertVariable("{user_name}")}
            >
              + {'{user_name}'}
            </button>
            <button
              type="button"
              className={styles.promptChip}
              onClick={() => handleInsertVariable("{company_name}")}
            >
              + {'{company_name}'}
            </button>
            <button
              type="button"
              className={styles.promptChip}
              onClick={() => handleInsertVariable("{fiscal_year}")}
            >
              + {'{fiscal_year}'}
            </button>
          </div>
        </div>
        <textarea
          className={`${styles.formTextarea} ${styles.codeTextarea}`}
          value={draft.system_prompt}
          onChange={(e) => updateDraft({ system_prompt: e.target.value })}
          placeholder="System instructions for the AI business intelligence copilot..."
          rows={12}
        />
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "#64748b", marginTop: "0.4rem" }}>
          <span>Monospaced markdown editor</span>
          <span>{draft.system_prompt.length} characters • ~{Math.round(draft.system_prompt.length / 4)} tokens</span>
        </div>
      </div>

      {/* Greeting Message */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>Welcome Greeting Message</label>
        <textarea
          className={styles.formTextarea}
          style={{ minHeight: "80px" }}
          value={draft.greeting_message}
          onChange={(e) => updateDraft({ greeting_message: e.target.value })}
          placeholder="First message spoken or displayed when opening a conversation."
        />
      </div>

      {/* Fallback & Boundary Rules */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>Boundary & Fallback Rules</label>
        <textarea
          className={styles.formTextarea}
          style={{ minHeight: "80px" }}
          value={draft.fallback_message}
          onChange={(e) => updateDraft({ fallback_message: e.target.value })}
          placeholder="Instructions on what to answer when queries fall outside BI / company data scope."
        />
      </div>
    </div>
  );
}
