"use client";

import React, { useEffect, useState, useRef } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Channel, ChatMessage, User } from "@/types";
import {
  MessageSquare,
  Hash,
  User as UserIcon,
  Plus,
  Send,
  Search,
  Sparkles,
  Users,
  Check,
  Circle,
  X,
  Radio,
  Clock,
  ShieldCheck,
  Smile,
  Paperclip
} from "lucide-react";
import { cn, formatTime } from "@/lib/utils";

export default function MessagesPage() {
  const { user } = useAuth();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [activeChannelId, setActiveChannelId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [onlineUserIds, setOnlineUserIds] = useState<string[]>([]);
  
  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("");
  const [tabFilter, setTabFilter] = useState<"ALL" | "DIRECT" | "GROUP">("ALL");

  // Message Input
  const [inputContent, setInputContent] = useState("");
  const [sending, setSending] = useState(false);

  // New Chat Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"DIRECT" | "GROUP">("DIRECT");
  const [selectedRecipientId, setSelectedRecipientId] = useState<string>("");
  const [groupName, setGroupName] = useState("");
  const [groupDesc, setGroupDesc] = useState("");
  const [selectedGroupMemberIds, setSelectedGroupMemberIds] = useState<string[]>([]);

  // Socket & Auto scroll refs
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // 1. Fetch initial Channels & Team Users
  const loadChannels = async () => {
    try {
      const data = await api.getChannels();
      setChannels(data);
      if (!activeChannelId && data.length > 0) {
        setActiveChannelId(data[0].id);
      }
    } catch (err) {
      console.error("Error loading channels", err);
    }
  };

  const loadUsers = async () => {
    try {
      const teamUsers = await api.getUsers();
      setUsers(teamUsers);
    } catch (err) {
      console.error("Error loading users", err);
    }
  };

  const loadOnlineUsers = async () => {
    try {
      const online = await api.getOnlineUsers();
      setOnlineUserIds(online);
    } catch (err) {}
  };

  useEffect(() => {
    loadChannels();
    loadUsers();
    loadOnlineUsers();
    const onlineInterval = setInterval(loadOnlineUsers, 10000);
    return () => clearInterval(onlineInterval);
  }, []);

  // 2. Fetch Messages when activeChannelId changes
  const loadMessages = async (chId: string) => {
    try {
      const msgs = await api.getChannelMessages(chId);
      setMessages(msgs);
      // Mark as read in channel list locally
      setChannels((prev) =>
        prev.map((c) => (c.id === chId ? { ...c, unread_count: 0 } : c))
      );
      api.markChannelRead(chId).catch(() => {});
    } catch (err) {
      console.error("Error loading messages", err);
    }
  };

  useEffect(() => {
    if (activeChannelId) {
      loadMessages(activeChannelId);
    }
  }, [activeChannelId]);

  // Auto scroll feed to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 3. WebSocket Real-time Connection
  useEffect(() => {
    if (!user) return;

    const wsUrl = `ws://localhost:8000/api/chat/ws?user_id=${user.id}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket messaging connected as", user.name);
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === "new_message") {
          const { channel_id, message } = payload;
          
          // Append to active channel feed if open
          setActiveChannelId((currentActiveId) => {
            if (currentActiveId === channel_id) {
              setMessages((prevMsgs) => {
                if (prevMsgs.some((m) => m.id === message.id)) return prevMsgs;
                return [...prevMsgs, message];
              });
            }
            return currentActiveId;
          });

          // Refresh channel list to update last message & unread badge
          loadChannels();
        }
      } catch (err) {
        console.error("Error parsing WS message", err);
      }
    };

    ws.onerror = (err) => {
      console.warn("WebSocket error", err);
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
    };

    return () => {
      ws.close();
    };
  }, [user?.id]);

  // Polling fallback to keep message list updated
  useEffect(() => {
    const interval = setInterval(() => {
      if (activeChannelId) {
        api.getChannelMessages(activeChannelId).then((msgs) => {
          setMessages((prev) => {
            if (msgs.length !== prev.length) return msgs;
            return prev;
          });
        }).catch(() => {});
      }
      loadChannels();
    }, 5000);
    return () => clearInterval(interval);
  }, [activeChannelId]);

  // 4. Send Message Action
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputContent.trim() || !activeChannelId || sending) return;

    const content = inputContent.trim();
    setInputContent("");
    setSending(true);

    try {
      const newMsg = await api.sendChatMessage(activeChannelId, content);
      setMessages((prev) => {
        if (prev.some((m) => m.id === newMsg.id)) return prev;
        return [...prev, newMsg];
      });
      loadChannels();
    } catch (err) {
      console.error("Failed to send message", err);
      setInputContent(content); // restore on error
    } finally {
      setSending(false);
    }
  };

  // 5. Create New Direct Chat
  const handleCreateDirectChat = async () => {
    if (!selectedRecipientId) return;
    try {
      const ch = await api.createDirectChat(selectedRecipientId);
      await loadChannels();
      setActiveChannelId(ch.id);
      setIsModalOpen(false);
      setSelectedRecipientId("");
    } catch (err) {
      console.error("Error creating direct chat", err);
    }
  };

  // 6. Create New Group Channel
  const handleCreateGroupChannel = async () => {
    if (!groupName.trim()) return;
    try {
      const ch = await api.createGroupChat({
        name: groupName.trim(),
        description: groupDesc.trim() || undefined,
        member_ids: selectedGroupMemberIds,
      });
      await loadChannels();
      setActiveChannelId(ch.id);
      setIsModalOpen(false);
      setGroupName("");
      setGroupDesc("");
      setSelectedGroupMemberIds([]);
    } catch (err) {
      console.error("Error creating group channel", err);
    }
  };

  // Active Channel Details
  const activeChannel = channels.find((c) => c.id === activeChannelId);

  // Helper to format channel title / direct participant
  const getChannelDisplay = (ch: Channel) => {
    if (ch.type === "GROUP") {
      return {
        title: `# ${ch.name}`,
        subtitle: ch.description || `${ch.members?.length || 0} members`,
        isOnline: false,
      };
    }
    // Direct message: find other member
    const otherMember = ch.members?.find((m) => m.user_id !== user?.id);
    const otherUser = otherMember?.user || users.find((u) => u.id === otherMember?.user_id);
    const isOnline = otherUser ? onlineUserIds.includes(otherUser.id) : false;
    return {
      title: otherUser ? otherUser.name : "Direct Message",
      subtitle: otherUser ? `${otherUser.role} • ${otherUser.email}` : "1-on-1 Chat",
      isOnline,
      user: otherUser
    };
  };

  // Filter channels for left sidebar
  const filteredChannels = channels.filter((ch) => {
    if (tabFilter === "DIRECT" && ch.type !== "DIRECT") return false;
    if (tabFilter === "GROUP" && ch.type !== "GROUP") return false;

    if (!searchQuery) return true;
    const display = getChannelDisplay(ch);
    return (
      display.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ch.last_message?.content.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  return (
    <div className="h-[calc(100vh-6rem)] flex gap-4 overflow-hidden">
      {/* LEFT PANEL: Channels & DM Navigation List */}
      <div className="w-80 md:w-96 bg-slate-900/70 border border-slate-800 backdrop-blur-xl rounded-2xl flex flex-col overflow-hidden shadow-xl">
        {/* Header */}
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center">
              <MessageSquare className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white leading-none">Messages & Channels</h2>
              <p className="text-[11px] text-slate-400 mt-0.5">Real-time Workspace Chat</p>
            </div>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="p-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold transition-all shadow-md shadow-emerald-500/20 flex items-center gap-1 text-xs"
            title="Start New Chat"
          >
            <Plus className="w-4 h-4" />
            <span>New</span>
          </button>
        </div>

        {/* Search Bar */}
        <div className="p-3 border-b border-slate-800/60">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search chat or message..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
            />
          </div>

          {/* Filter Tabs */}
          <div className="flex gap-1 mt-2.5 bg-slate-950/60 p-1 rounded-xl border border-slate-800/60">
            {(["ALL", "DIRECT", "GROUP"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTabFilter(t)}
                className={cn(
                  "flex-1 text-[11px] font-semibold py-1 rounded-lg transition-all",
                  tabFilter === t
                    ? "bg-slate-800 text-emerald-400 shadow-sm border border-slate-700/60"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                {t === "ALL" ? "All" : t === "DIRECT" ? "Direct" : "Groups"}
              </button>
            ))}
          </div>
        </div>

        {/* Channel List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {filteredChannels.length === 0 ? (
            <div className="text-center py-10 px-4">
              <MessageSquare className="w-8 h-8 text-slate-600 mx-auto mb-2 opacity-50" />
              <p className="text-xs text-slate-400">No conversations found</p>
            </div>
          ) : (
            filteredChannels.map((ch) => {
              const display = getChannelDisplay(ch);
              const isActive = ch.id === activeChannelId;
              const hasUnread = ch.unread_count > 0;

              return (
                <button
                  key={ch.id}
                  onClick={() => setActiveChannelId(ch.id)}
                  className={cn(
                    "w-full text-left p-3 rounded-xl transition-all duration-150 flex items-start gap-3 group relative border",
                    isActive
                      ? "bg-slate-800/90 border-slate-700/80 shadow-md"
                      : "bg-transparent border-transparent hover:bg-slate-800/40 hover:border-slate-800/60"
                  )}
                >
                  {/* Channel Icon or User Avatar */}
                  <div className="relative flex-shrink-0">
                    {ch.type === "GROUP" ? (
                      <div className="w-9 h-9 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-emerald-400 font-bold">
                        <Hash className="w-4 h-4" />
                      </div>
                    ) : (
                      <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-slate-950 font-bold flex items-center justify-center text-xs shadow-sm">
                        {display.title.slice(0, 2).toUpperCase()}
                      </div>
                    )}
                    {ch.type === "DIRECT" && display.isOnline && (
                      <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-500 ring-2 ring-slate-950" />
                    )}
                  </div>

                  {/* Channel Text Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span
                        className={cn(
                          "text-xs font-semibold truncate",
                          isActive ? "text-white" : "text-slate-200 group-hover:text-white"
                        )}
                      >
                        {display.title}
                      </span>
                      {ch.last_message && (
                        <span className="text-[10px] text-slate-400 font-mono">
                          {formatTime(ch.last_message.created_at)}
                        </span>
                      )}
                    </div>

                    <p className="text-[11px] text-slate-400 truncate mt-0.5 font-normal">
                      {ch.last_message
                        ? `${ch.last_message.sender?.name.split(" ")[0] || "User"}: ${ch.last_message.content}`
                        : display.subtitle}
                    </p>
                  </div>

                  {/* Unread Pill */}
                  {hasUnread && !isActive && (
                    <span className="w-5 h-5 rounded-full bg-emerald-500 text-slate-950 font-extrabold text-[10px] flex items-center justify-center shadow-lg shadow-emerald-500/30">
                      {ch.unread_count}
                    </span>
                  )}
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* RIGHT MAIN PANEL: Active Chat Feed */}
      <div className="flex-1 bg-slate-900/70 border border-slate-800 backdrop-blur-xl rounded-2xl flex flex-col overflow-hidden shadow-xl">
        {activeChannel ? (
          <>
            {/* Header */}
            {(() => {
              const display = getChannelDisplay(activeChannel);
              return (
                <div className="p-4 border-b border-slate-800/80 flex items-center justify-between bg-slate-950/40">
                  <div className="flex items-center gap-3">
                    {activeChannel.type === "GROUP" ? (
                      <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center font-bold">
                        <Hash className="w-5 h-5" />
                      </div>
                    ) : (
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-slate-950 font-bold flex items-center justify-center text-sm shadow-md">
                        {display.title.slice(0, 2).toUpperCase()}
                      </div>
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-base font-bold text-white">{display.title}</h2>
                        {activeChannel.type === "DIRECT" && display.isOnline && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                            Online
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">{display.subtitle}</p>
                    </div>
                  </div>

                  {/* Channel Meta & Live Socket Status */}
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-xl border border-emerald-500/20 flex items-center gap-1.5">
                      <Radio className="w-3 h-3 animate-pulse text-emerald-400" />
                      Real-time WS Active
                    </span>
                  </div>
                </div>
              );
            })()}

            {/* Scrollable Message List */}
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
              {messages.length === 0 ? (
                <div className="text-center py-16">
                  <Sparkles className="w-10 h-10 text-slate-600 mx-auto mb-2 opacity-60" />
                  <p className="text-sm font-semibold text-slate-300">Start the conversation</p>
                  <p className="text-xs text-slate-500 mt-1">Send a direct message or channel update below.</p>
                </div>
              ) : (
                messages.map((msg, index) => {
                  const isCurrentUser = msg.sender_id === user?.id;
                  const isSystem = msg.message_type === "SYSTEM";

                  if (isSystem) {
                    return (
                      <div key={msg.id} className="text-center my-3">
                        <span className="text-[11px] font-medium text-slate-400 bg-slate-800/60 px-3 py-1 rounded-full border border-slate-700/60">
                          {msg.content}
                        </span>
                      </div>
                    );
                  }

                  return (
                    <div
                      key={msg.id}
                      className={cn(
                        "flex items-end gap-3 group max-w-2xl",
                        isCurrentUser ? "ml-auto flex-row-reverse" : "mr-auto"
                      )}
                    >
                      {/* Avatar */}
                      <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-emerald-400 flex-shrink-0">
                        {msg.sender?.name?.slice(0, 2).toUpperCase() || "U"}
                      </div>

                      {/* Bubble Container */}
                      <div className={cn("space-y-1", isCurrentUser ? "text-right" : "text-left")}>
                        <div className="flex items-center gap-2 px-1">
                          <span className="text-xs font-semibold text-slate-300">
                            {msg.sender?.name || "Team Member"}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {formatTime(msg.created_at)}
                          </span>
                        </div>

                        <div
                          className={cn(
                            "p-3.5 rounded-2xl text-xs leading-relaxed shadow-md border",
                            isCurrentUser
                              ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-br-none border-emerald-500/40"
                              : "bg-slate-800/90 text-slate-100 rounded-bl-none border-slate-700/80"
                          )}
                        >
                          {msg.content}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Bar */}
            <form onSubmit={handleSendMessage} className="p-3 md:p-4 border-t border-slate-800/80 bg-slate-950/50 flex items-center gap-2">
              <div className="flex-1 relative flex items-center">
                <input
                  type="text"
                  placeholder={`Message ${
                    activeChannel.type === "GROUP"
                      ? `#${activeChannel.name}`
                      : getChannelDisplay(activeChannel).title
                  }...`}
                  value={inputContent}
                  onChange={(e) => setInputContent(e.target.value)}
                  className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-4 pr-10 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40 transition-all"
                />
              </div>

              <button
                type="submit"
                disabled={sending || !inputContent.trim()}
                className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-bold p-3 rounded-xl shadow-md shadow-emerald-500/20 transition-all disabled:opacity-40 flex items-center justify-center"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
            <MessageSquare className="w-12 h-12 text-slate-600 mb-3 opacity-40" />
            <h3 className="text-base font-bold text-white">Select a chat to begin</h3>
            <p className="text-xs text-slate-400 max-w-sm mt-1">
              Choose a Direct Message thread or Group Channel from the left sidebar or start a new conversation.
            </p>
          </div>
        )}
      </div>

      {/* NEW CHAT / GROUP MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                Start Conversation
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Tabs */}
            <div className="flex gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
              <button
                onClick={() => setModalMode("DIRECT")}
                className={cn(
                  "flex-1 text-xs font-semibold py-1.5 rounded-lg transition-all",
                  modalMode === "DIRECT"
                    ? "bg-slate-800 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                1-on-1 Direct Message
              </button>
              <button
                onClick={() => setModalMode("GROUP")}
                className={cn(
                  "flex-1 text-xs font-semibold py-1.5 rounded-lg transition-all",
                  modalMode === "GROUP"
                    ? "bg-slate-800 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                Group Channel
              </button>
            </div>

            {modalMode === "DIRECT" ? (
              <div className="space-y-3">
                <label className="block text-xs font-medium text-slate-300">
                  Select Team Member
                </label>
                <div className="max-h-60 overflow-y-auto space-y-1.5">
                  {users
                    .filter((u) => u.id !== user?.id)
                    .map((u) => {
                      const isSelected = selectedRecipientId === u.id;
                      return (
                        <div
                          key={u.id}
                          onClick={() => setSelectedRecipientId(u.id)}
                          className={cn(
                            "flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all",
                            isSelected
                              ? "bg-emerald-500/10 border-emerald-500/50 text-white"
                              : "bg-slate-950/60 border-slate-800/80 hover:bg-slate-800/60 text-slate-300"
                          )}
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-emerald-400">
                              {u.name.slice(0, 2).toUpperCase()}
                            </div>
                            <div>
                              <p className="text-xs font-semibold">{u.name}</p>
                              <p className="text-[10px] text-slate-400">{u.role} • {u.email}</p>
                            </div>
                          </div>
                          {isSelected && <Check className="w-4 h-4 text-emerald-400" />}
                        </div>
                      );
                    })}
                </div>

                <button
                  onClick={handleCreateDirectChat}
                  disabled={!selectedRecipientId}
                  className="w-full mt-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs py-2.5 rounded-xl shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-40"
                >
                  Start Direct Message
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Channel Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. project-aleta-planet"
                    value={groupName}
                    onChange={(e) => setGroupName(e.target.value)}
                    className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/60"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Description (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Cross-border API discussion"
                    value={groupDesc}
                    onChange={(e) => setGroupDesc(e.target.value)}
                    className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/60"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Select Members
                  </label>
                  <div className="max-h-40 overflow-y-auto space-y-1 border border-slate-800/80 rounded-xl p-2 bg-slate-950/60">
                    {users
                      .filter((u) => u.id !== user?.id)
                      .map((u) => {
                        const isChecked = selectedGroupMemberIds.includes(u.id);
                        return (
                          <div
                            key={u.id}
                            onClick={() => {
                              if (isChecked) {
                                setSelectedGroupMemberIds((prev) => prev.filter((id) => id !== u.id));
                              } else {
                                setSelectedGroupMemberIds((prev) => [...prev, u.id]);
                              }
                            }}
                            className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-800/60 cursor-pointer text-xs"
                          >
                            <span className="text-slate-200">{u.name} ({u.role})</span>
                            <input
                              type="checkbox"
                              checked={isChecked}
                              readOnly
                              className="accent-emerald-500 rounded"
                            />
                          </div>
                        );
                      })}
                  </div>
                </div>

                <button
                  onClick={handleCreateGroupChannel}
                  disabled={!groupName.trim()}
                  className="w-full mt-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs py-2.5 rounded-xl shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-40"
                >
                  Create Group Channel
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
