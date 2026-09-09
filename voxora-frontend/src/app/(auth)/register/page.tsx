"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/stores/authStore";
import styles from "../auth.module.css";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading, error, clearError } = useAuthStore();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [tenantName, setTenantName] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await register(email, name, password, tenantName);
      router.push("/ask");
    } catch {
      // Error is handled by the store
    }
  };

  return (
    <div className={styles.authLayout}>
      {/* ── Left Brand Panel ─────────────────────────────── */}
      <div className={styles.brandPanel}>
        <div className={styles.brandContent}>
          <div className={styles.logoMark}>V</div>
          <h1 className={styles.brandTitle}>Voxora AI</h1>
          <p className={styles.brandTagline}>
            Join thousands of teams using conversational AI
            to unlock insights from their business data.
          </p>

          <div className={styles.features}>
            <div className={styles.feature}>
              <div className={styles.featureIcon}>⚡</div>
              <div className={styles.featureText}>
                <h4>Instant Setup</h4>
                <p>Connect your data and start asking in minutes</p>
              </div>
            </div>
            <div className={styles.feature}>
              <div className={styles.featureIcon}>🏢</div>
              <div className={styles.featureText}>
                <h4>Multi-Tenant</h4>
                <p>Isolated data for your entire organization</p>
              </div>
            </div>
            <div className={styles.feature}>
              <div className={styles.featureIcon}>🤖</div>
              <div className={styles.featureText}>
                <h4>Agent Studio</h4>
                <p>Customize your AI assistant&apos;s behavior and knowledge</p>
              </div>
            </div>
            <div className={styles.feature}>
              <div className={styles.featureIcon}>📈</div>
              <div className={styles.featureText}>
                <h4>AI Dashboards</h4>
                <p>Auto-generated analytics from conversations</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Right Form Panel ─────────────────────────────── */}
      <div className={styles.formPanel}>
        <div className={styles.formContainer}>
          <div className={styles.formHeader}>
            <h2 className={styles.formTitle}>Create your account</h2>
            <p className={styles.formSubtitle}>
              Already have an account?{" "}
              <Link href="/login">Sign in</Link>
            </p>
          </div>

          {error && (
            <div className={styles.errorMessage}>
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className={styles.formGroup}>
              <label htmlFor="name" className={styles.label}>
                Your name
              </label>
              <div className={styles.inputWrapper}>
                <input
                  id="name"
                  type="text"
                  className={styles.input}
                  placeholder="Dinithi Nimesha"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    clearError();
                  }}
                  required
                  autoComplete="name"
                  autoFocus
                />
                <span className={styles.inputIcon}>👤</span>
              </div>
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="email" className={styles.label}>
                Work email
              </label>
              <div className={styles.inputWrapper}>
                <input
                  id="email"
                  type="email"
                  className={styles.input}
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    clearError();
                  }}
                  required
                  autoComplete="email"
                />
                <span className={styles.inputIcon}>✉️</span>
              </div>
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="tenant" className={styles.label}>
                Organization name
              </label>
              <div className={styles.inputWrapper}>
                <input
                  id="tenant"
                  type="text"
                  className={styles.input}
                  placeholder="Acme Corporation"
                  value={tenantName}
                  onChange={(e) => {
                    setTenantName(e.target.value);
                    clearError();
                  }}
                  required
                />
                <span className={styles.inputIcon}>🏢</span>
              </div>
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="password" className={styles.label}>
                Password
              </label>
              <div className={styles.inputWrapper}>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  className={styles.input}
                  placeholder="Minimum 8 characters"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    clearError();
                  }}
                  required
                  minLength={8}
                  autoComplete="new-password"
                />
                <span className={styles.inputIcon}>🔑</span>
                <button
                  type="button"
                  className={styles.passwordToggle}
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                >
                  {showPassword ? "🙈" : "👁️"}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className={styles.submitBtn}
              disabled={isLoading || !name || !email || !tenantName || !password}
            >
              <span>
                {isLoading && <div className={styles.spinner} />}
                {isLoading ? "Creating account..." : "Create account"}
              </span>
            </button>
          </form>

          <div className={styles.divider}>or continue with</div>

          <div className={styles.socialButtons}>
            <button type="button" className={styles.socialBtn}>
              <span>🔵</span> Google
            </button>
            <button type="button" className={styles.socialBtn}>
              <span>⬛</span> Microsoft
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
