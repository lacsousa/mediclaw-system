export interface ApiResponse<T> {
  data: T | null;
  error: { code: string; message: string } | null;
  meta: { total?: number; page?: number } | null;
}

export interface User {
  id: number;
  email: string;
  first_name: string;
  accepted_terms_at: string | null;
  role: "USER" | "ADMIN";
}

export interface Patient {
  id: number;
  first_name: string;
  birth_date: string | null;
  biological_sex: "M" | "F" | "OTHER" | null;
  height_cm: number | null;
  conversation_count: number;
  last_seen_at: string | null;
  latest_weight_kg: number | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationSummary {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface PatientDetail extends Patient {
  weight_logs: WeightLog[];
  sleep_logs: SleepLog[];
  activity_logs: ActivityLog[];
  nutrition_notes: NutritionNote[];
  conversations: ConversationSummary[];
}

export interface Conversation {
  id: number;
  title: string;
  patient: { id: number; first_name: string } | null;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  source: string;
  chunk_id: string;
}

export interface Message {
  id: number;
  role: "USER" | "ASSISTANT" | "SYSTEM";
  content: string;
  tokens_used: number | null;
  blocked_by_guardrail: boolean;
  metadata: { citations?: Citation[] };
  created_at: string;
}

export interface KnowledgeDocument {
  id: number;
  title: string;
  status: "PROCESSING" | "INDEXED" | "ERROR";
  chunk_count: number | null;
  created_at: string;
}

export interface AdminMetrics {
  users_total: number;
  conversations_total: number;
  messages_today: number;
  tokens_today: number;
  guardrail_blocks_today: number;
  kb_documents_indexed: number;
}

export interface WeightLog {
  id: number;
  value_kg: number;
  measured_at: string;
}

export interface SleepLog {
  id: number;
  duration_hours: number;
  quality_score: number;
  started_at: string;
}

export interface ActivityLog {
  id: number;
  type: string;
  duration_min: number;
  performed_at: string;
}

export interface NutritionNote {
  id: number;
  note: string;
  logged_at: string;
}
