"use client";

import React from "react";
import { useAgentStudioStore } from "@/stores/agentStudioStore";
import styles from "@/app/(app)/studio/studio.module.css";

const ALL_BUSINESS_AREAS = [
  "Revenue & Finance",
  "Product Performance",
  "Customer Intelligence",
  "Regional Operations",
  "Marketing Attribution",
  "Executive HR & Headcount",
];

const cleanStr = (s: string) => s.replace(/[^\w\s&]/gi, "").trim();

export default function DataAccessTab() {
  const { draft, updateDraft } = useAgentStudioStore();

  if (!draft) return null;

  const currentAreas = draft.allowed_data_areas || [];

  const toggleArea = (area: string) => {
    const isSelected = currentAreas.some(
      (a) => cleanStr(a).toLowerCase() === cleanStr(area).toLowerCase()
    );
    if (isSelected) {
      updateDraft({
        allowed_data_areas: currentAreas.filter(
          (a) => cleanStr(a).toLowerCase() !== cleanStr(area).toLowerCase()
        ),
      });
    } else {
      updateDraft({ allowed_data_areas: [...currentAreas, area] });
    }
  };

  const toggleRule = (ruleKey: string) => {
    const rules = draft.data_access_rules || {};
    updateDraft({
      data_access_rules: {
        ...rules,
        [ruleKey]: !rules[ruleKey],
      },
    });
  };

  return (
    <div>
      <h2 className={styles.panelTitle}>Data Access, Areas & Governance</h2>
      <p className={styles.panelDescription}>
        Control which departments, data domains, and security guardrails this agent can query within Google BigQuery.
      </p>

      {/* Business Areas */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>Permitted Business Domains</label>
        <div className={styles.chipsContainer}>
          {ALL_BUSINESS_AREAS.map((area) => {
            const isSelected = currentAreas.some(
              (a) => cleanStr(a).toLowerCase() === cleanStr(area).toLowerCase()
            );
            return (
              <button
                key={area}
                type="button"
                className={`${styles.areaChip} ${isSelected ? styles.areaChipSelected : ""}`}
                onClick={() => toggleArea(area)}
              >
                <span>{area}</span>
                {isSelected && <span style={{ fontSize: "0.75rem" }}>✓</span>}
              </button>
            );
          })}
        </div>
      </div>

      {/* Governance Rules */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>Security & SQL Execution Policies</label>
        <div className={styles.governanceList}>
          {/* PII Masking */}
          <div className={styles.governanceItem}>
            <div className={styles.governanceInfo}>
              <h4>Strict Customer PII Masking</h4>
              <p>Mask customer credit cards, phone numbers, and full names in text-to-SQL results.</p>
            </div>
            <label className={styles.toggleSwitch}>
              <input
                type="checkbox"
                checked={!!draft.data_access_rules?.mask_pii}
                onChange={() => toggleRule("mask_pii")}
              />
              <span className={styles.toggleSlider} />
            </label>
          </div>

          {/* Safe Read-Only Queries */}
          <div className={styles.governanceItem}>
            <div className={styles.governanceInfo}>
              <h4>Read-Only BigQuery Enforcement</h4>
              <p>Block any DDL/DML statements (DROP, DELETE, UPDATE, INSERT, ALTER).</p>
            </div>
            <label className={styles.toggleSwitch}>
              <input
                type="checkbox"
                checked={!!draft.data_access_rules?.read_only}
                onChange={() => toggleRule("read_only")}
              />
              <span className={styles.toggleSlider} />
            </label>
          </div>

          {/* Auto-visualize */}
          <div className={styles.governanceItem}>
            <div className={styles.governanceInfo}>
              <h4>Auto-Generate Visualizations</h4>
              <p>Automatically recommend and render Recharts (Bar, Line, Area, Pie) for numerical queries.</p>
            </div>
            <label className={styles.toggleSwitch}>
              <input
                type="checkbox"
                checked={!!draft.data_access_rules?.auto_visualize}
                onChange={() => toggleRule("auto_visualize")}
              />
              <span className={styles.toggleSlider} />
            </label>
          </div>

          {/* Auto SQL Generation */}
          <div className={styles.governanceItem}>
            <div className={styles.governanceInfo}>
              <h4>Automated Text-to-SQL Translation</h4>
              <p>Allow the agent to translate natural language questions directly into executable BigQuery queries.</p>
            </div>
            <label className={styles.toggleSwitch}>
              <input
                type="checkbox"
                checked={!!draft.data_access_rules?.allow_sql_generation}
                onChange={() => toggleRule("allow_sql_generation")}
              />
              <span className={styles.toggleSlider} />
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
