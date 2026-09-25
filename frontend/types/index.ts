export type UserRole = 'ADMIN' | 'MANAGER' | 'MEMBER';
export type UserStatus = 'ACTIVE' | 'INACTIVE';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  whatsapp_number?: string;
  whatsapp_enabled?: boolean;
  whatsapp_notify_blockers?: boolean;
  whatsapp_notify_daily_plan?: boolean;
  email_privacy_locked?: boolean;
  created_at: string;
  updated_at: string;
}

export type ProjectStatus = 'PLANNING' | 'ACTIVE' | 'ON_HOLD' | 'COMPLETED' | 'ARCHIVED';
export type ProjectPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: string;
  role: string;
  created_at: string;
  user?: User;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  status: ProjectStatus;
  priority: ProjectPriority;
  owner_id: string;
  start_date?: string;
  due_date?: string;
  created_at: string;
  updated_at: string;
  owner?: User;
  members: ProjectMember[];
}

export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'IN_REVIEW' | 'COMPLETED' | 'BLOCKED';
export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export interface TaskComment {
  id: string;
  task_id: string;
  user_id: string;
  content: string;
  created_at: string;
  updated_at: string;
  user?: User;
}

export interface Task {
  id: string;
  project_id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  assignee_id?: string;
  created_by: string;
  due_date?: string;
  created_at: string;
  updated_at: string;
  assignee?: User;
  creator?: User;
  comments: TaskComment[];
}

export type BlockerSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type BlockerStatus = 'OPEN' | 'RESOLVED';

export interface Blocker {
  id: string;
  task_id: string;
  reported_by: string;
  description: string;
  severity: BlockerSeverity;
  status: BlockerStatus;
  created_at: string;
  resolved_at?: string;
  reporter?: User;
}

export interface Activity {
  id: string;
  user_id?: string;
  project_id?: string;
  task_id?: string;
  activity_type: string;
  description: string;
  metadata_json?: Record<string, any>;
  created_at: string;
  user?: User;
}

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
}

export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: string;
  created_at: string;
  user?: User;
}

export interface Team {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  members: TeamMember[];
}

export interface Meeting {
  id: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  meeting_link: string;
  organizer_id: string;
  attendee_ids: string[];
}

export interface EmailItem {
  id: string;
  user_id: string;
  sender: string;
  sender_email: string;
  subject: string;
  body: string;
  urgency: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  category: 'CLIENT_BUG' | 'MEETING_REQUEST' | 'APPROVAL' | 'GENERAL';
  ai_summary?: string;
  ai_draft_reply?: string;
  status: 'UNREAD' | 'ACTIONED' | 'ARCHIVED';
  created_at: string;
}

export interface ChatMessage {
  id: string;
  channel_id: string;
  sender_id: string;
  sender?: User;
  content: string;
  message_type: 'TEXT' | 'SYSTEM';
  created_at: string;
}

export interface ChannelMember {
  id: string;
  channel_id: string;
  user_id: string;
  user?: User;
  joined_at: string;
  last_read_at: string;
}

export interface Channel {
  id: string;
  name?: string;
  type: 'DIRECT' | 'GROUP';
  description?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
  members: ChannelMember[];
  last_message?: ChatMessage;
  unread_count: number;
}

export interface WhatsAppAccount {
  id: string;
  provider: string;
  phone_number?: string;
  display_name?: string;
  status: string;
  last_connected_at?: string;
  last_disconnected_at?: string;
}

export interface WhatsAppConversation {
  id: string;
  whatsapp_account_id: string;
  external_conversation_id: number;
  contact_phone?: string;
  contact_name?: string;
  last_message_at?: string;
  last_message_preview?: string;
  unread_count: number;
  status: string;
}

export interface WhatsAppMessage {
  id: string;
  whatsapp_conversation_id: string;
  external_message_id: string;
  direction: "incoming" | "outgoing";
  sender_phone?: string;
  sender_name?: string;
  message_type: string;
  body?: string;
  provider_timestamp: string;
  status?: string;
}






