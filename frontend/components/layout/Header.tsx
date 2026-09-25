"use client";

import React, { useEffect, useState } from "react";
import { Bell, Search, ShieldCheck, LogOut, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { Notification } from "@/types";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import Link from "next/link";

export function Header() {
  const { user, logout } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const unreadCount = notifications.filter((n) => !n.read).length;

  useEffect(() => {
    if (user) {
      api.getNotifications()
        .then(setNotifications)
        .catch(() => {});
    }
  }, [user]);

  const initials = user?.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "US";

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/40 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Search Input */}
      <div className="relative w-72">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Search projects, tasks, team..."
          className="w-full bg-slate-900/90 border border-slate-800 rounded-xl pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 transition-colors"
        />
      </div>

      {/* Action Header Items */}
      <div className="flex items-center gap-3">
        <Link
          href="/notifications"
          className="relative p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-900 border border-transparent hover:border-slate-800 transition-all"
        >
          <Bell className="w-4 h-4" />
          {unreadCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-emerald-500 ring-4 ring-slate-950" />
          )}
        </Link>

        {/* User Profile Pill */}
        {user ? (
          <div className="flex items-center gap-3 pl-3 border-l border-slate-800">
            <Link
              href="/login"
              className="flex items-center gap-2.5 group hover:opacity-90 transition-all"
              title="Manage account"
            >
              <div className={cn(
                "w-8 h-8 rounded-full border flex items-center justify-center font-bold text-xs transition-colors",
                user.role === "ADMIN" ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40" :
                user.role === "MANAGER" ? "bg-cyan-500/20 text-cyan-400 border-cyan-500/40" :
                "bg-purple-500/20 text-purple-400 border-purple-500/40"
              )}>
                {initials}
              </div>
              <div className="text-left hidden sm:block">
                <div className="text-xs font-semibold text-white flex items-center gap-1 group-hover:text-emerald-400 transition-colors">
                  {user.name}
                  <ShieldCheck className="w-3 h-3 text-emerald-400 inline" />
                </div>
                <div className="text-[10px] font-mono flex items-center gap-1">
                  <span className={cn(
                    "px-1.5 py-0.2 rounded text-[9px] font-bold uppercase",
                    user.role === "ADMIN" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                    user.role === "MANAGER" ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" :
                    "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                  )}>
                    {user.role}
                  </span>
                </div>
              </div>
            </Link>

            <button
              onClick={logout}
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg border border-transparent hover:border-rose-500/20 transition-all ml-1"
              title="Sign Out"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <Link
            href="/login"
            className="text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-3.5 py-1.5 rounded-xl transition-all shadow-md shadow-emerald-500/20"
          >
            Sign In
          </Link>
        )}
      </div>
    </header>
  );
}
