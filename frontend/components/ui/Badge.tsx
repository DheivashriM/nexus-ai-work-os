import React from "react";
import { cn, getStatusColor } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: string;
  className?: string;
}

export function Badge({ children, variant, className }: BadgeProps) {
  const colorClass = variant ? getStatusColor(variant) : "bg-slate-800 text-slate-300 border-slate-700";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors",
        colorClass,
        className
      )}
    >
      {children}
    </span>
  );
}
