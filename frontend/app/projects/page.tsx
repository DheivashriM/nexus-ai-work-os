"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Project, User } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { formatDate } from "@/lib/utils";
import { FolderKanban, Plus, Calendar, User as UserIcon, Lock, ShieldAlert } from "lucide-react";

export default function ProjectsPage() {
  const { user } = useAuth();
  const canCreateProject = user?.role === "ADMIN" || user?.role === "MANAGER";
  const [permissionError, setPermissionError] = useState<string | null>(null);

  const [projects, setProjects] = useState<Project[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Active Project Detail Modal State
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [projectTasks, setProjectTasks] = useState<import("@/types").Task[]>([]);
  const [editDesc, setEditDesc] = useState("");
  const [savingProj, setSavingProj] = useState(false);
  const [editSuccess, setEditSuccess] = useState(false);

  // Form State
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState("ACTIVE");
  const [priority, setPriority] = useState("MEDIUM");
  const [ownerId, setOwnerId] = useState("");

  async function loadData() {
    try {
      const [projData, userData] = await Promise.all([api.getProjects(), api.getUsers()]);
      setProjects(projData);
      setUsers(userData);
      if (userData.length > 0) setOwnerId(userData[0].id);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (activeProject) {
      setEditDesc(activeProject.description || "");
      api.getTasks({ project_id: activeProject.id })
        .then(setProjectTasks)
        .catch(() => setProjectTasks([]));
    }
  }, [activeProject?.id]);

  async function handleCreateProject(e: React.FormEvent) {
    e.preventDefault();
    if (!name || !ownerId) return;

    try {
      await api.createProject({
        name,
        description,
        status: status as any,
        priority: priority as any,
        owner_id: ownerId,
      });
      setIsModalOpen(false);
      setName("");
      setDescription("");
      loadData();
    } catch (err: any) {
      alert(err.message || "Failed to create project");
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-medium">Loading Projects...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            Projects Workspace
            <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-bold bg-slate-900 border border-slate-800 text-slate-300">
              Role: {user?.role || "MEMBER"}
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">Manage project status, roadmaps, owners, and team assignments.</p>
        </div>
        {canCreateProject ? (
          <button
            onClick={() => { setPermissionError(null); setIsModalOpen(true); }}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-semibold text-xs flex items-center gap-2 hover:opacity-95 shadow-lg shadow-emerald-500/20 transition-all self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" /> New Project
          </button>
        ) : (
          <button
            onClick={() => setPermissionError("Permission denied: Creating projects requires an ADMIN or MANAGER role. You are currently logged in as MEMBER.")}
            className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 font-medium text-xs flex items-center gap-2 hover:bg-slate-800/80 transition-all self-start sm:self-auto cursor-not-allowed"
            title="Project Creation Restricted to ADMIN / MANAGER"
          >
            <Lock className="w-3.5 h-3.5 text-amber-400" />
            <span>New Project (Requires ADMIN/MANAGER)</span>
          </button>
        )}
      </div>

      {permissionError && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium flex items-center justify-between animate-in fade-in">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{permissionError}</span>
          </div>
          <button onClick={() => setPermissionError(null)} className="text-slate-400 hover:text-white underline text-[11px]">Dismiss</button>
        </div>
      )}

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map((project) => (
          <div
            key={project.id}
            onClick={() => setActiveProject(project)}
            className="glass-card glass-card-hover rounded-xl p-6 border border-slate-800 flex flex-col justify-between space-y-4 cursor-pointer hover:border-emerald-500/40 transition-all"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <Badge variant={project.status}>{project.status}</Badge>
                <Badge variant={project.priority}>{project.priority}</Badge>
              </div>

              <h3 className="text-base font-bold text-white tracking-tight hover:text-emerald-400 transition-colors">{project.name}</h3>
              <p className="text-xs text-slate-400 mt-2 line-clamp-3 leading-relaxed">
                {project.description || "No description provided."}
              </p>
            </div>

            <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <UserIcon className="w-3.5 h-3.5 text-slate-500" />
                <span>Owner: {project.owner ? project.owner.name : "Unassigned"}</span>
              </div>
              <div className="flex items-center gap-1.5 text-slate-400">
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                <span>{formatDate(project.created_at)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Project Detail & Tasks Modal */}
      {activeProject && (
        <Modal isOpen={!!activeProject} onClose={() => setActiveProject(null)} title={activeProject.name}>
          <div className="space-y-6 text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Badge variant={activeProject.status}>{activeProject.status}</Badge>
                <Badge variant={activeProject.priority}>{activeProject.priority}</Badge>
              </div>
              <span className="text-slate-400 text-[11px]">Owner: {activeProject.owner ? activeProject.owner.name : "Unassigned"}</span>
            </div>

            {/* Editable Description */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase text-slate-400 tracking-wider">Project Description & Scope</h4>
                {editSuccess && <span className="text-[11px] text-emerald-400 font-semibold animate-pulse">Updated successfully!</span>}
              </div>
              <textarea
                rows={4}
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
                placeholder="Type project goals, requirements, or scope..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-white focus:outline-none focus:border-emerald-500 resize-none"
              />
              <button
                type="button"
                disabled={savingProj}
                onClick={async () => {
                  setSavingProj(true);
                  try {
                    const updated = await api.updateProject(activeProject.id, { description: editDesc });
                    setActiveProject(updated);
                    setEditSuccess(true);
                    setTimeout(() => setEditSuccess(false), 2000);
                    loadData();
                  } catch (err: any) {
                    alert(err.message || "Failed to update project description");
                  } finally {
                    setSavingProj(false);
                  }
                }}
                className="px-3.5 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30 font-semibold text-xs transition-colors"
              >
                {savingProj ? "Saving..." : "Save Description"}
              </button>
            </div>

            {/* Associated Project Tasks */}
            <div className="space-y-3 pt-4 border-t border-slate-800">
              <h4 className="text-xs font-bold uppercase text-slate-400 tracking-wider">
                Project Tasks ({projectTasks.length})
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1 divide-y divide-slate-800/60">
                {projectTasks.length === 0 ? (
                  <p className="text-slate-500 text-xs py-3">No tasks created under this project yet.</p>
                ) : (
                  projectTasks.map((t) => (
                    <div key={t.id} className="pt-2 flex items-center justify-between text-xs">
                      <div>
                        <span className="font-semibold text-white">{t.title}</span>
                        <div className="text-[10px] text-slate-400">Assignee: {t.assignee ? t.assignee.name : "Unassigned"}</div>
                      </div>
                      <Badge variant={t.status}>{t.status}</Badge>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* Create Project Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create New Project">
        <form onSubmit={handleCreateProject} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Project Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Payment Gateway V2"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Description</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe project objectives and scope..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="PLANNING">PLANNING</option>
                <option value="ACTIVE">ACTIVE</option>
                <option value="ON_HOLD">ON_HOLD</option>
                <option value="COMPLETED">COMPLETED</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="LOW">LOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
                <option value="URGENT">URGENT</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Project Owner</label>
            <select
              value={ownerId}
              onChange={(e) => setOwnerId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            >
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name} ({u.role})
                </option>
              ))}
            </select>
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
              className="px-4 py-2 rounded-lg bg-emerald-500 text-slate-950 font-bold text-xs hover:bg-emerald-400 shadow-md shadow-emerald-500/20"
            >
              Create Project
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
