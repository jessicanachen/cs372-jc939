export type Role = "user" | "assistant";

export interface Message {
    id: number;
    role: Role;
    content: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}