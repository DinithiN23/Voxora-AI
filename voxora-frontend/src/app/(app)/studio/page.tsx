import styles from "../coming-soon.module.css";

export default function StudioPage() {
  return (
    <div className={styles.comingSoon}>
      <div className={styles.comingSoonIcon}>🤖</div>
      <h1 className={styles.comingSoonTitle}>Agent Studio</h1>
      <p className={styles.comingSoonDesc}>
        Configure your AI assistant&apos;s voice, personality, knowledge base,
        and data access rules. Create custom agents for different teams
        and use cases.
      </p>
      <div className={styles.comingSoonBadge}>
        🚧 Coming in Phase 5
      </div>
    </div>
  );
}
