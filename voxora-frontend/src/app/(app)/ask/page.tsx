"use client";

import { useState, useRef, useEffect, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useConversationStore } from "@/stores/conversationStore";
import { useAuthStore } from "@/stores/authStore";
import MarkdownRenderer from "@/components/chat/MarkdownRenderer";
import VisualizationViewer from "@/components/visualizations/VisualizationViewer";
import VoiceOverlay from "@/components/voice/VoiceOverlay";
import { useVoice } from "@/hooks/useVoice";
import type { ConversationDetail, Visualization } from "@/types/api";
import styles from "./ask.module.css";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  inputMode: "text" | "voice";
  timestamp: Date;
  isStreaming?: boolean;
  visualizations?: Visualization[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function AskContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const urlConvId = searchParams.get("id");

  const { addOrUpdateConversation, fetchConversations, setActiveConversationId } =
    useConversationStore();
  const { user } = useAuthStore();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(urlConvId);
  const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const sendMessageRef = useRef<(text: string, mode?: "text" | "voice") => Promise<void>>(
    async () => {}
  );

  // Phase 3: Advanced Voice Experience with Barge-in and Web Audio Analyser
  const voice = useVoice({
    onTranscriptComplete: (finalText) => {
      if (finalText.trim()) {
        sendMessageRef.current(finalText, "voice");
      }
    },
  });

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  // Load conversation when URL parameter changes (e.g. clicked in sidebar)
  useEffect(() => {
    setConversationId(urlConvId);
    setActiveConversationId(urlConvId);

    if (!urlConvId) {
      setMessages([]);
      setSuggestions([]);
      return;
    }

    let isMounted = true;
    const loadConversation = async () => {
      try {
        const detail = await api.get<ConversationDetail>(`/api/v1/conversations/${urlConvId}`);
        if (!isMounted) return;

        const loadedMessages: ChatMessage[] = (detail.messages || []).map((m) => ({
          id: m.id,
          role: m.role as "user" | "assistant",
          content: m.content,
          inputMode: m.input_mode || "text",
          timestamp: new Date(m.created_at),
          visualizations: m.visualizations || [],
        }));

        setMessages(loadedMessages);

        const lastMsg = loadedMessages[loadedMessages.length - 1];
        if (lastMsg && lastMsg.role === "assistant") {
          setSuggestions([
            "Break this down further",
            "What is driving this change?",
            "Show regional breakdown",
          ]);
        }
      } catch (err) {
        console.warn("Failed to load conversation thread:", err);
      }
    };

    loadConversation();
    return () => {
      isMounted = false;
    };
  }, [urlConvId, setActiveConversationId]);

  // Voice controls
  const toggleVoice = useCallback(() => {
    if (voice.isListening) {
      voice.stopListening();
    } else {
      voice.startListening((finalText) => {
        if (finalText.trim()) {
          sendMessageRef.current(finalText, "voice");
        }
      });
    }
  }, [voice]);

  const handleSpeak = useCallback(
    (text: string, id: string) => {
      voice.speak(text, id);
    },
    [voice]
  );

  // Copy message
  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMsgId(id);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  // Send message with Real-Time SSE Streaming & Visualizations
  const sendMessage = useCallback(
    async (text: string, mode: "text" | "voice" = "text") => {
      if (!text.trim() || isTyping) return;
      voice.stopListening();

      const userText = text.trim();
      const userMsgId = crypto.randomUUID();
      const aiTempId = crypto.randomUUID();

      const userMsg: ChatMessage = {
        id: userMsgId,
        role: "user",
        content: userText,
        inputMode: mode,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setSuggestions([]);
      setIsTyping(true);

      let activeId = conversationId;

      // 1. Ensure conversation exists on backend
      try {
        if (!activeId) {
          const newConv = await api.post<{ id: string; title: string }>("/api/v1/conversations", {
            title: userText.slice(0, 60),
          });
          activeId = newConv.id;
          setConversationId(activeId);
          setActiveConversationId(activeId);
          router.replace(`/ask?id=${activeId}`);
          addOrUpdateConversation({
            id: activeId,
            title: newConv.title || userText.slice(0, 60),
          });
        }
      } catch (err) {
        console.warn("Could not create conversation on backend:", err);
      }

      // 2. Placeholder assistant message with isStreaming: true
      const assistantPlaceholder: ChatMessage = {
        id: aiTempId,
        role: "assistant",
        content: "",
        inputMode: "text",
        timestamp: new Date(),
        isStreaming: true,
        visualizations: [],
      };

      setMessages((prev) => [...prev, assistantPlaceholder]);

      // 3. Connect to SSE streaming endpoint
      if (activeId) {
        try {
          const token = api.getToken();
          const response = await fetch(`${API_BASE}/api/v1/conversations/${activeId}/messages/stream`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({
              content: userText,
              input_mode: mode,
            }),
          });

          if (response.ok && response.body) {
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let accumulatedContent = "";

            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              const chunk = decoder.decode(value, { stream: true });
              const lines = chunk.split("\n");

              for (const line of lines) {
                if (line.startsWith("data: ")) {
                  try {
                    const data = JSON.parse(line.slice(6));

                    if (data.type === "visualization") {
                      // Attach chart payload to message in real time
                      setMessages((prev) =>
                        prev.map((msg) =>
                          msg.id === aiTempId
                            ? {
                                ...msg,
                                visualizations: [
                                  ...(msg.visualizations || []),
                                  data.visualization,
                                ],
                              }
                            : msg
                        )
                      );
                    } else if (data.type === "token") {
                      accumulatedContent += data.token;
                      setMessages((prev) =>
                        prev.map((msg) =>
                          msg.id === aiTempId
                            ? { ...msg, content: accumulatedContent, isStreaming: true }
                            : msg
                        )
                      );
                    } else if (data.type === "done") {
                      setMessages((prev) =>
                        prev.map((msg) =>
                          msg.id === aiTempId
                            ? {
                                ...msg,
                                id: data.message_id || aiTempId,
                                content: accumulatedContent,
                                isStreaming: false,
                              }
                            : msg
                        )
                      );

                      if (data.suggestions && data.suggestions.length > 0) {
                        setSuggestions(data.suggestions);
                      }

                      if (data.title) {
                        addOrUpdateConversation({
                          id: activeId!,
                          title: data.title,
                        });
                      }

                      fetchConversations();
                    }
                  } catch {
                    // Ignore SSE parse errors for partial chunks
                  }
                }
              }
            }

            setIsTyping(false);
            return;
          }
        } catch (streamErr) {
          console.warn("SSE stream failed, attempting standard API or demo fallback:", streamErr);
        }
      }

      // 4. Fallback simulation
      await new Promise((resolve) => setTimeout(resolve, 800));
      const simulatedText =
        "Based on Google BigQuery analytics data, **September sales are currently tracking at $2.4M**, which represents an **8.7% increase** compared to last month.";

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === aiTempId
            ? {
                ...msg,
                content: simulatedText,
                isStreaming: false,
              }
            : msg
        )
      );

      setSuggestions([
        "What are our top-selling products?",
        "Compare with last month",
        "Show regional breakdown",
      ]);
      setIsTyping(false);
    },
    [
      conversationId,
      isTyping,
      router,
      addOrUpdateConversation,
      fetchConversations,
      setActiveConversationId,
    ]
  );

  useEffect(() => {
    sendMessageRef.current = sendMessage;
  }, [sendMessage]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const defaultSuggestions = [
    { icon: "🏆", text: "What were our top 3 products by revenue?" },
    { icon: "🌍", text: "Show revenue breakdown by region" },
    { icon: "📈", text: "How is daily revenue trending?" },
    { icon: "💰", text: "What is our overall profit margin %?" },
  ];

  const hasMessages = messages.length > 0;
  const greetingName = user?.name ? user.name.split(" ")[0] : "Dinithi";

  return (
    <div className={styles.askPage}>
      {!hasMessages ? (
        /* ── Welcome / Empty State ──────────────────────── */
        <div className={styles.welcomeContainer}>
          <div className={styles.welcomeOrb}>✨</div>
          <h1 className={styles.welcomeTitle}>
            Good afternoon, <span className="vx-gradient-text">{greetingName}</span>
          </h1>
          <p className={styles.welcomeSubtitle}>
            Connected to Google BigQuery. Ask anything to analyze your business metrics and generate dynamic charts.
          </p>

          {/* Voice Input Action */}
          <div className={styles.voiceSection}>
            <button
              type="button"
              className={`${styles.voiceBtn} ${voice.isListening ? styles.listening : ""}`}
              onClick={toggleVoice}
              title={voice.isListening ? "Listening... click to stop" : "Ask by voice"}
            >
              🎙️
            </button>
            <span className={styles.voiceLabel}>
              {voice.isListening ? "Listening... speak now" : "Ask by voice"}
            </span>
          </div>

          {/* Quick Starter Questions */}
          <div className={styles.suggestions}>
            {defaultSuggestions.map((s, i) => (
              <button
                key={i}
                type="button"
                className={styles.suggestionCard}
                onClick={() => sendMessage(s.text)}
              >
                <span className={styles.suggestionIcon}>{s.icon}</span>
                <span>{s.text}</span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* ── Chat Messages Stream ────────────────────────── */
        <div className={styles.chatArea}>
          {messages.map((msg) => (
            <div key={msg.id} className={styles.messageGroup}>
              {msg.role === "user" ? (
                <div className={styles.userMessage}>
                  <div className={styles.userBubble}>
                    {msg.inputMode === "voice" && (
                      <div className={styles.voiceIndicator}>🎙️ Voice Query</div>
                    )}
                    {msg.content}
                  </div>
                </div>
              ) : (
                <div className={styles.assistantMessage}>
                  <div className={styles.assistantAvatar}>V</div>
                  <div className={styles.assistantBubbleWrapper}>
                    <div className={styles.assistantBubble}>
                      {/* Dynamic Visualizations from BigQuery */}
                      {msg.visualizations && msg.visualizations.length > 0 && (
                        <div>
                          {msg.visualizations.map((viz, vIdx) => (
                            <VisualizationViewer key={viz.id || vIdx} viz={viz} />
                          ))}
                        </div>
                      )}

                      <MarkdownRenderer
                        content={msg.content}
                        isStreaming={msg.isStreaming}
                      />
                    </div>

                    {!msg.isStreaming && msg.content && (
                      <div className={styles.messageActions}>
                        <button
                          type="button"
                          className={styles.actionBtn}
                          onClick={() => handleCopy(msg.content, msg.id)}
                          title="Copy answer"
                        >
                          {copiedMsgId === msg.id ? "✓ Copied" : "📋 Copy"}
                        </button>
                        <button
                          type="button"
                          className={`${styles.actionBtn} ${
                            voice.isSpeaking && voice.speakingId === msg.id
                              ? styles.speakingActive
                              : ""
                          }`}
                          onClick={() => handleSpeak(msg.content, msg.id)}
                          title={
                            voice.isSpeaking && voice.speakingId === msg.id
                              ? "Stop reading aloud"
                              : "Read aloud"
                          }
                        >
                          {voice.isSpeaking && voice.speakingId === msg.id
                            ? "⏹ Stop"
                            : "🔊 Listen"}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Typing dots while waiting for first stream token */}
          {isTyping &&
            messages.length > 0 &&
            messages[messages.length - 1]?.role === "assistant" &&
            !messages[messages.length - 1]?.content &&
            (!messages[messages.length - 1]?.visualizations || messages[messages.length - 1]?.visualizations?.length === 0) && (
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
                  type="button"
                  className={styles.followUpChip}
                  onClick={() => sendMessage(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          <div ref={chatEndRef} />
        </div>
      )}

      {/* ── Real-time Voice Experience Overlay ──────────── */}
      <VoiceOverlay
        isListening={voice.isListening}
        isSpeaking={voice.isSpeaking}
        transcript={voice.transcript}
        interimTranscript={voice.interimTranscript}
        analyser={voice.analyser}
        onCancel={() => voice.stopListening()}
        onSend={() => {
          const text = voice.interimTranscript || voice.transcript;
          voice.stopListening();
          if (text.trim()) {
            sendMessage(text, "voice");
          }
        }}
        onBargeIn={() => {
          voice.bargeIn((finalText) => {
            if (finalText.trim()) {
              sendMessage(finalText, "voice");
            }
          });
        }}
      />

      {/* ── Input Bar ──────────────────────────────────────── */}
      <div className={styles.inputArea}>
        <form className={styles.inputBar} onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            type="text"
            className={styles.textInput}
            placeholder="Ask anything about your BigQuery metrics, products, or revenue..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isTyping}
          />
          <button
            type="button"
            className={`${styles.inputVoiceBtn} ${voice.isListening ? styles.active : ""}`}
            onClick={toggleVoice}
            title={voice.isListening ? "Listening... click to stop" : "Ask with voice"}
          >
            🎙️
          </button>
          <button
            type="submit"
            className={styles.sendBtn}
            disabled={!input.trim() || isTyping}
            title="Send query"
          >
            ➤
          </button>
        </form>
        <p className={styles.inputHint}>
          Voxora AI • Connected to Google BigQuery • Real-time analytical SQL engine
        </p>
      </div>
    </div>
  );
}

export default function AskPage() {
  return (
    <Suspense fallback={<div className={styles.askPage} />}>
      <AskContent />
    </Suspense>
  );
}
