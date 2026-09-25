"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { Check, CheckCheck, MessageSquare, RefreshCw, Search, Send, Smartphone } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { WhatsAppConversation, WhatsAppMessage } from "@/types";

export default function WhatsAppInboxPage() {
  const { user } = useAuth();
  const [status, setStatus] = useState("Not Connected");
  const [conversations, setConversations] = useState<WhatsAppConversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<WhatsAppMessage[]>([]);
  const [query, setQuery] = useState("");
  const [body, setBody] = useState("");
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  async function loadConversations() {
    try {
      const [providerStatus, items] = await Promise.all([api.getWhatsAppStatus(), api.getWhatsAppConversations()]);
      setStatus(providerStatus.connected ? "Connected" : "Not Connected");
      setConversations(items);
      setActiveId((current) => current || items[0]?.id || null);
    } catch (err: any) {
      setStatus("Not Connected");
      setError(err.message || "Unable to load WhatsApp Inbox");
    }
  }

  useEffect(() => { loadConversations(); }, []);

  useEffect(() => {
    if (!activeId) return;
    api.getWhatsAppMessages(activeId).then(setMessages).catch((err) => setError(err.message));
  }, [activeId]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  useEffect(() => {
    if (!user) return;
    const socket = new WebSocket(`ws://localhost:8000/api/chat/ws?user_id=${user.id}`);
    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === "whatsapp.message.created") {
          const incoming = payload.message as WhatsAppMessage;
          if (payload.message.conversation_id === activeId) {
            setMessages((current) => current.some((item) => item.id === incoming.id) ? current : [...current, incoming]);
          }
          loadConversations();
        }
      } catch { /* Ignore malformed shared socket frames. */ }
    };
    return () => socket.close();
  }, [user?.id, activeId]);

  const active = conversations.find((item) => item.id === activeId);
  const filtered = conversations.filter((item) => `${item.contact_name || ""} ${item.contact_phone || ""} ${item.last_message_preview || ""}`.toLowerCase().includes(query.toLowerCase()));

  async function handleSend(event: FormEvent) {
    event.preventDefault();
    if (!activeId || !body.trim() || sending) return;
    const text = body.trim(); setBody(""); setSending(true); setError("");
    try {
      const sent = await api.sendWhatsAppMessage(activeId, text);
      setMessages((current) => [...current, sent]);
      await loadConversations();
    } catch (err: any) { setBody(text); setError(err.message || "Message failed"); }
    finally { setSending(false); }
  }

  return <div className="h-[calc(100vh-6rem)] flex flex-col gap-5">
    <header className="flex items-start justify-between border-b border-slate-800 pb-5"><div><div className="flex items-center gap-3"><MessageSquare className="text-emerald-400" /><h1 className="text-2xl font-bold text-white">WhatsApp Inbox</h1><span className={`text-[10px] uppercase tracking-widest px-2 py-1 rounded-full border ${status === "Connected" ? "text-emerald-300 bg-emerald-500/10 border-emerald-500/30" : "text-slate-400 bg-slate-800 border-slate-700"}`}>WhatsApp {status}</span></div><p className="text-sm text-slate-400 mt-2">External customer conversations via Meta Cloud API. Internal Nexus chat is separate.</p></div><button onClick={loadConversations} title="Refresh conversations" className="p-2 rounded-lg border border-slate-700 text-slate-300 hover:text-white"><RefreshCw className="w-4 h-4" /></button></header>
    {error && <div className="border border-rose-500/30 bg-rose-500/10 text-rose-300 rounded-xl px-4 py-3 text-sm">{error}</div>}
    <div className="grid grid-cols-[minmax(240px,320px)_1fr] min-h-0 flex-1 border border-slate-800 rounded-2xl overflow-hidden bg-slate-900/40"><aside className="border-r border-slate-800 flex flex-col min-h-0"><div className="p-4 border-b border-slate-800"><div className="relative"><Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search conversations" className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 pl-9 pr-3 text-sm text-white outline-none focus:border-emerald-500" /></div></div><div className="overflow-y-auto">{filtered.map((item) => <button key={item.id} onClick={() => setActiveId(item.id)} className={`w-full text-left p-4 border-b border-slate-800/70 hover:bg-slate-800/50 ${activeId === item.id ? "bg-slate-800/80" : ""}`}><div className="flex justify-between gap-2"><span className="font-semibold text-white truncate">{item.contact_name || "Unknown contact"}</span>{item.unread_count > 0 && <span className="bg-emerald-500 text-slate-950 text-xs font-bold rounded-full min-w-5 h-5 px-1 flex items-center justify-center">{item.unread_count}</span>}</div><div className="text-xs text-slate-500 mt-1">{item.contact_phone || "No phone supplied"}</div><div className="text-sm text-slate-400 truncate mt-2">{item.last_message_preview || "No message preview"}</div></button>)}{filtered.length === 0 && <div className="p-6 text-sm text-slate-500">No synced WhatsApp conversations.</div>}</div></aside><section className="flex flex-col min-h-0">{active ? <><div className="p-5 border-b border-slate-800 flex items-center gap-3"><div className="w-10 h-10 rounded-full bg-emerald-500/15 flex items-center justify-center text-emerald-300"><Smartphone className="w-5 h-5" /></div><div><h2 className="font-semibold text-white">{active.contact_name || "Unknown contact"}</h2><p className="text-xs text-slate-400">{active.contact_phone || "WhatsApp contact"} · {active.status}</p></div></div><div className="flex-1 overflow-y-auto p-5 space-y-3">{messages.map((message) => <div key={message.id} className={`flex ${message.direction === "outgoing" ? "justify-end" : "justify-start"}`}><div className={`max-w-[75%] rounded-2xl px-4 py-3 ${message.direction === "outgoing" ? "bg-emerald-500 text-slate-950 rounded-br-sm" : "bg-slate-800 text-slate-100 rounded-bl-sm"}`}><p className="text-sm whitespace-pre-wrap">{message.body || "Unsupported message type"}</p><div className="flex items-center justify-end gap-1 mt-1 text-[10px] opacity-70">{new Date(message.provider_timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}{message.direction === "outgoing" && (message.status === "failed" ? <span>Failed</span> : message.status === "pending" ? <Check className="w-3 h-3" /> : <CheckCheck className="w-3 h-3" />)}</div></div></div>)}<div ref={endRef} /></div><form onSubmit={handleSend} className="p-4 border-t border-slate-800 flex gap-3"><input value={body} onChange={(event) => setBody(event.target.value)} placeholder="Type a WhatsApp message" className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-emerald-500" /><button disabled={sending || !body.trim()} className="px-4 rounded-xl bg-emerald-500 text-slate-950 font-semibold disabled:opacity-40 flex items-center gap-2"><Send className="w-4 h-4" />Send</button></form></> : <div className="flex-1 flex items-center justify-center text-slate-500">No conversation selected.</div>}</section></div>
  </div>;
}