"use client";

import React, { useEffect, useState } from "react";
import { api, AIConversation } from "@/lib/api";
import {
  Bot,
  Sparkles,
  Send,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Wrench,
  MessageSquare,
  Clock,
  Terminal,
  Cpu
} from "lucide-react";

interface ChatMessage {
  id?: string;
  sender: "user" | "assistant";
  content: string;
  steps?: Array<{
    step_number: number;
    tool_name: string;
    description: string;
    status: string;
    result?: any;
  }>;
  actions_taken?: string[];
}

const SUGGESTED_PROMPTS = [
  "What emails are critical?",
  "What tasks do I need to do today?",
  "Who are our team members?",
  "List active projects.",
  "Create a project task.",
  "What blockers do we have?",
  "Summarize project status."
];

export default function AIAssistantPage() {
  const [conversations, setConversations] = useState<AIConversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputPrompt, setInputPrompt] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadConversations();
  }, []);

  async function loadConversations(currentActiveId?: string) {
    try {
      const data = await api.getAIConversations();
      setConversations(data);
      const targetId = currentActiveId || activeConvId;
      if (data.length > 0 && !targetId) {
        selectConversation(data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  }

  async function selectConversation(id: string) {
    setActiveConvId(id);
    try {
      const conv = await api.getAIConversationById(id);
      const formatted: ChatMessage[] = conv.messages.map((m) => ({
        id: m.id,
        sender: m.role === "user" ? "user" : "assistant",
        content: m.content,
        actions_taken: m.tool_calls?.summaries || []
      }));
      setMessages(formatted);
    } catch (err) {
      console.error(err);
    }
  }

  function startNewConversation() {
    setActiveConvId(null);
    setMessages([
      {
        sender: "assistant",
        content: "Hello! I am your AI Work OS Assistant. I can manage tasks, projects, team members, blockers, workload, and audit logs. How can I help you today?"
      }
    ]);
  }

  async function handleDeleteConversation(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    try {
      await api.deleteAIConversation(id);
      if (activeConvId === id) {
        startNewConversation();
      }
      loadConversations();
    } catch (err) {
      console.error(err);
    }
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!inputPrompt.trim() || loading) return;

    const userText = inputPrompt;
    setInputPrompt("");
    setLoading(true);

    // Append user message immediately
    setMessages((prev) => [...prev, { sender: "user", content: userText }]);

    try {
      const response = await api.postAIChat(userText, activeConvId || undefined);
      setActiveConvId(response.conversation_id);

      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          content: response.reply,
          steps: response.execution_steps,
          actions_taken: response.actions_taken
        }
      ]);

      // Pass active conversation ID to prevent duplicate re-fetching
      loadConversations(response.conversation_id);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          content: `AI service is currently unavailable: ${err.message || "Failed to process request."}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-6xl animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Bot className="w-6 h-6 text-emerald-400" /> AI Assistant Workspace
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Execute operations, query team members, operational data, assign work, and track blockers using natural language.
          </p>
        </div>
        <button
          onClick={startNewConversation}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-semibold text-xs flex items-center gap-2 hover:opacity-95 shadow-lg shadow-emerald-500/20 transition-all self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" /> New Conversation
        </button>
      </div>

      {/* Main Grid: History Drawer + Active Chat */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Drawer: Past Conversations */}
        <div className="glass-card rounded-xl border border-slate-800 p-4 space-y-4 lg:col-span-1 flex flex-col max-h-[600px]">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <MessageSquare className="w-3.5 h-3.5 text-cyan-400" /> Past Chats
          </h3>

          <div className="space-y-1.5 overflow-y-auto flex-1 pr-1">
            {conversations.length === 0 ? (
              <p className="text-xs text-slate-500 py-4">No past chats yet.</p>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => selectConversation(conv.id)}
                  className={`p-2.5 rounded-lg text-xs cursor-pointer flex items-center justify-between group transition-colors ${
                    activeConvId === conv.id
                      ? "bg-slate-800 text-white font-medium border border-slate-700"
                      : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                  }`}
                >
                  <span className="truncate flex-1">{conv.title}</span>
                  <button
                    onClick={(e) => handleDeleteConversation(conv.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 transition-opacity"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Area: Interactive Chat Stream */}
        <div className="glass-card rounded-xl border border-slate-800 lg:col-span-3 flex flex-col h-[600px] overflow-hidden">
          {/* Message Stream */}
          <div className="p-6 overflow-y-auto flex-1 space-y-6">
            {messages.map((msg, index) => {
              // Filter out internal technical log pills (like "Retrieved X projects" or "No matching tasks found")
              const uniqueActions = (msg.actions_taken || []).filter((act) => {
                const lower = act.trim().toLowerCase();
                if (lower === msg.content.trim().toLowerCase()) return false;
                if (lower.startsWith("retrieved") || lower.startsWith("no matching") || lower.startsWith("error:")) return false;
                return true;
              });

              return (
                <div
                  key={index}
                  className={`flex items-start gap-3 text-xs ${
                    msg.sender === "user" ? "flex-row-reverse" : "flex-row"
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${
                      msg.sender === "user"
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                    }`}
                  >
                    {msg.sender === "user" ? "You" : "AI"}
                  </div>

                  <div className="space-y-2 max-w-xl">
                    {/* Tool Execution Steps Pills (Action Visibility) */}
                    {msg.steps && msg.steps.length > 0 && (
                      <div className="space-y-1.5 mb-2">
                        {msg.steps.map((step, sIdx) => (
                          <div
                            key={sIdx}
                            className="bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-1.5 text-[11px] font-mono text-slate-300 flex items-center gap-2"
                          >
                            <Wrench className="w-3 h-3 text-cyan-400" />
                            <span>Tool: <strong className="text-white">{step.tool_name}</strong></span>
                            <span className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold ml-auto ${
                              step.status === "SUCCESS" ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400"
                            }`}>
                              {step.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Main Message Bubble */}
                    <div
                      className={`p-4 rounded-xl border leading-relaxed whitespace-pre-line ${
                        msg.sender === "user"
                          ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-100"
                          : "bg-slate-900/90 border-slate-800 text-slate-200"
                      }`}
                    >
                      {msg.content}
                    </div>

                    {/* Verified User Action Pills */}
                    {uniqueActions.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {uniqueActions.map((act, aIdx) => (
                          <span
                            key={aIdx}
                            className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-full text-[10px] font-medium flex items-center gap-1"
                          >
                            <CheckCircle2 className="w-3 h-3" /> {act}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex items-center gap-3 text-xs text-slate-400 pl-2">
                <div className="w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                <span>Executing requested tool actions & verifying state...</span>
              </div>
            )}
          </div>

          {/* Prompt Suggestion Chips */}
          <div className="px-4 py-2 bg-slate-950/80 border-t border-slate-800 flex items-center gap-2 overflow-x-auto">
            <span className="text-[10px] uppercase font-bold text-slate-500 shrink-0">Try Prompt:</span>
            {SUGGESTED_PROMPTS.map((p, i) => (
              <button
                key={i}
                onClick={() => setInputPrompt(p)}
                className="text-[11px] text-slate-400 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-800 px-2.5 py-1 rounded-full whitespace-nowrap transition-colors"
              >
                {p}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <form onSubmit={handleSend} className="p-4 bg-slate-950 border-t border-slate-800 flex items-center gap-3">
            <input
              type="text"
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              placeholder="Ask AI to query team members, projects, create tasks, assign work, or file blockers..."
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
            <button
              type="submit"
              disabled={loading || !inputPrompt.trim()}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-bold text-xs hover:opacity-90 disabled:opacity-50 shadow-md shadow-emerald-500/20 transition-all flex items-center gap-2"
            >
              <Send className="w-4 h-4" /> Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
