/* TypeScript types for the Voxora API */

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  tenant_id: string;
  tenant_name: string;
  role: string | null;
  is_active: boolean;
  last_login: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthResponse {
  tokens: TokenResponse;
  user: User;
}

export interface Visualization {
  id: string;
  chart_type: "bar" | "line" | "pie" | "table" | "kpi" | "map";
  chart_config: Record<string, unknown>;
  data_payload: Record<string, unknown>;
  title: string | null;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  input_mode: "text" | "voice";
  intent: Record<string, unknown> | null;
  entities: Record<string, unknown> | null;
  visualizations: Visualization[];
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string | null;
  status: "active" | "archived";
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail {
  id: string;
  title: string | null;
  status: "active" | "archived";
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface AskResponse {
  message: Message;
  suggestions: string[];
  voice_url: string | null;
}

export interface GlossaryItem {
  term: string;
  definition: string;
}

export interface AgentConfig {
  id: string;
  tenant_id: string;
  name: string;
  avatar: string;
  role_title: string;
  description: string;
  tone: "executive" | "analytical" | "strategic" | "technical" | string;
  temperature: number;
  system_prompt: string;
  greeting_message: string;
  fallback_message: string;
  voice_id: string;
  voice_speed: number;
  voice_pitch: number;
  allowed_data_areas: string[];
  data_access_rules: {
    mask_pii?: boolean;
    read_only?: boolean;
    auto_visualize?: boolean;
    allow_sql_generation?: boolean;
    [key: string]: unknown;
  };
  knowledge_glossary: GlossaryItem[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgentPreset {
  id: string;
  name: string;
  avatar: string;
  role_title: string;
  description: string;
  tone: string;
  temperature: number;
  system_prompt: string;
  greeting_message: string;
  fallback_message: string;
  voice_id: string;
  voice_speed: number;
  voice_pitch: number;
  allowed_data_areas: string[];
  data_access_rules: Record<string, unknown>;
  knowledge_glossary: GlossaryItem[];
}

export interface AgentTestResponse {
  response: string;
  persona_applied: string;
  tone_applied: string;
  model_used: string;
  latency_ms: number;
}

