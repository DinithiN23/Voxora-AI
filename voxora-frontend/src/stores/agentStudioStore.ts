/**
 * Voxora Agent Studio Store (Zustand)
 *
 * Manages active agent configuration, preset templates, unsaved drafts,
 * interactive sandbox test sessions, and voice previews.
 */

import { create } from "zustand";
import { api, ApiError } from "@/lib/api";
import type { AgentConfig, AgentPreset, AgentTestResponse, GlossaryItem } from "@/types/api";

export interface SandboxChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  latency_ms?: number;
  timestamp: string;
}

interface AgentStudioState {
  config: AgentConfig | null;
  draft: AgentConfig | null;
  presets: AgentPreset[];
  isLoading: boolean;
  isSaving: boolean;
  isTesting: boolean;
  isPlayingVoice: boolean;
  isDirty: boolean;
  statusMessage: { type: "success" | "error" | "info"; text: string } | null;
  activeTab: "persona" | "voice" | "prompt" | "glossary" | "data" | "sandbox";
  sandboxMessages: SandboxChatMessage[];

  // Actions
  fetchAgentConfig: () => Promise<void>;
  fetchPresets: () => Promise<void>;
  setActiveTab: (tab: "persona" | "voice" | "prompt" | "glossary" | "data" | "sandbox") => void;
  updateDraft: (changes: Partial<AgentConfig>) => void;
  addGlossaryItem: (item: GlossaryItem) => void;
  removeGlossaryItem: (index: number) => void;
  updateGlossaryItem: (index: number, item: GlossaryItem) => void;
  applyPreset: (presetId: string) => void;
  saveConfig: () => Promise<void>;
  resetToFactoryDefault: () => Promise<void>;
  discardChanges: () => void;
  runSandboxTest: (question: string) => Promise<void>;
  clearSandboxChat: () => void;
  previewVoice: (sampleText?: string) => Promise<void>;
  clearStatusMessage: () => void;
}

export const useAgentStudioStore = create<AgentStudioState>((set, get) => ({
  config: null,
  draft: null,
  presets: [],
  isLoading: false,
  isSaving: false,
  isTesting: false,
  isPlayingVoice: false,
  isDirty: false,
  statusMessage: null,
  activeTab: "persona",
  sandboxMessages: [
    {
      id: "initial-assistant-greeting",
      role: "assistant",
      content: "Greetings! I am your Voxora Executive Copilot running in the Agent Studio Test Bench. Ask me any analytical, financial, or business question to evaluate my persona and tone.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ],

  fetchAgentConfig: async () => {
    set({ isLoading: true });
    try {
      const config = await api.get<AgentConfig>("/api/v1/studio/agent");
      set({
        config,
        draft: JSON.parse(JSON.stringify(config)),
        isDirty: false,
        isLoading: false,
      });
    } catch (err) {
      console.error("Failed to load agent configuration:", err);
      set({
        isLoading: false,
        statusMessage: { type: "error", text: "Failed to load agent configuration." },
      });
    }
  },

  fetchPresets: async () => {
    try {
      const presets = await api.get<AgentPreset[]>("/api/v1/studio/presets");
      set({ presets });
    } catch (err) {
      console.warn("Failed to load presets:", err);
    }
  },

  setActiveTab: (tab) => set({ activeTab: tab }),

  updateDraft: (changes) => {
    const { draft, config } = get();
    if (!draft) return;

    const newDraft = { ...draft, ...changes };
    const isDirty = JSON.stringify(newDraft) !== JSON.stringify(config);
    set({ draft: newDraft, isDirty });
  },

  addGlossaryItem: (item) => {
    const { draft } = get();
    if (!draft) return;
    const updated = [...(draft.knowledge_glossary || []), item];
    get().updateDraft({ knowledge_glossary: updated });
  },

  removeGlossaryItem: (index) => {
    const { draft } = get();
    if (!draft) return;
    const updated = [...(draft.knowledge_glossary || [])];
    updated.splice(index, 1);
    get().updateDraft({ knowledge_glossary: updated });
  },

  updateGlossaryItem: (index, item) => {
    const { draft } = get();
    if (!draft) return;
    const updated = [...(draft.knowledge_glossary || [])];
    updated[index] = item;
    get().updateDraft({ knowledge_glossary: updated });
  },

  applyPreset: (presetId) => {
    const { presets, draft } = get();
    const preset = presets.find((p) => p.id === presetId);
    if (!preset || !draft) return;

    const newDraft: AgentConfig = {
      ...draft,
      name: preset.name,
      avatar: preset.avatar,
      role_title: preset.role_title,
      description: preset.description,
      tone: preset.tone,
      temperature: preset.temperature,
      system_prompt: preset.system_prompt,
      greeting_message: preset.greeting_message,
      fallback_message: preset.fallback_message,
      voice_id: preset.voice_id,
      voice_speed: preset.voice_speed,
      voice_pitch: preset.voice_pitch,
      allowed_data_areas: preset.allowed_data_areas,
      data_access_rules: preset.data_access_rules,
      knowledge_glossary: JSON.parse(JSON.stringify(preset.knowledge_glossary)),
    };

    set({
      draft: newDraft,
      isDirty: true,
      statusMessage: {
        type: "info",
        text: `Loaded '${preset.name}' template into draft. Review and click 'Save & Publish' to activate.`,
      },
    });
  },

  discardChanges: () => {
    const { config } = get();
    if (!config) return;
    set({
      draft: JSON.parse(JSON.stringify(config)),
      isDirty: false,
      statusMessage: { type: "info", text: "Draft changes discarded." },
    });
  },

  saveConfig: async () => {
    const { draft } = get();
    if (!draft) return;

    set({ isSaving: true });
    try {
      const updated = await api.put<AgentConfig>("/api/v1/studio/agent", draft);
      set({
        config: updated,
        draft: JSON.parse(JSON.stringify(updated)),
        isDirty: false,
        isSaving: false,
        statusMessage: {
          type: "success",
          text: `Successfully published '${updated.name}' configuration across Voxora AI!`,
        },
      });
    } catch (err) {
      console.error("Save error:", err);
      const isAuthErr = err instanceof ApiError && err.status === 401;
      set({
        isSaving: false,
        statusMessage: {
          type: "error",
          text: isAuthErr
            ? "Sign in with admin@voxora.ai to publish agent configuration changes."
            : err instanceof Error ? err.message : "Failed to save agent configuration.",
        },
      });
    }
  },

  resetToFactoryDefault: async () => {
    set({ isSaving: true });
    try {
      const resetConfig = await api.post<AgentConfig>("/api/v1/studio/agent/reset", {});
      set({
        config: resetConfig,
        draft: JSON.parse(JSON.stringify(resetConfig)),
        isDirty: false,
        isSaving: false,
        statusMessage: {
          type: "info",
          text: "Agent configuration reset to factory defaults.",
        },
      });
    } catch (err) {
      console.error("Reset error:", err);
      const isAuthErr = err instanceof ApiError && err.status === 401;
      set({
        isSaving: false,
        statusMessage: {
          type: "error",
          text: isAuthErr
            ? "Sign in with admin@voxora.ai to reset agent configuration."
            : "Failed to reset agent configuration.",
        },
      });
    }
  },

  runSandboxTest: async (question: string) => {
    const { draft, sandboxMessages } = get();
    if (!question.trim()) return;

    const userMsg: SandboxChatMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: question.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    set({
      sandboxMessages: [...sandboxMessages, userMsg],
      isTesting: true,
    });

    try {
      const testPayload = {
        question: question.trim(),
        system_prompt: draft?.system_prompt,
        tone: draft?.tone,
        temperature: draft?.temperature,
        knowledge_glossary: draft?.knowledge_glossary,
      };

      const result = await api.post<AgentTestResponse>("/api/v1/studio/test", testPayload);

      const assistantMsg: SandboxChatMessage = {
        id: `msg-resp-${Date.now()}`,
        role: "assistant",
        content: result.response,
        latency_ms: result.latency_ms,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      set((state) => ({
        sandboxMessages: [...state.sandboxMessages, assistantMsg],
        isTesting: false,
      }));
    } catch (err) {
      console.error("Sandbox test error:", err);
      const errorMsg: SandboxChatMessage = {
        id: `msg-err-${Date.now()}`,
        role: "assistant",
        content: `Sandbox response error: ${err instanceof Error ? err.message : "Unknown test bench error"}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      set((state) => ({
        sandboxMessages: [...state.sandboxMessages, errorMsg],
        isTesting: false,
      }));
    }
  },

  clearSandboxChat: () => {
    set({
      sandboxMessages: [
        {
          id: `msg-clear-${Date.now()}`,
          role: "assistant",
          content: "Sandbox session refreshed. Ready for custom query evaluation.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ],
    });
  },

  previewVoice: async (sampleText) => {
    const { draft } = get();
    if (!draft) return;

    const textToSpeak =
      sampleText ||
      draft.greeting_message ||
      `Good day. I am ${draft.name}, your ${draft.role_title}.`;

    set({ isPlayingVoice: true });

    try {
      // Attempt backend synthesis
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiBase}/api/v1/studio/voice-preview`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("voxora_access_token") || ""}`,
        },
        body: JSON.stringify({
          text: textToSpeak,
          voice_id: draft.voice_id,
          speed: draft.voice_speed,
          pitch: draft.voice_pitch,
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);
        audio.onended = () => {
          set({ isPlayingVoice: false });
          URL.revokeObjectURL(audioUrl);
        };
        audio.onerror = () => set({ isPlayingVoice: false });
        await audio.play();
        return;
      }
    } catch (e) {
      // Backend synthesis fallback
      set({ statusMessage: { type: "info", text: "Backend voice synthesis unavailable. Falling back to browser speech." } });
    }

    // Client-side Web Speech API fallback
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(textToSpeak);
      utterance.rate = draft.voice_speed || 1.0;
      utterance.pitch = Math.max(0.5, Math.min(2.0, 1.0 + (draft.voice_pitch || 0) / 10));
      utterance.onend = () => set({ isPlayingVoice: false });
      utterance.onerror = () => set({ isPlayingVoice: false });
      window.speechSynthesis.speak(utterance);
    } else {
      set({ isPlayingVoice: false });
    }
  },

  clearStatusMessage: () => set({ statusMessage: null }),
}));
