import styles from "../coming-soon.module.css";

export default function DashboardsPage() {
  return (
    <div className={styles.comingSoon}>
      <div className={styles.comingSoonIcon}>📊</div>
      <h1 className={styles.comingSoonTitle}>Dashboards</h1>
      <p className={styles.comingSoonDesc}>
        Traditional and AI-generated analytics dashboards. 
        Create custom views, share with your team, and let Voxora 
        build dashboards from your conversations.
      </p>
      <div className={styles.comingSoonBadge}>
        🚧 Coming in Phase 4
      </div>
    </div>
  );
}
