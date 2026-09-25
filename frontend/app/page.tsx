"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Project, Task, User, Blocker, Activity } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { formatDate, formatRelativeTime, parseDate } from "@/lib/utils";
import {
  FolderKanban,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Users,
  Activity as ActivityIcon,
  Plus,
  ArrowUpRight,
  ShieldAlert,
  ShieldCheck,
  Briefcase,
  UserCheck,
  Bot,
  MessageSquare,
  AlertCircle
} from "lucide-react";
import Link from "next/link";

export default function Dashboard() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [blockers, setBlockers] = useState<Blocker[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [projRes, taskRes, blockRes, userRes, actRes] = await Promise.all([
          api.getProjects(),
          api.getTasks(),
          api.getBlockers(),
          api.getUsers(),
          api.getActivities(15),
        ]);
        setProjects(projRes);
        setTasks(taskRes);
        setBlockers(blockRes);
        setUsers(userRes);
        setActivities(actRes);
      } catch (err) {
        console.error("Error loading dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-medium">Loading Workspace Dashboard...</span>
        </div>
      </div>
    );
  }

  const role = user?.role || "MEMBER";

  // Filtered metrics
  const totalProjects = projects.length;
  const activeProjects = projects.filter((p) => p.status === "ACTIVE").length;
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter((t) => t.status === "COMPLETED").length;
  const openBlockers = blockers.filter((b) => b.status === "OPEN");

  // Member-specific metrics
  const myTasks = tasks.filter((t) => t.assignee_id === user?.id);
  const myActiveTasks = myTasks.filter((t) => t.status !== "COMPLETED");
  const myCompletedTasks = myTasks.filter((t) => t.status === "COMPLETED");
  const now = new Date();
  const myOverdueTasks = myTasks.filter(
    (t) => t.due_date && parseDate(t.due_date) < now && t.status !== "COMPLETED"
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Dynamic Header according to Role */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800 p-6 rounded-2xl backdrop-blur-xl shadow-xl">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-500 to-cyan-500 text-slate-950 font-extrabold text-base flex items-center justify-center shadow-lg shadow-emerald-500/20">
            {user?.name ? user.name.slice(0, 2).toUpperCase() : "US"}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white tracking-tight">
                Welcome back, {user?.name || "User"}
              </h1>
              <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                {role} View
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {role === "ADMIN" && "System Administrator Control Panel • Full Workspace Oversight & Audit Feed"}
              {role === "MANAGER" && "Project Management Dashboard • Progress Tracking, Task Allocations & Blocker Resolution"}
              {role === "MEMBER" && "Individual Contributor Hub • My Active Assignments, Deadlines & Workspace Updates"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {role === "ADMIN" && (
            <Link
              href="/team"
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs flex items-center gap-2 border border-slate-700 transition-all"
            >
              <Users className="w-4 h-4 text-emerald-400" /> Manage Team
            </Link>
          )}
          <Link
            href="/tasks"
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-bold text-xs flex items-center gap-2 hover:opacity-95 shadow-lg shadow-emerald-500/20 transition-all"
          >
            <Plus className="w-4 h-4" /> Create Task
          </Link>
        </div>
      </div>

      {/* Critical Blocker Alert Banner */}
      {openBlockers.length > 0 && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-2xl p-4 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400 mt-0.5">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-rose-300">
                {openBlockers.length} Active Blocker{openBlockers.length > 1 ? "s" : ""} Requiring Attention
              </h3>
              <p className="text-xs text-rose-200/70 mt-1 max-w-2xl">
                {openBlockers[0].description}
              </p>
            </div>
          </div>
          <Link
            href="/tasks"
            className="px-3.5 py-2 rounded-xl bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 text-xs font-bold whitespace-nowrap border border-rose-500/30 transition-colors"
          >
            View Blockers
          </Link>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 1. ADMINISTRATOR DASHBOARD VIEW */}
      {/* ========================================================================= */}
      {role === "ADMIN" && (
        <>
          {/* Admin KPI Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="glass-card rounded-2xl p-5 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">Total Workspace Projects</span>
                <FolderKanban className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="text-2xl font-bold text-white">{totalProjects}</div>
              <div className="text-[11px] text-cyan-400 mt-1 font-medium">{activeProjects} Active Projects</div>
            </div>

            <div className="glass-card rounded-2xl p-5 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">Workspace Completion</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-white">{completedTasks} <span className="text-xs font-normal text-slate-400">/ {totalTasks}</span></div>
              <div className="text-[11px] text-emerald-400 mt-1 font-medium">
                {totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0}% Completion Rate
              </div>
            </div>

            <div className="glass-card rounded-2xl p-5 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">Open System Blockers</span>
                <AlertTriangle className="w-4 h-4 text-rose-400" />
              </div>
              <div className="text-2xl font-bold text-white">{openBlockers.length}</div>
              <div className="text-[11px] text-rose-400 mt-1 font-medium">Requires Management Action</div>
            </div>

            <div className="glass-card rounded-2xl p-5 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">Registered Team Members</span>
                <Users className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-2xl font-bold text-white">{users.length}</div>
              <div className="text-[11px] text-purple-400 mt-1 font-medium">Active Accounts</div>
            </div>
          </div>

          {/* Admin Main Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <FolderKanban className="w-4 h-4 text-emerald-400" /> All Active Projects
                </h2>
                <Link href="/projects" className="text-xs text-slate-400 hover:text-white flex items-center gap-1 font-semibold">
                  Manage Projects <ArrowUpRight className="w-3 h-3" />
                </Link>
              </div>

              {projects.length === 0 ? (
                <div className="text-center py-10 border border-dashed border-slate-800 rounded-xl">
                  <p className="text-xs text-slate-400">No projects created yet.</p>
                  <Link href="/projects" className="mt-2 inline-block text-xs text-emerald-400 font-semibold hover:underline">
                    + Create First Project
                  </Link>
                </div>
              ) : (
                <div className="divide-y divide-slate-800/80">
                  {projects.map((p) => (
                    <div key={p.id} className="py-3.5 flex items-center justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-bold text-white">{p.name}</h3>
                          <Badge variant={p.status}>{p.status}</Badge>
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{p.description || "No description."}</p>
                      </div>
                      <Badge variant={p.priority}>{p.priority}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Audit Log Stream */}
            <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <ActivityIcon className="w-4 h-4 text-cyan-400" /> System Audit Stream
              </h2>
              {activities.length === 0 ? (
                <p className="text-xs text-slate-500 py-6 text-center">No system activities logged yet.</p>
              ) : (
                <div className="space-y-3.5">
                  {activities.slice(0, 7).map((act) => (
                    <div key={act.id} className="flex items-start gap-3 text-xs">
                      <div className="w-2 h-2 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
                      <div>
                        <p className="text-slate-300 font-medium">{act.description}</p>
                        <span className="text-[10px] text-slate-500 block mt-0.5">
                          {formatRelativeTime(act.created_at)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* ========================================================================= */}
      {/* 2. PROJECT MANAGER DASHBOARD VIEW */}
      {/* ========================================================================= */}
      {role === "MANAGER" && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="glass-card rounded-2xl p-5 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">Managed Projects</span>
                <Briefcase className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="text-2xl font-bold text-white">{totalProjects}</div>
              <div className="text-[11px] text-cyan-400 mt-1 font-medium">{activeProjects} Active</div>
            </div>

            <div className="glass-card rounded-2xl p-5 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">Task Progress</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-white">{completedTasks} <span className="text-xs text-slate-400">/ {totalTasks}</span></div>
              <div className="text-[11px] text-emerald-400 mt-1 font-medium">Completed Work</div>
            </div>

            <div className="glass-card rounded-2xl p-5 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">Team Blockers</span>
                <AlertTriangle className="w-4 h-4 text-rose-400" />
              </div>
              <div className="text-2xl font-bold text-white">{openBlockers.length}</div>
              <div className="text-[11px] text-rose-400 mt-1 font-medium">Clearance Required</div>
            </div>

            <div className="glass-card rounded-2xl p-5 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">Team Members</span>
                <Users className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-2xl font-bold text-white">{users.length}</div>
              <div className="text-[11px] text-purple-400 mt-1 font-medium font-mono">Assigned Roster</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Clock className="w-4 h-4 text-emerald-400" /> Active Tasks Queue
                </h2>
                <Link href="/tasks" className="text-xs text-slate-400 hover:text-white flex items-center gap-1 font-semibold">
                  All Tasks <ArrowUpRight className="w-3 h-3" />
                </Link>
              </div>

              {tasks.length === 0 ? (
                <p className="text-xs text-slate-400 py-6 text-center">No tasks assigned or created yet.</p>
              ) : (
                <div className="divide-y divide-slate-800/80">
                  {tasks.slice(0, 6).map((task) => (
                    <div key={task.id} className="py-3 flex items-center justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-slate-200 truncate">{task.title}</span>
                          <Badge variant={task.status}>{task.status}</Badge>
                        </div>
                        <p className="text-xs text-slate-400 mt-1">
                          Assignee: <strong className="text-slate-300">{task.assignee ? task.assignee.name : "Unassigned"}</strong> • Due: {formatDate(task.due_date)}
                        </p>
                      </div>
                      <Badge variant={task.priority}>{task.priority}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Team Roster Workload */}
            <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-cyan-400" /> Workload Allocation
              </h2>
              {users.length === 0 ? (
                <p className="text-xs text-slate-500 py-6 text-center">No members in workspace.</p>
              ) : (
                <div className="space-y-3">
                  {users.map((u) => {
                    const count = tasks.filter((t) => t.assignee_id === u.id && t.status !== "COMPLETED").length;
                    return (
                      <div key={u.id} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                        <div>
                          <p className="text-xs font-bold text-white">{u.name}</p>
                          <p className="text-[10px] text-slate-400 font-mono">{u.role}</p>
                        </div>
                        <span className="text-xs font-semibold text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-lg border border-cyan-500/20">
                          {count} Active Tasks
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* ========================================================================= */}
      {/* 3. TEAM MEMBER / CONTRIBUTOR DASHBOARD VIEW */}
      {/* ========================================================================= */}
      {role === "MEMBER" && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="glass-card rounded-2xl p-5 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">My Active Tasks</span>
                <Clock className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="text-2xl font-bold text-white">{myActiveTasks.length}</div>
              <div className="text-[11px] text-cyan-400 mt-1 font-medium">Assigned to Me</div>
            </div>

            <div className="glass-card rounded-2xl p-5 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">My Completed</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-white">{myCompletedTasks.length}</div>
              <div className="text-[11px] text-emerald-400 mt-1 font-medium">Finished Tasks</div>
            </div>

            <div className="glass-card rounded-2xl p-5 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">Overdue Items</span>
                <AlertCircle className="w-4 h-4 text-rose-400" />
              </div>
              <div className="text-2xl font-bold text-white">{myOverdueTasks.length}</div>
              <div className="text-[11px] text-rose-400 mt-1 font-medium">Requires Completion</div>
            </div>

            <div className="glass-card rounded-2xl p-5 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider">Team Direct Chat</span>
                <MessageSquare className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-2xl font-bold text-white">{users.length - 1}</div>
              <div className="text-[11px] text-purple-400 mt-1 font-medium">Available Teammates</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <UserCheck className="w-4 h-4 text-emerald-400" /> My Assigned Tasks
                </h2>
                <Link href="/tasks" className="text-xs text-slate-400 hover:text-white flex items-center gap-1 font-semibold">
                  Open Tasks Board <ArrowUpRight className="w-3 h-3" />
                </Link>
              </div>

              {myTasks.length === 0 ? (
                <div className="text-center py-10 border border-dashed border-slate-800 rounded-xl">
                  <p className="text-xs text-slate-400">You currently have no tasks assigned to you.</p>
                </div>
              ) : (
                <div className="divide-y divide-slate-800/80">
                  {myTasks.map((t) => (
                    <div key={t.id} className="py-3 flex items-center justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-semibold text-slate-200">{t.title}</h3>
                          <Badge variant={t.status}>{t.status}</Badge>
                        </div>
                        <p className="text-xs text-slate-400 mt-1">Due: {formatDate(t.due_date)}</p>
                      </div>
                      <Badge variant={t.priority}>{t.priority}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Quick Actions & AI Assistant Box */}
            <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4 flex flex-col justify-between">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2 mb-2">
                  <Bot className="w-4 h-4 text-cyan-400" /> AI Co-Pilot Assistant
                </h2>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Need help resolving a task or drafting an update? Your AI Copilot can parse tasks, file blockers, and manage communications.
                </p>
              </div>

              <div className="space-y-2 pt-4">
                <Link
                  href="/ai-assistant"
                  className="w-full bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-bold text-xs py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 shadow-md shadow-emerald-500/20 transition-all hover:opacity-90"
                >
                  Open AI Workspace <ArrowUpRight className="w-3 h-3" />
                </Link>
                <Link
                  href="/messages"
                  className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 border border-slate-700 transition-all"
                >
                  <MessageSquare className="w-3.5 h-3.5 text-emerald-400" /> Chat with Team
                </Link>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
