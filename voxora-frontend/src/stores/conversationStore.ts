/**
 * Voxora Conversation Store (Zustand)
 *
 * Manages conversation list, active thread, deletion, and title updates.
 */

import { create } from "zustand";
import { api } from "@/lib/api";
import type { Conversation } from "@/types/api";

interface ConversationState {
  conversations: Conversation[];
  activeConversationId: string | null;
  isLoading: boolean;
  error: string | null;

  fetchConversations: () => Promise<void>;
  setActiveConversationId: (id: string | null) => void;
  deleteConversation: (id: string) => Promise<void>;
  addOrUpdateConversation: (conv: Partial<Conversation> & { id: string }) => void;
  clearConversations: () => void;
}

export const useConversationStore = create<ConversationState>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  isLoading: false,
  error: null,

  fetchConversations: async () => {
    // Only fetch if token is available
    const token = typeof window !== "undefined" ? localStorage.getItem("voxora_access_token") : null;
    if (!token) return;

    set({ isLoading: true, error: null });
    try {
      const data = await api.get<Conversation[]>("/api/v1/conversations");
      set({ conversations: data, isLoading: false });
    } catch (err) {
      console.warn("Failed to fetch conversations:", err);
      set({ isLoading: false, error: err instanceof Error ? err.message : "Failed to load history" });
    }
  },

  setActiveConversationId: (id: string | null) => {
    set({ activeConversationId: id });
  },

  deleteConversation: async (id: string) => {
    // Optimistic delete from UI
    const previous = get().conversations;
    set({
      conversations: previous.filter((c) => c.id !== id),
      activeConversationId: get().activeConversationId === id ? null : get().activeConversationId,
    });

    try {
      await api.delete(`/api/v1/conversations/${id}`);
    } catch (err) {
      console.error("Failed to archive conversation:", err);
      // Rollback on failure
      set({ conversations: previous });
    }
  },

  addOrUpdateConversation: (conv) => {
    set((state) => {
      const index = state.conversations.findIndex((c) => c.id === conv.id);
      if (index >= 0) {
        const updated = [...state.conversations];
        updated[index] = { ...updated[index], ...conv } as Conversation;
        // Move updated to top
        const item = updated.splice(index, 1)[0];
        return { conversations: [item, ...updated] };
      } else {
        const newConv: Conversation = {
          id: conv.id,
          title: conv.title || "New Conversation",
          status: "active",
          message_count: conv.message_count || 1,
          created_at: conv.created_at || new Date().toISOString(),
          updated_at: conv.updated_at || new Date().toISOString(),
        };
        return { conversations: [newConv, ...state.conversations] };
      }
    });
  },

  clearConversations: () => {
    set({ conversations: [], activeConversationId: null });
  },
}));
