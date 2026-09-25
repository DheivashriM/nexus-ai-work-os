"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Task, Project, User } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { formatDate } from "@/lib/utils";
import {
  CheckSquare,
  Plus,
  Filter,
  MessageSquare,
  AlertTriangle,
  UserCheck,
  Calendar,
  X
} from "lucide-react";

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters State
  const [selectedProject, setSelectedProject] = useState("");
  const [selectedAssignee, setSelectedAssignee] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");
  const [selectedPriority, setSelectedPriority] = useState("");

  // Create Task Modal State
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [taskTitle, setTaskTitle] = useState("");
  const [taskDesc, setTaskDesc] = useState("");
  const [projectId, setProjectId] = useState("");
  const [assigneeId, setAssigneeId] = useState("");
  const [taskStatus, setTaskStatus] = useState("TODO");
  const [taskPriority, setTaskPriority] = useState("MEDIUM");
  const [taskDueDate, setTaskDueDate] = useState("");

  // Selected Task Drawer State
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [editDesc, setEditDesc] = useState("");
  const [savingDesc, setSavingDesc] = useState(false);
  const [editSuccess, setEditSuccess] = useState(false);
  const [commentText, setCommentText] = useState("");
  const [isBlockerModalOpen, setIsBlockerModalOpen] = useState(false);
  const [blockerDesc, setBlockerDesc] = useState("");
  const [blockerSeverity, setBlockerSeverity] = useState("HIGH");

  useEffect(() => {
    if (activeTask) {
      setEditDesc(activeTask.description || "");
    }
  }, [activeTask?.id]);

  async function loadData() {
    try {
      const [taskRes, projRes, userRes] = await Promise.all([
        api.getTasks({
          project_id: selectedProject || undefined,
          assignee_id: selectedAssignee || undefined,
          status: selectedStatus || undefined,
          priority: selectedPriority || undefined,
        }),
        api.getProjects(),
        api.getUsers(),
      ]);
      setTasks(taskRes);
      setProjects(projRes);
      setUsers(userRes);
      if (projRes.length > 0 && !projectId) setProjectId(projRes[0].id);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [selectedProject, selectedAssignee, selectedStatus, selectedPriority]);

  async function handleCreateTask(e: React.FormEvent) {
    e.preventDefault();
    if (!taskTitle || !projectId) return;

    try {
      await api.createTask({
        project_id: projectId,
        title: taskTitle,
        description: taskDesc,
        status: taskStatus as any,
        priority: taskPriority as any,
        assignee_id: assigneeId || undefined,
        due_date: taskDueDate ? new Date(taskDueDate).toISOString() : undefined
      });
      setIsTaskModalOpen(false);
      setTaskTitle("");
      setTaskDesc("");
      setTaskDueDate("");
      loadData();
    } catch (err: any) {
      alert(err.message || "Failed to create task");
    }
  }

  async function handleStatusChange(taskId: string, newStatus: string) {
    try {
      await api.updateTask(taskId, { status: newStatus as any });
      loadData();
      if (activeTask && activeTask.id === taskId) {
        setActiveTask({ ...activeTask, status: newStatus as any });
      }
    } catch (err: any) {
      alert(err.message || "Failed to update task status");
    }
  }

  async function handleAddComment(e: React.FormEvent) {
    e.preventDefault();
    if (!activeTask || !commentText.trim()) return;

    try {
      await api.addTaskComment(activeTask.id, commentText);
      setCommentText("");
      const updated = await api.getTaskById(activeTask.id);
      setActiveTask(updated);
      loadData();
    } catch (err: any) {
      alert(err.message || "Failed to post comment");
    }
  }

  async function handleFileBlocker(e: React.FormEvent) {
    e.preventDefault();
    if (!activeTask || !blockerDesc.trim()) return;

    try {
      await api.createBlocker({
        task_id: activeTask.id,
        description: blockerDesc,
        severity: blockerSeverity,
      });
      setIsBlockerModalOpen(false);
      setBlockerDesc("");
      const updated = await api.getTaskById(activeTask.id);
      setActiveTask(updated);
      loadData();
    } catch (err: any) {
      alert(err.message || "Failed to file blocker");
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-medium">Loading Tasks...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Task Management</h1>
          <p className="text-xs text-slate-400 mt-1">Track task assignments, statuses, blockers, and comment threads.</p>
        </div>
        <button
          onClick={() => setIsTaskModalOpen(true)}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-semibold text-xs flex items-center gap-2 hover:opacity-95 shadow-lg shadow-emerald-500/20 transition-all self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" /> Create Task
        </button>
      </div>

      {/* Filter Controls Bar */}
      <div className="glass-card rounded-xl p-4 border border-slate-800 flex flex-wrap items-center gap-4 text-xs">
        <div className="flex items-center gap-2 text-slate-400 font-semibold">
          <Filter className="w-3.5 h-3.5 text-emerald-400" /> Filters:
        </div>

        <select
          value={selectedProject}
          onChange={(e) => setSelectedProject(e.target.value)}
          className="bg-slate-900 border border-slate-800 text-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:border-emerald-500"
        >
          <option value="">All Projects</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>

        <select
          value={selectedAssignee}
          onChange={(e) => setSelectedAssignee(e.target.value)}
          className="bg-slate-900 border border-slate-800 text-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:border-emerald-500"
        >
          <option value="">All Assignees</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>{u.name}</option>
          ))}
        </select>

        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="bg-slate-900 border border-slate-800 text-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:border-emerald-500"
        >
          <option value="">All Statuses</option>
          <option value="TODO">TODO</option>
          <option value="IN_PROGRESS">IN_PROGRESS</option>
          <option value="IN_REVIEW">IN_REVIEW</option>
          <option value="COMPLETED">COMPLETED</option>
          <option value="BLOCKED">BLOCKED</option>
        </select>

        <select
          value={selectedPriority}
          onChange={(e) => setSelectedPriority(e.target.value)}
          className="bg-slate-900 border border-slate-800 text-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:border-emerald-500"
        >
          <option value="">All Priorities</option>
          <option value="LOW">LOW</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="HIGH">HIGH</option>
          <option value="URGENT">URGENT</option>
        </select>
      </div>

      {/* Task List Table */}
      <div className="glass-card rounded-xl border border-slate-800 overflow-hidden">
        <div className="divide-y divide-slate-800/80">
          {tasks.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              No tasks matching selected filter criteria.
            </div>
          ) : (
            tasks.map((task) => (
              <div
                key={task.id}
                onClick={() => setActiveTask(task)}
                className="p-4 hover:bg-slate-900/60 cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 transition-colors"
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-bold text-white hover:text-emerald-400 transition-colors truncate">
                      {task.title}
                    </span>
                    <Badge variant={task.status}>{task.status}</Badge>
                    <Badge variant={task.priority}>{task.priority}</Badge>
                  </div>
                  <p className="text-xs text-slate-400 line-clamp-1">
                    {task.description || "No task description."}
                  </p>
                </div>

                <div className="flex items-center gap-6 text-xs text-slate-400 shrink-0">
                  <div className="flex items-center gap-2">
                    <UserCheck className="w-3.5 h-3.5 text-slate-500" />
                    <span>{task.assignee ? task.assignee.name : "Unassigned"}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <MessageSquare className="w-3.5 h-3.5 text-slate-500" />
                    <span>{task.comments ? task.comments.length : 0}</span>
                  </div>
                  <select
                    value={task.status}
                    onClick={(e) => e.stopPropagation()}
                    onChange={(e) => handleStatusChange(task.id, e.target.value)}
                    className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-[11px] font-semibold text-slate-300 focus:outline-none"
                  >
                    <option value="TODO">TODO</option>
                    <option value="IN_PROGRESS">IN_PROGRESS</option>
                    <option value="IN_REVIEW">IN_REVIEW</option>
                    <option value="COMPLETED">COMPLETED</option>
                    <option value="BLOCKED">BLOCKED</option>
                  </select>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Create Task Modal */}
      <Modal isOpen={isTaskModalOpen} onClose={() => setIsTaskModalOpen(false)} title="Create New Task">
        <form onSubmit={handleCreateTask} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Task Title</label>
            <input
              type="text"
              required
              value={taskTitle}
              onChange={(e) => setTaskTitle(e.target.value)}
              placeholder="e.g. Implement OAuth Auth Middleware"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Project</label>
            <select
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Description</label>
            <textarea
              rows={3}
              value={taskDesc}
              onChange={(e) => setTaskDesc(e.target.value)}
              placeholder="Task details and requirement specifications..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Status</label>
              <select
                value={taskStatus}
                onChange={(e) => setTaskStatus(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="TODO">TODO</option>
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="IN_REVIEW">IN_REVIEW</option>
                <option value="COMPLETED">COMPLETED</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Priority</label>
              <select
                value={taskPriority}
                onChange={(e) => setTaskPriority(e.target.value)}
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
            <label className="block text-xs font-semibold text-slate-300 mb-1">Assignee</label>
            <select
              value={assigneeId}
              onChange={(e) => setAssigneeId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="">Unassigned</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>{u.name} ({u.role})</option>
              ))}
            </select>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsTaskModalOpen(false)}
              className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-emerald-500 text-slate-950 font-bold text-xs hover:bg-emerald-400"
            >
              Create Task
            </button>
          </div>
        </form>
      </Modal>

      {/* Task Detail & Comments Modal */}
      {activeTask && (
        <Modal isOpen={!!activeTask} onClose={() => setActiveTask(null)} title={activeTask.title}>
          <div className="space-y-6 text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant={activeTask.status}>{activeTask.status}</Badge>
                <Badge variant={activeTask.priority}>{activeTask.priority}</Badge>
              </div>
              <button
                onClick={() => setIsBlockerModalOpen(true)}
                className="px-3 py-1.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 font-semibold flex items-center gap-1.5 transition-colors"
              >
                <AlertTriangle className="w-3.5 h-3.5" /> Report Blocker
              </button>
            </div>

            {/* Assignee Selection */}
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-2">
              <label className="block text-[11px] font-semibold text-slate-400">Assigned Team Member</label>
              <select
                value={activeTask.assignee?.id || ""}
                onChange={async (e) => {
                  const newAssigneeId = e.target.value;
                  try {
                    const updated = await api.assignTask(activeTask.id, newAssigneeId || undefined);
                    setActiveTask(updated);
                    loadData();
                  } catch (err: any) {
                    alert(err.message || "Failed to reassign task");
                  }
                }}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="">Unassigned</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name} ({u.role})
                  </option>
                ))}
              </select>
            </div>

            {/* Editable Description */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase text-slate-400 tracking-wider">Description</h4>
                {editSuccess && <span className="text-[11px] text-emerald-400 font-semibold animate-pulse">Saved successfully!</span>}
              </div>
              <textarea
                rows={4}
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
                placeholder="Type task description or requirements here..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-white focus:outline-none focus:border-emerald-500 resize-none"
              />
              <button
                type="button"
                disabled={savingDesc}
                onClick={async () => {
                  setSavingDesc(true);
                  try {
                    const updated = await api.updateTask(activeTask.id, { description: editDesc });
                    setActiveTask(updated);
                    setEditSuccess(true);
                    setTimeout(() => setEditSuccess(false), 2000);
                    loadData();
                  } catch (err: any) {
                    alert(err.message || "Failed to update description");
                  } finally {
                    setSavingDesc(false);
                  }
                }}
                className="px-3.5 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30 font-semibold text-xs transition-colors"
              >
                {savingDesc ? "Saving..." : "Save Description"}
              </button>
            </div>

            {/* Comment Stream */}
            <div className="space-y-3 pt-4 border-t border-slate-800">
              <h4 className="text-xs font-bold uppercase text-slate-400 tracking-wider">
                Comments ({activeTask.comments ? activeTask.comments.length : 0})
              </h4>

              <div className="space-y-3 max-h-48 overflow-y-auto pr-1">
                {activeTask.comments && activeTask.comments.map((comment) => (
                  <div key={comment.id} className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between text-slate-400">
                      <span className="font-semibold text-slate-200">{comment.user ? comment.user.name : "Team Member"}</span>
                      <span className="text-[10px]">{formatDate(comment.created_at)}</span>
                    </div>
                    <p className="text-slate-300">{comment.content}</p>
                  </div>
                ))}
              </div>

              <form onSubmit={handleAddComment} className="flex gap-2">
                <input
                  type="text"
                  placeholder="Write a comment..."
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-500 text-slate-950 font-bold hover:bg-emerald-400"
                >
                  Post
                </button>
              </form>
            </div>
          </div>
        </Modal>
      )}

      {/* File Blocker Modal */}
      <Modal isOpen={isBlockerModalOpen} onClose={() => setIsBlockerModalOpen(false)} title="Report Task Blocker">
        <form onSubmit={handleFileBlocker} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Blocker Description</label>
            <textarea
              rows={3}
              required
              value={blockerDesc}
              onChange={(e) => setBlockerDesc(e.target.value)}
              placeholder="Describe the issue blocking progress (e.g. Missing API credentials)..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-rose-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Severity</label>
            <select
              value={blockerSeverity}
              onChange={(e) => setBlockerSeverity(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white focus:outline-none focus:border-rose-500"
            >
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsBlockerModalOpen(false)}
              className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-rose-500 text-white font-bold text-xs hover:bg-rose-600"
            >
              Submit Blocker
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
