"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import styles from "./MarkdownRenderer.module.css";

interface MarkdownRendererProps {
  content: string;
  isStreaming?: boolean;
}

export default function MarkdownRenderer({ content, isStreaming }: MarkdownRendererProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleCopy = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  let codeBlockCounter = 0;

  return (
    <div className={styles.markdownContainer}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ children }) => (
            <div className={styles.tableWrapper}>
              <table className={styles.table}>{children}</table>
            </div>
          ),
          code: ({ className, children, ...props }) => {
            const isInline = !className && typeof children === "string" && !children.includes("\n");
            if (isInline) {
              return (
                <code className={styles.inlineCode} {...props}>
                  {children}
                </code>
              );
            }

            const codeText = String(children).replace(/\n$/, "");
            const blockId = codeBlockCounter++;
            const match = /language-(\w+)/.exec(className || "");
            const lang = match ? match[1] : "code";

            return (
              <div className={styles.codeBlockWrapper}>
                <div className={styles.codeBlockHeader}>
                  <span>{lang}</span>
                  <button
                    type="button"
                    className={styles.copyCodeBtn}
                    onClick={() => handleCopy(codeText, blockId)}
                  >
                    {copiedIndex === blockId ? (
                      "✓ Copied"
                    ) : (
                      <span style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                        </svg>
                        <span>Copy</span>
                      </span>
                    )}
                  </button>
                </div>
                <pre className={styles.codeBlock}>
                  <code>{children}</code>
                </pre>
              </div>
            );
          },
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "var(--vx-brand-primary, #10b981)", textDecoration: "underline" }}
            >
              {children}
            </a>
          ),
        }}
      >
        {content}
      </ReactMarkdown>

      {isStreaming && <span className={styles.streamCursor}>▌</span>}
    </div>
  );
}
