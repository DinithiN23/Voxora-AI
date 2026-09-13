"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useConversationStore } from "@/stores/conversationStore";
import { useAuthStore } from "@/stores/authStore";
import MarkdownRenderer from "@/components/chat/MarkdownRenderer";
import VisualizationViewer from "@/components/visualizations/VisualizationViewer";
import { useVoice } from "@/hooks/useVoice";
import type { ConversationDetail, Visualization } from "@/types/api";
import styles from "@/app/(app)/ask/ask.module.css";

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

interface UniversalChatProps {
  initialConversationId?: string | null;
  isWidget?: boolean;
}

export default function UniversalChat({ initialConversationId = null, isWidget = false }: UniversalChatProps) {
  const router = useRouter();

  const { addOrUpdateConversation, fetchConversations, setActiveConversationId } =
    useConversationStore();
  const { user } = useAuthStore();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(initialConversationId);
  const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const sendMessageRef = useRef<(text: string, mode?: "text" | "voice") => Promise<void>>(
    async () => {}
  );

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

  useEffect(() => {
    const ensureAuth = async () => {
      const token = api.getToken();
      if (!token) {
        try {
          await useAuthStore.getState().login("admin@voxora.ai", "Admin@123");
        } catch {}
      }
    };
    ensureAuth();
  }, []);

  useEffect(() => {
    if (initialConversationId !== undefined) {
      setConversationId(initialConversationId);
      setActiveConversationId(initialConversationId);
    }
  }, [initialConversationId, setActiveConversationId]);

  useEffect(() => {
    if (!conversationId) {
      setMessages([]);
      setSuggestions([]);
      return;
    }

    let isMounted = true;
    const loadConversation = async () => {
      try {
        const detail = await api.get<ConversationDetail>(`/api/v1/conversations/${conversationId}`);
        if (!isMounted) return;

        const loadedMessages: ChatMessage[] = (detail.messages || []).map((m) => ({
          id: m.id,
          role: m.role as "user" | "assistant",
          content: m.content,
          inputMode: m.input_mode || "text",
          timestamp: new Date(m.created_at),
          visualizations: m.visualizations || [],
        }));

        // Do not overwrite local optimistic state if a message is currently streaming
        setMessages((prev) => {
          const isStreaming = prev.some((m) => m.isStreaming);
          return isStreaming ? prev : loadedMessages;
        });

        const lastMsg = loadedMessages[loadedMessages.length - 1];
        if (lastMsg && lastMsg.role === "assistant") {
          setSuggestions((prev) => prev.length > 0 ? prev : [
            "Break this down further",
            "What is driving this change?",
            "Show regional breakdown",
          ]);
        } else {
           setSuggestions([]);
        }
      } catch (err) {
        console.warn("Failed to load conversation thread:", err);
      }
    };

    loadConversation();
    return () => {
      isMounted = false;
    };
  }, [conversationId]);

  const toggleVoice = useCallback(() => {
    if (!voice.isSupported) {
      alert("Voice recognition is not supported in your browser. Please use text input.");
      return;
    }

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

  useEffect(() => {
    if (voice.error) {
      const errorMsgId = crypto.randomUUID();
      setMessages((prev) => [
        ...prev,
        {
          id: errorMsgId,
          role: "assistant",
          content: `⚠️ **Voice Error:** ${voice.error}`,
          inputMode: "text",
          timestamp: new Date(),
        },
      ]);
    }
  }, [voice.error]);

  useEffect(() => {
    if (voice.isListening && voice.interimTranscript) {
      setInput(voice.interimTranscript);
    }
  }, [voice.isListening, voice.interimTranscript]);

  const handleSpeak = useCallback(
    (text: string, id: string) => {
      voice.speak(text, id);
    },
    [voice]
  );

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMsgId(id);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

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

      try {
        if (!activeId) {
          const newConv = await api.post<{ id: string; title: string }>("/api/v1/conversations", {
            title: userText.slice(0, 60),
          });
          activeId = newConv.id;
          setConversationId(activeId);
          setActiveConversationId(activeId);
          if (!isWidget) {
            router.replace(`/ask?id=${activeId}`);
          }
          addOrUpdateConversation({
            id: activeId,
            title: newConv.title || userText.slice(0, 60),
          });
        }
      } catch (err) {
        console.warn("Could not create conversation, attempting auto-login:", err);
        try {
          await useAuthStore.getState().login("admin@voxora.ai", "Admin@123");
          const retryConv = await api.post<{ id: string; title: string }>("/api/v1/conversations", {
            title: userText.slice(0, 60),
          });
          activeId = retryConv.id;
          setConversationId(activeId);
          setActiveConversationId(activeId);
          if (!isWidget) {
            router.replace(`/ask?id=${activeId}`);
          }
          addOrUpdateConversation({
            id: activeId,
            title: retryConv.title || userText.slice(0, 60),
          });
        } catch (retryErr) {}
      }

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
                      const finalMsgId = data.message_id || aiTempId;
                      setMessages((prev) =>
                        prev.map((msg) =>
                          msg.id === aiTempId
                            ? {
                                ...msg,
                                id: finalMsgId,
                                content: accumulatedContent,
                                isStreaming: false,
                              }
                            : msg
                        )
                      );

                      if (mode === "voice" && accumulatedContent.trim()) {
                        voice.speak(accumulatedContent, finalMsgId);
                      }

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
                  } catch {}
                }
              }
            }

            setIsTyping(false);
            return;
          }
        } catch (streamErr) {}
      }

      await new Promise((resolve) => setTimeout(resolve, 600));

      const answerText = "⚠️ **Connection to analytics engine lost.** Click here to retry.";

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === aiTempId
            ? {
                ...msg,
                content: answerText,
                isStreaming: false,
              }
            : msg
        )
      );

      setSuggestions([]);

      if (mode === "voice" && answerText.trim()) {
        voice.speak(answerText, aiTempId);
      }

      setIsTyping(false);
    },
    [
      conversationId,
      isTyping,
      router,
      addOrUpdateConversation,
      fetchConversations,
      setActiveConversationId,
      voice,
      isWidget,
    ]
  );

  useEffect(() => {
    sendMessageRef.current = sendMessage;
  }, [sendMessage]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : "D";

  return (
    <>
      <div className={styles.chatArea}>
        {messages.length === 0 && (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", opacity: 0.5 }}>
             <p>Send a message or use your voice to begin.</p>
          </div>
        )}
        
        {messages.map((msg) => (
          <div key={msg.id} className={styles.messageGroup}>
            {msg.role === "user" ? (
              <div className={styles.userMessage}>
                <div className={styles.userBubble}>{msg.content}</div>
                <div className={styles.userAvatar} title={user?.name || "User"}>
                  {userInitial}
                </div>
              </div>
            ) : (
              <div className={styles.assistantMessage}>
                <div className={styles.assistantAvatar} title="Voxora AI Assistant">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="11" width="18" height="10" rx="2" />
                    <circle cx="12" cy="5" r="2" />
                    <path d="M12 7v4" />
                    <line x1="8" y1="16" x2="8.01" y2="16" strokeWidth="2.5" />
                    <line x1="16" y1="16" x2="16.01" y2="16" strokeWidth="2.5" />
                  </svg>
                </div>
                <div className={styles.assistantContentRow}>
                  <div className={styles.assistantBubble}>
                    {msg.visualizations && msg.visualizations.length > 0 && (
                      <div>
                        {msg.visualizations.map((viz, vIdx) => (
                          <VisualizationViewer key={viz.id || vIdx} viz={viz} />
                        ))}
                      </div>
                    )}
                    <MarkdownRenderer content={msg.content} isStreaming={msg.isStreaming} />
                  </div>
                  {!msg.isStreaming && msg.content && (
                    <div className={styles.assistantControlsCol}>
                      <button
                        type="button"
                        className={`${styles.ctrlBtn} ${voice.isSpeaking && voice.speakingId === msg.id ? styles.speakingActive : ""}`}
                        onClick={() => handleSpeak(msg.content, msg.id)}
                        title={voice.isSpeaking && voice.speakingId === msg.id ? "Stop speaking" : "Read answer aloud"}
                      >
                        {voice.isSpeaking && voice.speakingId === msg.id ? (
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
                          </svg>
                        ) : (
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                            <line x1="23" y1="9" x2="17" y2="15" />
                            <line x1="17" y1="9" x2="23" y2="15" />
                          </svg>
                        )}
                      </button>
                      <button type="button" className={styles.ctrlBtn} onClick={() => handleCopy(msg.content, msg.id)} title="Copy answer">
                        {copiedMsgId === msg.id ? (
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="20 6 9 17 4 12" />
                          </svg>
                        ) : (
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                          </svg>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
        {isTyping && messages.length > 0 && messages[messages.length - 1]?.role === "assistant" && !messages[messages.length - 1]?.content && (!messages[messages.length - 1]?.visualizations || messages[messages.length - 1]?.visualizations?.length === 0) && (
          <div className={styles.typingIndicator}>
            <div className={styles.assistantAvatar}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="10" rx="2" />
                <circle cx="12" cy="5" r="2" />
                <path d="M12 7v4" />
                <line x1="8" y1="16" x2="8.01" y2="16" strokeWidth="2.5" />
                <line x1="16" y1="16" x2="16.01" y2="16" strokeWidth="2.5" />
              </svg>
            </div>
            <div className={styles.typingDots}>
              <div className={styles.typingDot} />
              <div className={styles.typingDot} />
              <div className={styles.typingDot} />
            </div>
          </div>
        )}
        {suggestions.length > 0 && !isTyping && (
          <div className={styles.followUpSuggestions}>
            {suggestions.map((s, i) => (
              <button key={i} type="button" className={styles.followUpChip} onClick={() => sendMessage(s)}>
                {s}
              </button>
            ))}
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <div className={styles.inputArea}>
        {voice.isListening ? (
          <div className={styles.activeListeningBar}>
            <button type="button" className={styles.activeListeningMicBtn} onClick={toggleVoice} title="Listening... Click to stop">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            </button>
            <div className={styles.activeListeningContent}>
              <div className={styles.activeListeningBadge}>
                <span className={styles.pulseRedDot} />
                <span>LIVE RECOGNITION</span>
              </div>
              <div className={styles.activeListeningText}>
                {voice.interimTranscript || voice.transcript ? (
                  <>
                    <span>{voice.interimTranscript || voice.transcript}</span>
                    <span className={styles.blinkingCaret}>|</span>
                  </>
                ) : (
                  <span className={styles.listeningPlaceholder}>Listening... Speak your question naturally</span>
                )}
              </div>
            </div>
            <div className={styles.activeListeningControls}>
              <button type="button" className={styles.cancelListeningBtn} onClick={() => voice.stopListening()} title="Cancel voice input">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          </div>
        ) : (
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
            <button type="button" className={styles.inputVoiceBtn} onClick={toggleVoice} title="Ask with voice">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
            </button>
            <button type="submit" className={styles.sendBtn} disabled={!input.trim() || isTyping} title="Send query">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </form>
        )}
        <p className={styles.inputHint}>
          Voxora AI • Connected to Google BigQuery • Real-time analytical SQL engine
        </p>
      </div>
    </>
  );
}
