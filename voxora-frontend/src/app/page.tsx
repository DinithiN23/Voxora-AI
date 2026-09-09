import Link from "next/link";
import styles from "./landing.module.css";

export default function LandingPage() {
  return (
    <div className={styles.landing}>
      {/* ── Navbar ────────────────────────────────────────── */}
      <nav className={styles.navbar}>
        <div className={styles.navLogo}>
          <div className={styles.navLogoMark}>V</div>
          <span className={styles.navLogoText}>Voxora</span>
        </div>
        <div className={styles.navActions}>
          <Link href="/login" className={styles.navLink}>
            Sign in
          </Link>
          <Link href="/register" className={styles.navCta}>
            Get Started
          </Link>
        </div>
      </nav>

      {/* ── Hero ──────────────────────────────────────────── */}
      <section className={styles.hero}>
        <div className={styles.heroBadge}>✨ Conversational Business Intelligence</div>

        <h1 className={styles.heroTitle}>
          Ask your data anything.{" "}
          <span className="vx-gradient-text">Get answers instantly.</span>
        </h1>

        <p className={styles.heroSubtitle}>
          Voxora AI transforms how teams interact with business data.
          Speak or type natural-language questions and receive accurate
          insights, charts, and dashboards — powered by AI.
        </p>

        <div className={styles.heroActions}>
          <Link href="/register" className={styles.heroPrimary}>
            Start Free Trial →
          </Link>
          <Link href="/ask" className={styles.heroSecondary}>
            🎙️ Try the Demo
          </Link>
        </div>

        {/* ── Demo Preview ────────────────────────────────── */}
        <div className={styles.demoPreview}>
          <div className={styles.demoHeader}>
            <div className={`${styles.demoDot} ${styles.demoDotRed}`} />
            <div className={`${styles.demoDot} ${styles.demoDotYellow}`} />
            <div className={`${styles.demoDot} ${styles.demoDotGreen}`} />
          </div>

          <div className={styles.demoMessage}>
            <div className={styles.demoUserBubble}>
              How were sales this month?
            </div>
          </div>

          <div className={styles.demoAiBubble}>
            September sales are currently at <strong>$2.4M</strong>, up{" "}
            <strong>8.7%</strong> compared with the same period last month.
            Daily average stands at $343K with the strongest day on September 3.
          </div>

          <div className={styles.demoKpi}>
            <div className={styles.demoKpiCard}>
              <div className={styles.demoKpiValue}>$2.4M</div>
              <div className={styles.demoKpiLabel}>Monthly Revenue</div>
              <div className={styles.demoKpiBadge}>↑ 8.7%</div>
            </div>
            <div className={styles.demoKpiCard}>
              <div className={styles.demoKpiValue}>3,842</div>
              <div className={styles.demoKpiLabel}>Total Orders</div>
              <div className={styles.demoKpiBadge}>↑ 9.5%</div>
            </div>
            <div className={styles.demoKpiCard}>
              <div className={styles.demoKpiValue}>284</div>
              <div className={styles.demoKpiLabel}>New Customers</div>
              <div className={styles.demoKpiBadge}>↑ 13.1%</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────── */}
      <section className={styles.features}>
        <h2 className={styles.sectionTitle}>
          Three powerful experiences
        </h2>
        <p className={styles.sectionSubtitle}>
          Everything you need to turn data into decisions
        </p>

        <div className={styles.featureGrid}>
          <div className={styles.featureCard}>
            <div className={styles.featureCardIcon}>💬</div>
            <h3 className={styles.featureCardTitle}>Ask Voxora</h3>
            <p className={styles.featureCardDesc}>
              Conversational text and voice BI. Ask questions in plain English, 
              get answers with charts and follow-up context.
            </p>
          </div>

          <div className={styles.featureCard}>
            <div className={styles.featureCardIcon}>📊</div>
            <h3 className={styles.featureCardTitle}>Dashboards</h3>
            <p className={styles.featureCardDesc}>
              Traditional and AI-generated analytics dashboards. 
              Auto-created from your conversations or built manually.
            </p>
          </div>

          <div className={styles.featureCard}>
            <div className={styles.featureCardIcon}>🤖</div>
            <h3 className={styles.featureCardTitle}>Agent Studio</h3>
            <p className={styles.featureCardDesc}>
              Configure your AI agent&apos;s voice, behaviour, data access, 
              prompts, and business knowledge — all in one place.
            </p>
          </div>

          <div className={styles.featureCard}>
            <div className={styles.featureCardIcon}>🎙️</div>
            <h3 className={styles.featureCardTitle}>Voice-First</h3>
            <p className={styles.featureCardDesc}>
              Speak your questions naturally. Hear AI responses aloud. 
              Full voice flow with barge-in and context retention.
            </p>
          </div>

          <div className={styles.featureCard}>
            <div className={styles.featureCardIcon}>🔒</div>
            <h3 className={styles.featureCardTitle}>Enterprise Security</h3>
            <p className={styles.featureCardDesc}>
              Multi-tenant isolation, role-based access, 
              permission-gated data — the AI never sees what you can&apos;t.
            </p>
          </div>

          <div className={styles.featureCard}>
            <div className={styles.featureCardIcon}>🧠</div>
            <h3 className={styles.featureCardTitle}>Context Memory</h3>
            <p className={styles.featureCardDesc}>
              Follow-up questions that remember what you asked. 
              &quot;Compare those with last month&quot; just works.
            </p>
          </div>
        </div>
      </section>

      {/* ── Flow ──────────────────────────────────────────── */}
      <section className={styles.flow}>
        <h2 className={styles.sectionTitle}>How it works</h2>
        <p className={styles.sectionSubtitle}>
          From question to answer in seconds
        </p>

        <div className={styles.flowSteps}>
          <div className={styles.flowStep}>💬 Ask</div>
          <span className={styles.flowArrow}>→</span>
          <div className={styles.flowStep}>🧠 Understand</div>
          <span className={styles.flowArrow}>→</span>
          <div className={styles.flowStep}>🔍 Query</div>
          <span className={styles.flowArrow}>→</span>
          <div className={styles.flowStep}>📊 Analyse</div>
          <span className={styles.flowArrow}>→</span>
          <div className={styles.flowStep}>💡 Explain</div>
          <span className={styles.flowArrow}>→</span>
          <div className={styles.flowStep}>📈 Visualize</div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────── */}
      <section className={styles.cta}>
        <div className={styles.ctaCard}>
          <h2 className={styles.ctaTitle}>
            Ready to talk to your data?
          </h2>
          <p className={styles.ctaDesc}>
            Start asking questions in minutes. No complex setup required.
          </p>
          <Link href="/register" className={styles.heroPrimary}>
            Get Started Free →
          </Link>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────── */}
      <footer className={styles.footer}>
        © 2026 Voxora AI. Conversational Business Intelligence.
      </footer>
    </div>
  );
}
