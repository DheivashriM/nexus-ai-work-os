import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Parses an ISO date string or Date object reliably into a local Date instance.
 * Normalizes ISO strings without timezone offsets (e.g. "2026-09-08T12:00:00") as UTC ("Z").
 */
export function parseDate(dateInput?: string | Date | null): Date {
  if (!dateInput) return new Date();
  if (dateInput instanceof Date) return dateInput;
  let str = String(dateInput).trim();
  if (!str) return new Date();
  
  // If ISO string lacks 'Z' or timezone offset, append 'Z' so JS treats as UTC
  if (str.includes("T") && !str.endsWith("Z") && !/[+-]\d{2}:?\d{2}$/.test(str)) {
    str += "Z";
  } else if (!str.includes("T") && /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(str)) {
    str = str.replace(" ", "T") + "Z";
  }
  const d = new Date(str);
  return isNaN(d.getTime()) ? new Date() : d;
}

export function formatDate(dateInput?: string | Date | null): string {
  if (!dateInput) return "N/A";
  const date = parseDate(dateInput);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric"
  });
}

export function formatTime(dateInput?: string | Date | null): string {
  if (!dateInput) return "";
  const date = parseDate(dateInput);
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit"
  });
}

export function formatDateTime(dateInput?: string | Date | null): string {
  if (!dateInput) return "N/A";
  const date = parseDate(dateInput);
  return `${formatDate(date)} ${formatTime(date)}`;
}

export function formatRelativeTime(dateInput?: string | Date | null): string {
  if (!dateInput) return "Just now";
  const date = parseDate(dateInput);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 10) return "Just now";
  if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
  return formatDate(date);
}

export function getStatusColor(status: string): string {
  switch (status.toUpperCase()) {
    case "COMPLETED":
    case "RESOLVED":
    case "ACTIVE":
      return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    case "IN_PROGRESS":
      return "bg-cyan-500/10 text-cyan-400 border-cyan-500/20";
    case "IN_REVIEW":
      return "bg-purple-500/10 text-purple-400 border-purple-500/20";
    case "TODO":
    case "PLANNING":
      return "bg-slate-500/10 text-slate-300 border-slate-500/20";
    case "BLOCKED":
    case "OPEN":
    case "CRITICAL":
      return "bg-rose-500/10 text-rose-400 border-rose-500/20";
    case "HIGH":
    case "URGENT":
      return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    default:
      return "bg-slate-500/10 text-slate-400 border-slate-500/20";
  }
}
