"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { User, Task } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Users, Plus, ShieldCheck, CheckCircle2, Clock, Lock, ShieldAlert } from "lucide-react";

export default function TeamPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN";
  const [permError, setPermError] = useState<string | null>(null);

  const [users, setUsers] = useState<User[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // New Member State
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("MEMBER");
  const [password, setPassword] = useState("");

  async function loadData() {
    try {
      const [userRes, taskRes] = await Promise.all([api.getUsers(), api.getTasks()]);
      setUsers(userRes);
      setTasks(taskRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleAddUser(e: React.FormEvent) {
    e.preventDefault();
    if (!name || !email) return;

    try {
      await api.createUser({
        name,
        email,
        role: role as any,
        password,
        status: "ACTIVE",
      });
      setIsModalOpen(false);
      setName("");
      setEmail("");
      setPassword("");
      loadData();
    } catch (err: any) {
      alert(err.message || "Failed to create user");
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-medium">Loading Team Roster...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            Team Workload & Roster
            <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-bold bg-slate-900 border border-slate-800 text-slate-300">
              Role: {user?.role || "MEMBER"}
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">Manage team members, roles, permissions, and active workload distribution.</p>
        </div>
        {isAdmin ? (
          <button
            onClick={() => { setPermError(null); setIsModalOpen(true); }}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-semibold text-xs flex items-center gap-2 hover:opacity-95 shadow-lg shadow-emerald-500/20 transition-all self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" /> Add Team Member
          </button>
        ) : (
          <button
            onClick={() => setPermError("Permission denied: Adding new team members and managing roles requires Platform ADMIN privileges.")}
            className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 font-medium text-xs flex items-center gap-2 hover:bg-slate-800/80 transition-all self-start sm:self-auto cursor-not-allowed"
          >
            <Lock className="w-3.5 h-3.5 text-amber-400" />
            <span>Add Member (Requires ADMIN)</span>
          </button>
        )}
      </div>

      {permError && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium flex items-center justify-between animate-in fade-in">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{permError}</span>
          </div>
          <button onClick={() => setPermError(null)} className="text-slate-400 hover:text-white underline text-[11px]">Dismiss</button>
        </div>
      )}

      {/* Team Member Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {users.map((user) => {
          const userTasks = tasks.filter((t) => t.assignee_id === user.id);
          const activeTasks = userTasks.filter((t) => t.status !== "COMPLETED").length;
          const completedTasks = userTasks.filter((t) => t.status === "COMPLETED").length;

          return (
            <div
              key={user.id}
              className="glass-card glass-card-hover rounded-xl p-6 border border-slate-800 space-y-4"
            >
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-full bg-slate-800 text-emerald-400 font-bold text-sm flex items-center justify-center border border-slate-700">
                  {user.name.split(" ").map((n) => n[0]).join("")}
                </div>
                <Badge variant={user.role}>{user.role}</Badge>
              </div>

              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-1.5">
                  {user.name}
                  {user.role === "ADMIN" && <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">{user.email}</p>
              </div>

              <div className="pt-3 border-t border-slate-800/80 grid grid-cols-2 gap-4 text-xs">
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/60">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block">Active Workload</span>
                  <span className="text-sm font-bold text-cyan-400 mt-0.5 block">{activeTasks} Active Tasks</span>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/60">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block">Completed</span>
                  <span className="text-sm font-bold text-emerald-400 mt-0.5 block">{completedTasks} Tasks</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Add User Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Add Team Member">
        <form onSubmit={handleAddUser} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Full Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Maya Lin"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="maya@aiworkspace.com"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="MEMBER">MEMBER</option>
                <option value="MANAGER">MANAGER</option>
                <option value="ADMIN">ADMIN</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Initial Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Set a temporary password"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-emerald-500 text-slate-950 font-bold text-xs hover:bg-emerald-400"
            >
              Add Member
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
