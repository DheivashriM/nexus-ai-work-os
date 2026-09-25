"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FolderKanban,
  CheckSquare,
  Users,
  Calendar,
  Mail,
  Bell,
  Bot,
  Settings,
  Sparkles,
  MessageSquare
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Direct & Group Chat", href: "/messages", icon: MessageSquare, tag: "Live WS" },
  { name: "WhatsApp Inbox", href: "/whatsapp", icon: MessageSquare, tag: "External" },
  { name: "Projects", href: "/projects", icon: FolderKanban },
  { name: "Tasks", href: "/tasks", icon: CheckSquare },
  { name: "Team", href: "/team", icon: Users },
  { name: "Calendar & Meetings", href: "/meetings", icon: Calendar },
  { name: "Smart Email Inbox", href: "/emails", icon: Mail, tag: "AI Urgency" },
  { name: "Notifications", href: "/notifications", icon: Bell },
  { name: "AI Assistant", href: "/ai-assistant", icon: Bot, tag: "Phase 2" },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-950/80 border-r border-slate-800 flex flex-col justify-between h-screen sticky top-0 backdrop-blur-xl z-30">
      <div>
        {/* Brand Logo Header */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-800/60">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Sparkles className="w-5 h-5 text-slate-950 font-bold" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-white leading-none">Nexus AI OS</h1>
            <p className="text-xs text-slate-400 mt-1 font-medium">Work Operating System</p>
          </div>
        </div>

        {/* Navigation items */}
        <nav className="p-3 space-y-1.5 mt-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group",
                  isActive
                    ? "bg-slate-800/90 text-white shadow-sm border border-slate-700/60"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                )}
              >
                <div className="flex items-center gap-3">
                  <Icon className={cn("w-4 h-4 transition-colors", isActive ? "text-emerald-400" : "text-slate-400 group-hover:text-slate-200")} />
                  <span>{item.name}</span>
                </div>
                {item.tag && (
                  <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    {item.tag}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Info Badge */}
      <div className="p-4 border-t border-slate-800/60">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3 text-xs">
          <div className="flex items-center justify-between font-semibold text-slate-200">
            <span>Phase 1 Foundation</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          </div>
          <p className="text-[11px] text-slate-400 mt-1">PostgreSQL & FastAPI Active</p>
        </div>
      </div>
    </aside>
  );
}
