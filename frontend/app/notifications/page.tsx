"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Notification } from "@/types";
import { formatRelativeTime } from "@/lib/utils";
import { Bell, CheckCheck, MessageSquare, AlertCircle } from "lucide-react";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  async function loadNotifications() {
    try {
      const data = await api.getNotifications();
      setNotifications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadNotifications();
  }, []);

  async function handleMarkRead(id: string) {
    try {
      await api.markNotificationRead(id);
      loadNotifications();
    } catch (err) {
      console.error(err);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-medium">Loading Notifications...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl animate-in fade-in duration-300">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Internal Notifications</h1>
        <p className="text-xs text-slate-400 mt-1">Audit events, task assignments, comment alerts, and blocker notifications.</p>
      </div>

      <div className="glass-card rounded-xl border border-slate-800 overflow-hidden divide-y divide-slate-800/80">
        {notifications.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            No notifications available.
          </div>
        ) : (
          notifications.map((notif) => (
            <div
              key={notif.id}
              className={`p-4 flex items-start justify-between gap-4 transition-colors ${
                notif.read ? "bg-slate-950/40" : "bg-slate-900/60"
              }`}
            >
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg mt-0.5 ${
                  notif.type.includes("BLOCKER") ? "bg-rose-500/20 text-rose-400" : "bg-cyan-500/20 text-cyan-400"
                }`}>
                  <Bell className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white flex items-center gap-2">
                    {notif.title}
                    {!notif.read && (
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                    )}
                  </h3>
                  <p className="text-xs text-slate-300 mt-1">{notif.message}</p>
                  <span className="text-[10px] text-slate-500 mt-1 block">
                    {formatRelativeTime(notif.created_at)}
                  </span>
                </div>
              </div>

              {!notif.read && (
                <button
                  onClick={() => handleMarkRead(notif.id)}
                  className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 hover:text-white text-[11px] font-semibold flex items-center gap-1 transition-colors"
                >
                  <CheckCheck className="w-3 h-3" /> Mark Read
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
