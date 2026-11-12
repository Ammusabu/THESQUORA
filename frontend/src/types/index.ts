export interface User {
  id: string;
  name: string;
  email: string;
  role: "admin" | "user";
  department: string | null;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface DocumentItem {
  id: string;
  title: string;
  filename: string;
  file_type: "pdf" | "docx" | "txt";
  owner_id: string;
  department: string | null;
  category: string | null;
  classification_confidence: number | null;
  upload_date: string;
  processing_status: "pending" | "processing" | "processed" | "failed";
  total_chunks: number;
  file_size: number;
  summary: string | null;
  error: string | null;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
  page: number;
  limit: number;
}
