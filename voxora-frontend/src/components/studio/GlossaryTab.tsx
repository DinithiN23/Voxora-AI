"use client";

import React, { useState } from "react";
import { useAgentStudioStore } from "@/stores/agentStudioStore";
import styles from "@/app/(app)/studio/studio.module.css";

const RECOMMENDED_TERMS = [
  {
    term: "Gross Margin",
    definition: "Gross Profit divided by Total Revenue expressed as a percentage. Target benchmark > 55%.",
  },
  {
    term: "AOV",
    definition: "Average Order Value: Total Revenue divided by Total Order Count ($2.9K in Superstore).",
  },
  {
    term: "Customer Segments",
    definition: "Enterprise ($1.5M+ spend), Mid-Market ($500K-$1.5M spend), and SMB (<$500K spend).",
  },
  {
    term: "EBITDA Margin",
    definition: "Operating earnings before interest, taxes, depreciation, and amortization divided by revenue.",
  },
  {
    term: "Direct Sales",
    definition: "Revenue originated by dedicated Enterprise Account Executive direct sales contracts.",
  },
  {
    term: "Fiscal Year",
    definition: "Standard financial operating calendar year ending December 31st.",
  },
];

export default function GlossaryTab() {
  const { draft, addGlossaryItem, removeGlossaryItem, updateDraft } = useAgentStudioStore();
  const [newTerm, setNewTerm] = useState("");
  const [newDefinition, setNewDefinition] = useState("");

  if (!draft) return null;

  const handleAddTerm = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTerm.trim() || !newDefinition.trim()) return;

    addGlossaryItem({
      term: newTerm.trim(),
      definition: newDefinition.trim(),
    });

    setNewTerm("");
    setNewDefinition("");
  };

  const handleImportRecommended = () => {
    const existing = draft.knowledge_glossary || [];
    const existingTerms = new Set(existing.map((g) => g.term.toLowerCase()));
    const toAdd = RECOMMENDED_TERMS.filter((r) => !existingTerms.has(r.term.toLowerCase()));

    updateDraft({
      knowledge_glossary: [...existing, ...toAdd],
    });
  };

  return (
    <div>
      <div className={styles.glossaryControls}>
        <div>
          <h2 className={styles.panelTitle}>Knowledge Base & Business Glossary</h2>
          <p className={styles.panelDescription} style={{ marginBottom: 0 }}>
            Define custom organizational formulas, KPI calculation rules, and company acronyms. Voxora injects these into every answer.
          </p>
        </div>
        <button
          type="button"
          className={`${styles.actionBtn} ${styles.btnSecondary}`}
          onClick={handleImportRecommended}
        >
          Import Recommended Metrics
        </button>
      </div>

      {/* Add New Term Form */}
      <form onSubmit={handleAddTerm} className={styles.addTermRow} style={{ marginTop: "1.5rem" }}>
        <input
          type="text"
          className={styles.formInput}
          placeholder="Term (e.g. Net Margin)"
          value={newTerm}
          onChange={(e) => setNewTerm(e.target.value)}
        />
        <input
          type="text"
          className={styles.formInput}
          placeholder="Definition / Business calculation rule..."
          value={newDefinition}
          onChange={(e) => setNewDefinition(e.target.value)}
        />
        <button
          type="submit"
          className={`${styles.actionBtn} ${styles.btnPrimary}`}
          disabled={!newTerm.trim() || !newDefinition.trim()}
        >
          + Add Term
        </button>
      </form>

      {/* Term List */}
      <div className={styles.termList}>
        {(draft.knowledge_glossary || []).map((item, idx) => (
          <div key={idx} className={styles.termItem}>
            <div className={styles.termContent}>
              <h4 className={styles.termTitle}>{item.term}</h4>
              <p className={styles.termDefinition}>{item.definition}</p>
            </div>
            <button
              type="button"
              className={styles.deleteTermBtn}
              onClick={() => removeGlossaryItem(idx)}
              title="Remove term"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 6h18" />
                <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
              </svg>
            </button>
          </div>
        ))}

        {(!draft.knowledge_glossary || draft.knowledge_glossary.length === 0) && (
          <div style={{ textAlign: "center", padding: "2rem", color: "#64748b" }}>
            No glossary terms defined yet. Click &quot;Import Recommended Metrics&quot; above to seed standard C-suite definitions.
          </div>
        )}
      </div>
    </div>
  );
}
