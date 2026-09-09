"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/stores/authStore";
import styles from "../auth.module.css";

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading, error, clearError } = useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
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
            Ask questions about your business in plain English.
            Get instant answers, insights, and visualizations.
          </p>

          <div className={styles.features}>
            <div className={styles.feature}>
              <div className={styles.featureIcon}>🎙️</div>
              <div className={styles.featureText}>
                <h4>Voice & Text</h4>
                <p>Speak or type your business questions naturally</p>
              </div>
            </div>
            <div className={styles.feature}>
              <div className={styles.featureIcon}>📊</div>
              <div className={styles.featureText}>
                <h4>Smart Visualizations</h4>
                <p>AI-generated charts and dashboards, instantly</p>
              </div>
            </div>
            <div className={styles.feature}>
              <div className={styles.featureIcon}>💬</div>
              <div className={styles.featureText}>
                <h4>Conversational Context</h4>
                <p>Follow-up questions that remember what you asked</p>
              </div>
            </div>
            <div className={styles.feature}>
              <div className={styles.featureIcon}>🔒</div>
              <div className={styles.featureText}>
                <h4>Enterprise Security</h4>
                <p>Role-based access to your business data</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Right Form Panel ─────────────────────────────── */}
      <div className={styles.formPanel}>
        <div className={styles.formContainer}>
          <div className={styles.formHeader}>
            <h2 className={styles.formTitle}>Welcome back</h2>
            <p className={styles.formSubtitle}>
              Don&apos;t have an account?{" "}
              <Link href="/register">Create one</Link>
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
              <label htmlFor="email" className={styles.label}>
                Email address
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
                  autoFocus
                />
                <span className={styles.inputIcon}>✉️</span>
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
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    clearError();
                  }}
                  required
                  autoComplete="current-password"
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
              disabled={isLoading || !email || !password}
            >
              <span>
                {isLoading && <div className={styles.spinner} />}
                {isLoading ? "Signing in..." : "Sign in"}
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
