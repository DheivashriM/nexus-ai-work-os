import { User, Team, Project, Task, Blocker, Activity, Notification, Meeting, EmailItem, Channel, ChatMessage, WhatsAppAccount, WhatsAppConversation, WhatsAppMessage } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function fetcher<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const authHeaders: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...authHeaders,
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    if (res.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    }
    const errorData = await res.json().catch(() => ({ detail: "Network request failed" }));
    throw new Error(errorData.detail || `HTTP Error ${res.status}`);
  }

  if (res.status === 204) {
    return {} as T;
  }

  return res.json();
}


export interface AIChatResponse {
  conversation_id: string;
  reply: string;
  execution_steps: Array<{
    step_number: number;
    tool_name: string;
    description: string;
    status: string;
    arguments?: Record<string, any>;
    result?: Record<string, any>;
  }>;
  actions_taken: string[];
}

export interface AIConversation {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Array<{
    id: string;
    conversation_id: string;
    role: string;
    content: string;
    tool_calls?: any;
    created_at: string;
  }>;
}

export const api = {
  // Users
  getUsers: () => fetcher<User[]>("/users"),
  getMe: () => fetcher<User>("/users/me"),
  getUserById: (id: string) => fetcher<User>(`/users/${id}`),
  createUser: (data: Partial<User> & { password?: string }) =>
    fetcher<User>("/users", { method: "POST", body: JSON.stringify(data) }),
  updateMySettings: (data: Partial<User>) =>
    fetcher<User>("/users/me/settings", { method: "PUT", body: JSON.stringify(data) }),
  getMyEmailSettings: () => fetcher<EmailSettings>("/users/me/email-settings"),
  saveMyEmailSettings: (data: EmailSettingsUpdate) => fetcher<EmailSettings>("/users/me/email-settings", { method: "PUT", body: JSON.stringify(data) }),
  testMyEmailSettings: () => fetcher<EmailSettings>("/users/me/email-settings/test", { method: "POST" }),

  // Teams
  getTeams: () => fetcher<Team[]>("/teams"),
  getTeamById: (id: string) => fetcher<Team>(`/teams/${id}`),
  createTeam: (data: { name: string; description?: string }) =>
    fetcher<Team>("/teams", { method: "POST", body: JSON.stringify(data) }),

  // Projects
  getProjects: (status?: string) =>
    fetcher<Project[]>(`/projects${status ? `?status=${status}` : ""}`),
  getProjectById: (id: string) => fetcher<Project>(`/projects/${id}`),
  createProject: (data: Partial<Project>) =>
    fetcher<Project>("/projects", { method: "POST", body: JSON.stringify(data) }),
  updateProject: (id: string, data: Partial<Project>) =>
    fetcher<Project>(`/projects/${id}`, { method: "PUT", body: JSON.stringify(data) }),

  // Tasks
  getTasks: (params?: { project_id?: string; assignee_id?: string; status?: string; priority?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.project_id) searchParams.append("project_id", params.project_id);
    if (params?.assignee_id) searchParams.append("assignee_id", params.assignee_id);
    if (params?.status) searchParams.append("status", params.status);
    if (params?.priority) searchParams.append("priority", params.priority);
    const query = searchParams.toString();
    return fetcher<Task[]>(`/tasks${query ? `?${query}` : ""}`);
  },
  getTaskById: (id: string) => fetcher<Task>(`/tasks/${id}`),
  createTask: (data: Partial<Task>) =>
    fetcher<Task>("/tasks", { method: "POST", body: JSON.stringify(data) }),
  updateTask: (id: string, data: Partial<Task>) =>
    fetcher<Task>(`/tasks/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  assignTask: (id: string, assignee_id?: string) =>
    fetcher<Task>(`/tasks/${id}/assign`, { method: "POST", body: JSON.stringify({ assignee_id }) }),
  addTaskComment: (taskId: string, content: string) =>
    fetcher<any>(`/tasks/${taskId}/comments`, { method: "POST", body: JSON.stringify({ content }) }),

  // Blockers
  getBlockers: (status?: string) =>
    fetcher<Blocker[]>(`/blockers${status ? `?status=${status}` : ""}`),
  createBlocker: (data: { task_id: string; description: string; severity?: string }) =>
    fetcher<Blocker>("/blockers", { method: "POST", body: JSON.stringify(data) }),
  updateBlocker: (id: string, data: { status?: string; description?: string }) =>
    fetcher<Blocker>(`/blockers/${id}`, { method: "PUT", body: JSON.stringify(data) }),

  // Activities & Notifications
  getActivities: (limit = 50) => fetcher<Activity[]>(`/activities?limit=${limit}`),
  getNotifications: () => fetcher<Notification[]>("/notifications"),
  markNotificationRead: (id: string) => fetcher<Notification>(`/notifications/${id}/read`, { method: "PUT" }),

  // Meetings
  getMeetings: () => fetcher<Meeting[]>("/meetings"),
  scheduleMeeting: (data: { attendee: string; title?: string; date_time?: string; duration_minutes?: number; description?: string }) =>
    fetcher<Meeting>("/meetings/schedule", { method: "POST", body: JSON.stringify(data) }),

  // AI Agent Endpoints
  postAIChat: (message: string, conversation_id?: string) =>
    fetcher<AIChatResponse>("/ai/chat", { method: "POST", body: JSON.stringify({ message, conversation_id }) }),
  getAIConversations: () => fetcher<AIConversation[]>("/ai/conversations"),
  getAIConversationById: (id: string) => fetcher<AIConversation>(`/ai/conversations/${id}`),
  deleteAIConversation: (id: string) => fetcher<void>(`/ai/conversations/${id}`, { method: "DELETE" }),
  getAIActionLogs: () => fetcher<any[]>("/ai/action-logs"),

  // Smart Email Assistant
  getEmails: (urgency?: string) => fetcher<EmailItem[]>(`/emails${urgency ? `?urgency=${urgency}` : ""}`),
  syncGmailInbox: (limit = 10) => fetcher<EmailItem[]>(`/emails/sync-gmail?limit=${limit}`, { method: "POST" }),
  simulateEmail: (data: { sender: string; sender_email: string; subject: string; body: string }) =>
    fetcher<EmailItem>("/emails/simulate", { method: "POST", body: JSON.stringify(data) }),
  sendEmailReply: (emailId: string, reply_body?: string, recipient_email?: string) =>
    fetcher<{ message: string; email_id: string }>(`/emails/${emailId}/reply`, { method: "POST", body: JSON.stringify({ reply_body, recipient_email }) }),
  convertEmailToTask: (emailId: string, projectId: string) =>
    fetcher<{ message: string; task_id: string }>(`/emails/${emailId}/convert-task?project_id=${projectId}`, { method: "POST" }),

  // Health check
  checkHealth: () => fetcher<{ status: string; env: string; database: string; ai_agent?: string }>("/health"),

  // Auth Login & Registration
  loginUser: (email: string, password: string) =>
    fetcher<{ access_token: string; token_type: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  registerUser: (data: { name: string; email: string; password: string }) =>
    fetcher<{ access_token: string; token_type: string; user: User }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Chat & Messaging
  getChannels: () => fetcher<Channel[]>("/chat/channels"),
  createDirectChat: (recipient_id: string) =>
    fetcher<Channel>("/chat/direct", { method: "POST", body: JSON.stringify({ recipient_id }) }),
  createGroupChat: (data: { name: string; description?: string; member_ids: string[] }) =>
    fetcher<Channel>("/chat/group", { method: "POST", body: JSON.stringify(data) }),
  getChannelMessages: (channelId: string, limit = 100) =>
    fetcher<ChatMessage[]>(`/chat/channels/${channelId}/messages?limit=${limit}`),
  sendChatMessage: (channelId: string, content: string, message_type: string = "TEXT") =>
    fetcher<ChatMessage>(`/chat/channels/${channelId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, message_type }),
    }),
  markChannelRead: (channelId: string) =>
    fetcher<void>(`/chat/channels/${channelId}/read`, { method: "POST" }),
  getOnlineUsers: () => fetcher<string[]>("/chat/online-users"),

  // WhatsApp Inbox (Meta Cloud API-backed and separate from internal chat)
  getWhatsAppStatus: () => fetcher<{ configured: boolean; connected: boolean; status: string; accounts: WhatsAppAccount[] }>("/whatsapp/status"),
  getWhatsAppConfig: () => fetcher<{ configured: boolean; phone_number_id?: string; public_api_url?: string; webhook_url?: string }>("/whatsapp/admin/config"),
  saveWhatsAppConfig: (data: { phone_number_id: string; access_token: string; app_secret: string; verify_token: string; public_api_url: string }) => fetcher<{ configured: boolean; phone_number_id?: string; public_api_url?: string; webhook_url?: string }>("/whatsapp/admin/config", { method: "PUT", body: JSON.stringify(data) }),
  getWhatsAppConversations: () => fetcher<WhatsAppConversation[]>("/whatsapp/conversations"),
  getWhatsAppMessages: (conversationId: string) => fetcher<WhatsAppMessage[]>(`/whatsapp/conversations/${conversationId}/messages`),
  sendWhatsAppMessage: (conversationId: string, body: string) => fetcher<WhatsAppMessage>(`/whatsapp/conversations/${conversationId}/messages`, { method: "POST", body: JSON.stringify({ body }) }),
  syncWhatsApp: () => fetcher<{ accounts: number; conversations: number; messages: number }>("/whatsapp/sync", { method: "POST" }),
  configureWhatsAppWebhooks: () => fetcher<{ url: string; verify_token_configured: boolean; subscribe_fields: string[]; note: string }>("/whatsapp/admin/webhooks", { method: "POST" }),

};

export interface EmailSettings {
  configured: boolean;
  enabled: boolean;
  email_address?: string;
  imap_host?: string;
  imap_port?: number;
  smtp_host?: string;
  smtp_port?: number;
}

export interface EmailSettingsUpdate {
  enabled: boolean;
  email_address: string;
  password: string;
  imap_host: string;
  imap_port: number;
  smtp_host: string;
  smtp_port: number;
}


