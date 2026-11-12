import { api } from "./client";

export interface SourceRef {
  document_id: string;
  title: string;
  page_number: number | null;
  chunk_index: number | null;
  snippet: string | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  user_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  source_references: SourceRef[];
  created_at: string;
  feedback?: "up" | "down" | null;
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export async function ask(question: string, conversationId?: string) {
  const res = await api.post("/api/chat", {
    question,
    conversation_id: conversationId,
  });
  return res.data as {
    conversation_id: string;
    message: Message;
    context_used: number;
    model: string | null;
  };
}

export async function listConversations(page = 1, limit = 20) {
  const res = await api.get("/api/chat/conversations", { params: { page, limit } });
  return res.data as {
    items: Conversation[];
    total: number;
    page: number;
    limit: number;
  };
}

export async function getConversation(id: string) {
  const res = await api.get(`/api/chat/conversations/${id}`);
  return res.data as { conversation: Conversation; messages: Message[] };
}

export async function deleteConversation(id: string) {
  await api.delete(`/api/chat/conversations/${id}`);
}


export async function rateMessage(messageId: string, rating: "up" | "down" | null): Promise<void> {
  await api.post(`/api/chat/messages/${messageId}/feedback`, { rating });
}
