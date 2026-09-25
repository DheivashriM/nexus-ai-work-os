"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Meeting, User } from "@/types";
import { Modal } from "@/components/ui/Modal";
import { CalendarView } from "@/components/CalendarView";
import { Video, Plus, Sparkles } from "lucide-react";

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Schedule Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [attendee, setAttendee] = useState("");
  const [dateTime, setDateTime] = useState("today 6pm");
  const [duration, setDuration] = useState(30);
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  async function loadData() {
    setLoading(true);
    try {
      const [mRes, uRes] = await Promise.all([
        api.getMeetings().catch(() => []),
        api.getUsers().catch(() => [])
      ]);
      setMeetings(mRes);
      setUsers(uRes);
      if (uRes.length > 0 && !attendee) {
        setAttendee(uRes[0].name);
      }
    } catch (err) {
      console.error("Failed to load meetings data:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const handleScheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!attendee) {
      setErrorMsg("Please select or specify an attendee.");
      return;
    }

    setSubmitting(true);
    setErrorMsg("");

    try {
      await api.scheduleMeeting({
        attendee,
        title: title || undefined,
        date_time: dateTime,
        duration_minutes: duration,
        description: description || undefined
      });

      // Reset form and reload list
      setTitle("");
      setDescription("");
      setIsModalOpen(false);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to schedule meeting.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Video className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Meetings & Visual Google Calendar</h1>
              <p className="text-sm text-slate-400 mt-0.5">
                Visually inspect meeting schedules, join Google Meet calls, or schedule new meetings with team members.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-semibold text-sm shadow-lg shadow-emerald-500/20 transition-all duration-200"
        >
          <Plus className="w-4 h-4" />
          <span>Schedule Meeting</span>
        </button>
      </div>

      {/* Info Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex items-start gap-3 text-sm text-slate-300 backdrop-blur-sm">
        <Sparkles className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <p className="font-medium text-slate-200">Interactive Visual Calendar & Google Meet Integration</p>
          <p className="text-xs text-slate-400 mt-1">
            Meetings created manually or via the AI Assistant (e.g. <span className="text-cyan-400 font-mono">"schedule a meeting with Selva tomorrow 10am"</span>) appear visually on your calendar grid with Google Meet join links and attendee notifications.
          </p>
        </div>
      </div>

      {/* Interactive Calendar View */}
      {loading ? (
        <div className="h-96 rounded-2xl bg-slate-900/40 border border-slate-800/60 animate-pulse flex items-center justify-center text-slate-500 text-sm">
          Loading Visual Calendar...
        </div>
      ) : (
        <CalendarView
          meetings={meetings}
          users={users}
          onScheduleForDate={(dateStr) => {
            setDateTime(`${dateStr} 6pm`);
            setIsModalOpen(true);
          }}
          onOpenScheduleModal={() => setIsModalOpen(true)}
        />
      )}

      {/* Manual Meeting Creation Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Schedule New Meeting"
      >
        <form onSubmit={handleScheduleSubmit} className="space-y-4">
          {errorMsg && (
            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium">
              {errorMsg}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Meeting Title / Topic
            </label>
            <input
              type="text"
              placeholder="e.g. Project Sync with Selva"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Select Attendee <span className="text-emerald-400">*</span>
            </label>
            {users.length > 0 ? (
              <select
                value={attendee}
                onChange={(e) => setAttendee(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-emerald-500 transition-colors"
              >
                {users.map((u) => (
                  <option key={u.id} value={u.name}>
                    {u.name} ({u.email})
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                placeholder="e.g. Selva"
                value={attendee}
                onChange={(e) => setAttendee(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-emerald-500 transition-colors"
                required
              />
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Date & Time Expression
              </label>
              <input
                type="text"
                placeholder="e.g. today 6pm, tomorrow 10am"
                value={dateTime}
                onChange={(e) => setDateTime(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Duration (minutes)
              </label>
              <select
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-emerald-500 transition-colors"
              >
                <option value={15}>15 mins</option>
                <option value={30}>30 mins</option>
                <option value={45}>45 mins</option>
                <option value={60}>60 mins</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Description / Agenda
            </label>
            <textarea
              rows={3}
              placeholder="Optional meeting goals or discussion points..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-emerald-500 transition-colors resize-none"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 rounded-xl text-slate-400 hover:text-white text-sm font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-semibold text-sm shadow-md transition-all duration-200 disabled:opacity-50"
            >
              {submitting ? (
                <span>Scheduling...</span>
              ) : (
                <>
                  <Video className="w-4 h-4" />
                  <span>Create Meeting</span>
                </>
              )}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
