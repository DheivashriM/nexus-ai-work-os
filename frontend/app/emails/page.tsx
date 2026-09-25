"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EmailItem, Project } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import {
  Mail,
  AlertTriangle,
  Sparkles,
  Send,
  CheckCircle2,
  Plus,
  ArrowRight,
  ShieldAlert,
  Clock,
  UserCheck,
  CheckSquare,
  RefreshCw
} from "lucide-react";

export default function SmartEmailsPage() {
  const [emails, setEmails] = useState<EmailItem[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncingGmail, setSyncingGmail] = useState(false);
  const [filterUrgency, setFilterUrgency] = useState<string | null>(null);

  // Simulation Modal
  const [isSimulateModalOpen, setIsSimulateModalOpen] = useState(false);
  const [simSender, setSimSender] = useState("John Client");
  const [simEmail, setSimEmail] = useState("john@acme-corp.com");
  const [simSubject, setSimSubject] = useState("CRITICAL: Payment Checkout Failing in Production!");
  const [simBody, setSimBody] = useState("Hi team, users are getting 500 error when clicking pay now button. This is breaking checkout. Please investigate ASAP!");
  const [simulating, setSimulating] = useState(false);

  // Reply Edit State
  const [editingReplyId, setEditingReplyId] = useState<string | null>(null);
  const [replyText, setReplyText] = useState("");
  const [recipientMap, setRecipientMap] = useState<Record<string, string>>({});
  const [sendingId, setSendingId] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState("");
  const [connectedEmail, setConnectedEmail] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    try {
      const [eRes, pRes] = await Promise.all([
        api.getEmails(filterUrgency || undefined).catch(() => []),
        api.getProjects().catch(() => [])
      ]);
      setEmails(eRes);
      setProjects(pRes);
    } catch (err) {
      console.error("Failed to load email data:", err);
    } finally {
      setLoading(false);
    }
  }

  const handleSyncGmail = async () => {
    setSyncingGmail(true);
    try {
      const synced = await api.syncGmailInbox(10);
      setSuccessMsg(`Synced ${synced.length} new email(s) from ${connectedEmail || "your connected mailbox"}.`);
      setTimeout(() => setSuccessMsg(""), 4000);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to sync Gmail inbox.");
    } finally {
      setSyncingGmail(false);
    }
  };

  useEffect(() => {
    loadData();
    api.getMyEmailSettings()
      .then((settings) => setConnectedEmail(settings.enabled && settings.configured ? settings.email_address || null : null))
      .catch(() => setConnectedEmail(null));
  }, [filterUrgency]);

  const handleSimulateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSimulating(true);
    try {
      await api.simulateEmail({
        sender: simSender,
        sender_email: simEmail,
        subject: simSubject,
        body: simBody
      });
      setIsSimulateModalOpen(false);
      setSuccessMsg("New email ingested and analyzed by AI!");
      setTimeout(() => setSuccessMsg(""), 3000);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to simulate email");
    } finally {
      setSimulating(false);
    }
  };

  const handleSendReply = async (email: EmailItem) => {
    setSendingId(email.id);
    const targetRecipient = recipientMap[email.id] || email.sender_email;
    try {
      await api.sendEmailReply(email.id, replyText || undefined, targetRecipient);
      setSuccessMsg(`AI reply successfully dispatched to ${targetRecipient}!`);
      setTimeout(() => setSuccessMsg(""), 4000);
      setEditingReplyId(null);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to send reply");
    } finally {
      setSendingId(null);
    }
  };

  const handleConvertToTask = async (emailId: string) => {
    if (projects.length === 0) {
      alert("Please create a project first before converting emails to tasks.");
      return;
    }
    const projectId = projects[0].id;
    try {
      await api.convertEmailToTask(emailId, projectId);
      setSuccessMsg("Converted email to Task successfully!");
      setTimeout(() => setSuccessMsg(""), 3000);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to convert email to task");
    }
  };

  const getUrgencyBadge = (urgency: string) => {
    switch (urgency) {
      case "CRITICAL":
        return <span className="bg-red-500/10 border border-red-500/30 text-red-400 font-extrabold text-[11px] px-2.5 py-0.5 rounded-full flex items-center gap-1 animate-pulse"><ShieldAlert className="w-3 h-3" /> CRITICAL</span>;
      case "HIGH":
        return <span className="bg-orange-500/10 border border-orange-500/30 text-orange-400 font-bold text-[11px] px-2.5 py-0.5 rounded-full flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> HIGH URGENCY</span>;
      case "MEDIUM":
        return <span className="bg-amber-500/10 border border-amber-500/30 text-amber-300 font-medium text-[11px] px-2.5 py-0.5 rounded-full">MEDIUM</span>;
      default:
        return <span className="bg-slate-800 border border-slate-700 text-slate-400 text-[11px] px-2.5 py-0.5 rounded-full">LOW</span>;
    }
  };

  const criticalCount = emails.filter((e) => e.urgency === "CRITICAL" || e.urgency === "HIGH").length;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Mail className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Smart Email Assistant & Gmail Filter</h1>
              <p className="text-sm text-slate-400 mt-0.5">
                AI analyzes incoming emails, ranks urgency, and drafts automated replies for your 1-click approval.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <button
            onClick={handleSyncGmail}
            disabled={syncingGmail}
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-semibold text-sm transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${syncingGmail ? "animate-spin" : ""}`} />
            <span>{syncingGmail ? "Syncing Gmail..." : "Sync Real Gmail Inbox"}</span>
          </button>

          <button
            onClick={() => setIsSimulateModalOpen(true)}
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-slate-950 font-semibold text-sm shadow-lg shadow-cyan-500/20 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Simulate Email</span>
          </button>
        </div>
      </div>

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm font-medium flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* AI Urgency Banner */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 backdrop-blur-xl">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-white text-sm">AI Urgency Detection Engine Active</h3>
              {connectedEmail ? (
                <span className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold text-[11px] px-2.5 py-0.5 rounded-full flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Gmail Connected ({connectedEmail})
                </span>
              ) : (
                <span className="bg-slate-800 border border-slate-700 text-slate-400 font-semibold text-[11px] px-2.5 py-0.5 rounded-full">
                  Email Not Connected
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Currently monitoring inbox. Found <span className="text-red-400 font-bold">{criticalCount} urgent emails</span> requiring review.
            </p>
          </div>
        </div>

        {/* Urgency Filter Pills */}
        <div className="flex flex-wrap gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setFilterUrgency(null)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              filterUrgency === null ? "bg-slate-800 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            All ({emails.length})
          </button>
          <button
            onClick={() => setFilterUrgency("CRITICAL")}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              filterUrgency === "CRITICAL" ? "bg-red-500/20 text-red-400 border border-red-500/30" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Critical
          </button>
          <button
            onClick={() => setFilterUrgency("HIGH")}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              filterUrgency === "HIGH" ? "bg-orange-500/20 text-orange-400 border border-orange-500/30" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            High
          </button>
        </div>
      </div>

      {/* Email Inbox Cards */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-44 rounded-2xl bg-slate-900/40 border border-slate-800/60 animate-pulse" />
          ))}
        </div>
      ) : emails.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-12 text-center max-w-md mx-auto space-y-4">
          <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-slate-400">
            <Mail className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-semibold text-white">No Emails in Smart Inbox</h3>
          <p className="text-sm text-slate-400">
            Simulate receiving an email from a client or test email triggers to see AI urgency detection in action.
          </p>
          <button
            onClick={() => setIsSimulateModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Simulate First Email</span>
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {emails.map((e) => {
            const isEditing = editingReplyId === e.id;
            const currentReplyText = isEditing ? replyText : e.ai_draft_reply || "";

            return (
              <div
                key={e.id}
                className={`bg-slate-900/80 border rounded-2xl p-6 transition-all duration-200 backdrop-blur-xl space-y-5 ${
                  e.urgency === "CRITICAL"
                    ? "border-red-500/40 shadow-xl shadow-red-500/5"
                    : e.urgency === "HIGH"
                    ? "border-orange-500/30"
                    : "border-slate-800 hover:border-slate-700/80"
                }`}
              >
                {/* Email Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
                  <div className="flex items-start gap-3">
                    <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-200 font-bold text-sm shrink-0">
                      {e.sender.charAt(0)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-base">{e.sender}</span>
                        <span className="text-xs text-slate-400 font-mono">&lt;{e.sender_email}&gt;</span>
                      </div>
                      <h3 className="font-semibold text-slate-200 text-sm mt-0.5">{e.subject}</h3>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-auto">
                    {getUrgencyBadge(e.urgency)}
                    <span className="text-[11px] text-slate-500 font-medium">
                      {new Date(e.created_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}
                    </span>
                  </div>
                </div>

                {/* Email Content Body */}
                <div className="bg-slate-950/60 border border-slate-800/80 p-4 rounded-xl text-xs text-slate-300 leading-relaxed font-sans">
                  {e.body}
                </div>

                {/* AI Analysis & Draft Reply Box */}
                <div className="bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border border-cyan-500/30 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs font-bold text-cyan-400">
                      <Sparkles className="w-4 h-4 text-cyan-400" />
                      <span>AI Drafted Response (Suggested Action)</span>
                    </div>

                    {e.status === "ACTIONED" && (
                      <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Action Completed
                      </span>
                    )}
                  </div>

                  {/* Recipient To Address Bar */}
                  <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800 font-mono">
                    <span className="text-slate-400 font-bold text-[11px] uppercase tracking-wider">To (Recipient):</span>
                    <input
                      type="email"
                      value={recipientMap[e.id] ?? e.sender_email}
                      onChange={(evt) => setRecipientMap({ ...recipientMap, [e.id]: evt.target.value })}
                      className="bg-transparent text-emerald-400 font-semibold focus:outline-none flex-1 font-mono text-xs"
                      placeholder="Recipient email address..."
                    />
                  </div>

                  {isEditing ? (
                    <textarea
                      rows={4}
                      value={replyText}
                      onChange={(evt) => setReplyText(evt.target.value)}
                      className="w-full p-3 rounded-lg bg-slate-950 border border-cyan-500/50 text-xs text-slate-200 focus:outline-none focus:border-cyan-400 font-mono resize-none"
                    />
                  ) : (
                    <div className="text-xs text-slate-300 bg-slate-950/80 p-3 rounded-lg border border-slate-800 font-mono whitespace-pre-wrap leading-relaxed">
                      {currentReplyText}
                    </div>
                  )}

                  {/* Actions Toolbar */}
                  <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80">
                    <button
                      onClick={() => handleSendReply(e)}
                      disabled={sendingId === e.id}
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-bold text-xs shadow-md transition-all disabled:opacity-50"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>{sendingId === e.id ? "Sending..." : "Approve & Send AI Reply"}</span>
                    </button>

                    {!isEditing ? (
                      <button
                        onClick={() => {
                          setEditingReplyId(e.id);
                          setReplyText(e.ai_draft_reply || "");
                        }}
                        className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
                      >
                        Edit Draft
                      </button>
                    ) : (
                      <button
                        onClick={() => setEditingReplyId(null)}
                        className="px-3 py-2 rounded-xl bg-slate-800 text-slate-400 text-xs transition-colors"
                      >
                        Cancel Edit
                      </button>
                    )}

                    <button
                      onClick={() => handleConvertToTask(e.id)}
                      className="ml-auto inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-semibold transition-colors border border-slate-700/60"
                    >
                      <CheckSquare className="w-3.5 h-3.5" />
                      <span>Turn into Task</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Simulation Modal */}
      <Modal
        isOpen={isSimulateModalOpen}
        onClose={() => setIsSimulateModalOpen(false)}
        title="Simulate Inbound Email for AI Analysis"
      >
        <form onSubmit={handleSimulateSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Sender Name</label>
              <input
                type="text"
                value={simSender}
                onChange={(e) => setSimSender(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Sender Email</label>
              <input
                type="email"
                value={simEmail}
                onChange={(e) => setSimEmail(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Email Subject</label>
            <input
              type="text"
              value={simSubject}
              onChange={(e) => setSimSubject(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Email Body</label>
            <textarea
              rows={4}
              value={simBody}
              onChange={(e) => setSimBody(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm resize-none"
              required
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsSimulateModalOpen(false)}
              className="px-4 py-2 text-slate-400 hover:text-white text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={simulating}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-slate-950 font-bold text-sm"
            >
              {simulating ? "Processing AI Analysis..." : "Ingest & Analyze Email"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
