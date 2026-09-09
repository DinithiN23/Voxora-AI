"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import styles from "./ask.module.css";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  inputMode: "text" | "voice";
  timestamp: Date;
}

// Simple markdown-like rendering for bold and tables
function renderContent(content: string) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let tableRows: string[][] = [];
  let inTable = false;
  let tableKey = 0;

  const processInline = (text: string) => {
    // Bold: **text**
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  const flushTable = () => {
    if (tableRows.length > 0) {
      const header = tableRows[0];
      const body = tableRows.slice(1).filter(
        (row) => !row.every((cell) => /^[-|:\s]+$/.test(cell))
      );

      elements.push(
        <table key={`table-${tableKey++}`}>
          <thead>
            <tr>
              {header.map((cell, i) => (
                <th key={i}>{processInline(cell.trim())}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {body.map((row, ri) => (
              <tr key={ri}>
                {row.map((cell, ci) => (
                  <td key={ci}>{processInline(cell.trim())}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
      tableRows = [];
    }
    inTable = false;
  };

  lines.forEach((line, i) => {
    if (line.startsWith("|")) {
      inTable = true;
      const cells = line
        .split("|")
        .filter((c) => c.trim() !== "");
      tableRows.push(cells);
    } else {
      if (inTable) flushTable();

      if (line.startsWith("- ")) {
        elements.push(
          <div key={i} style={{ paddingLeft: "16px", marginBottom: "4px" }}>
            • {processInline(line.slice(2))}
          </div>
        );
      } else if (line.trim() === "") {
        elements.push(<br key={i} />);
      } else {
        elements.push(
          <p key={i} style={{ marginBottom: "4px" }}>
            {processInline(line)}
          </p>
        );
      }
    }
  });

  if (inTable) flushTable();

  return elements;
}

// Simulated AI responses for demo
function getSimulatedResponse(question: string): {
  content: string;
  suggestions: string[];
} {
  const q = question.toLowerCase();

  if (q.includes("sales") && (q.includes("month") || q.includes("today"))) {
    return {
      content:
        "Based on the available data, September sales are currently tracking at **$2.4M**, which represents an **8.7% increase** compared to the same period last month.\n\nKey highlights:\n- Daily average: $343K\n- Strongest day: September 3 ($412K)\n- On track to exceed the monthly target of $3.2M",
      suggestions: [
        "What are the top-performing products?",
        "Compare with last month",
        "Show sales by region",
        "Which region is growing fastest?",
      ],
    };
  }

  if (q.includes("top") && q.includes("product")) {
    return {
      content:
        "Here are the **top-selling products** this month:\n\n| Rank | Product | Units | Revenue |\n|------|---------|-------|---------|\n| 1 | Product A | 12,450 | $430K |\n| 2 | Product B | 10,320 | $381K |\n| 3 | Product C | 8,940 | $312K |\n| 4 | Product D | 6,780 | $242K |\n| 5 | Product E | 5,210 | $194K |\n\n**Product A** is the clear leader, contributing approximately **18%** of total product revenue. Product B is close behind with strong growth in the Eastern region.",
      suggestions: [
        "Compare these with last month",
        "Show revenue by region for Product A",
        "Which products are declining?",
        "What's the profit margin by product?",
      ],
    };
  }

  if (q.includes("compare") || q.includes("last month")) {
    return {
      content:
        "Comparing current month with last month:\n\n| Metric | This Month | Last Month | Change |\n|--------|-----------|------------|--------|\n| Revenue | $2.4M | $2.21M | ↑ 8.7% |\n| Orders | 3,842 | 3,510 | ↑ 9.5% |\n| Avg Order Value | $625 | $630 | ↓ 0.8% |\n| New Customers | 284 | 251 | ↑ 13.1% |\n\nRevenue is growing primarily due to **higher order volume** rather than increased order values. The **13.1% increase** in new customers is a particularly positive signal.",
      suggestions: [
        "Why did revenue increase?",
        "Show the trend over 6 months",
        "Which category grew the most?",
        "Forecast next month",
      ],
    };
  }

  if (
    q.includes("why") &&
    (q.includes("drop") || q.includes("decrease") || q.includes("fell") || q.includes("decline") || q.includes("increase"))
  ) {
    return {
      content:
        "Analysing the performance change:\n\nThe largest contributing factor was activity in the **Western region**, where order volume changed by **22%**.\n\nPotential causes:\n- A major distributor reported inventory changes\n- Competitor launched a campaign in the same region\n- Seasonal patterns show historical trends in this period\n\nWould you like me to drill deeper into the regional data?",
      suggestions: [
        "Show me Western region details",
        "Break down by customer segment",
        "Show channel performance",
        "What about other regions?",
      ],
    };
  }

  if (q.includes("region") || q.includes("western")) {
    return {
      content:
        "Here's the **regional performance** breakdown:\n\n| Region | Revenue | Orders | Growth |\n|--------|---------|--------|--------|\n| Eastern | $820K | 1,245 | ↑ 14.2% |\n| Western | $580K | 892 | ↓ 6.8% |\n| Central | $640K | 1,024 | ↑ 9.1% |\n| Southern | $360K | 681 | ↑ 3.4% |\n\nThe **Eastern region** continues to outperform all others. The Western region's decline warrants attention — particularly the drop in new customer acquisition.",
      suggestions: [
        "Drill into Eastern region",
        "Show customer trends by region",
        "Compare regional performance over 6 months",
        "What products sell best in each region?",
      ],
    };
  }

  return {
    content:
      "I understand your question. In the current preview, I'm using sample responses to demonstrate the conversational flow.\n\nOnce connected to your data sources, I'll be able to:\n- Query your business data in real-time\n- Provide accurate insights and analysis\n- Generate dynamic visualizations\n- Remember context for follow-up questions\n\nTry asking about **sales performance**, **top products**, **comparisons**, or **regional data**!",
    suggestions: [
      "How are sales this month?",
      "Show top-selling products",
      "Compare this month with last month",
      "Show regional performance",
    ],
  };
}

export default function AskPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  const sendMessage = useCallback(
    async (text: string, mode: "text" | "voice" = "text") => {
      if (!text.trim()) return;

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text.trim(),
        inputMode: mode,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setSuggestions([]);
      setIsTyping(true);

      // Attempt real AI call via backend
      try {
        let convId = conversationId;
        if (!convId) {
          try {
            const newConv = await api.post<{ id: string }>("/api/v1/conversations", {
              title: text.trim().slice(0, 60),
            });
            convId = newConv.id;
            setConversationId(convId);
          } catch {
            // Unauthenticated or offline fallback
          }
        }

        if (convId) {
          const res = await api.post<{
            message: { id: string; content: string; role: string };
            suggestions: string[];
          }>(`/api/v1/conversations/${convId}/messages`, {
            content: text.trim(),
            input_mode: mode,
          });

          const aiMsg: ChatMessage = {
            id: res.message.id,
            role: "assistant",
            content: res.message.content,
            inputMode: "text",
            timestamp: new Date(),
          };

          setMessages((prev) => [...prev, aiMsg]);
          if (res.suggestions && res.suggestions.length > 0) {
            setSuggestions(res.suggestions);
          }
          setIsTyping(false);
          return;
        }
      } catch (err) {
        console.warn("Backend conversation call failed, falling back to local simulation:", err);
      }

      // Graceful fallback simulation
      await new Promise((resolve) => setTimeout(resolve, 800 + Math.random() * 500));

      const response = getSimulatedResponse(text);

      const aiMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.content,
        inputMode: "text",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMsg]);
      setSuggestions(response.suggestions);
      setIsTyping(false);
    },
    [conversationId]
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  const toggleVoice = () => {
    if (isListening) {
      setIsListening(false);
      // In production: stop SpeechRecognition
    } else {
      setIsListening(true);
      // In production: start SpeechRecognition
      // Simulate voice input for demo
      setTimeout(() => {
        setIsListening(false);
        sendMessage("How are sales performing this month?", "voice");
      }, 2500);
    }
  };

  const hasMessages = messages.length > 0;

  const defaultSuggestions = [
    { icon: "📈", text: "How are sales performing this month?" },
    { icon: "🏆", text: "What are our top 10 products?" },
    { icon: "📊", text: "Compare this month with last month" },
    { icon: "🌍", text: "Show regional performance breakdown" },
  ];

  return (
    <div className={styles.askPage}>
      {!hasMessages ? (
        /* ── Welcome / Empty State ──────────────────────── */
        <div className={styles.welcomeContainer}>
          <div className={styles.welcomeOrb}>✨</div>
          <h1 className={styles.welcomeTitle}>
            Good afternoon, <span className="vx-gradient-text">Dinithi</span>
          </h1>
          <p className={styles.welcomeSubtitle}>
            What would you like to know about your business?
          </p>

          {/* Voice Button */}
          <div className={styles.voiceSection}>
            <button
              className={`${styles.voiceBtn} ${
                isListening ? styles.listening : ""
              }`}
              onClick={toggleVoice}
            >
              🎙️
            </button>
            <span className={styles.voiceLabel}>
              {isListening ? "Listening..." : "Ask by voice"}
            </span>
          </div>

          {/* Suggested Questions */}
          <div className={styles.suggestions}>
            {defaultSuggestions.map((s, i) => (
              <button
                key={i}
                className={styles.suggestionCard}
                onClick={() => handleSuggestionClick(s.text)}
              >
                <span className={styles.suggestionIcon}>{s.icon}</span>
                {s.text}
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* ── Chat Area ──────────────────────────────────── */
        <div className={styles.chatArea}>
          {messages.map((msg) => (
            <div key={msg.id} className={styles.messageGroup}>
              {msg.role === "user" ? (
                <div className={styles.userMessage}>
                  <div className={styles.userBubble}>
                    {msg.inputMode === "voice" && (
                      <div className={styles.voiceIndicator}>🎙️ Voice</div>
                    )}
                    {msg.content}
                  </div>
                </div>
              ) : (
                <div className={styles.assistantMessage}>
                  <div className={styles.assistantAvatar}>V</div>
                  <div className={styles.assistantBubble}>
                    {renderContent(msg.content)}
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className={styles.typingIndicator}>
              <div className={styles.assistantAvatar}>V</div>
              <div className={styles.typingDots}>
                <div className={styles.typingDot} />
                <div className={styles.typingDot} />
                <div className={styles.typingDot} />
              </div>
            </div>
          )}

          {/* Follow-up Suggestions */}
          {suggestions.length > 0 && !isTyping && (
            <div className={styles.followUpSuggestions}>
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  className={styles.followUpChip}
                  onClick={() => handleSuggestionClick(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          <div ref={chatEndRef} />
        </div>
      )}

      {/* ── Input Bar ────────────────────────────────────── */}
      <div className={styles.inputArea}>
        <form className={styles.inputBar} onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            type="text"
            className={styles.textInput}
            placeholder="Ask anything about your business..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isTyping}
          />
          <button
            type="button"
            className={`${styles.inputVoiceBtn} ${
              isListening ? styles.active : ""
            }`}
            onClick={toggleVoice}
          >
            🎙️
          </button>
          <button
            type="submit"
            className={styles.sendBtn}
            disabled={!input.trim() || isTyping}
          >
            ➤
          </button>
        </form>
        <p className={styles.inputHint}>
          Voxora can make mistakes. Always verify important data.
        </p>
      </div>
    </div>
  );
}
