"use client";

import React, { useState } from "react";
import { Meeting, User } from "@/types";
import { Badge } from "@/components/ui/Badge";
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  Clock,
  Video,
  Users,
  ExternalLink,
  Copy,
  Check,
  Plus,
  Grid,
  List,
  Sparkles
} from "lucide-react";

interface CalendarViewProps {
  meetings: Meeting[];
  users: User[];
  onScheduleForDate?: (dateStr: string) => void;
  onOpenScheduleModal?: () => void;
}

export function CalendarView({
  meetings,
  users,
  onScheduleForDate,
  onOpenScheduleModal
}: CalendarViewProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [viewMode, setViewMode] = useState<"month" | "list">("month");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // Helper to format Date to YYYY-MM-DD string
  const formatDateKey = (d: Date) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  };

  // Group meetings by date key "YYYY-MM-DD"
  const meetingsByDate: Record<string, Meeting[]> = {};
  meetings.forEach((m) => {
    try {
      const d = new Date(m.start_time);
      const key = formatDateKey(d);
      if (!meetingsByDate[key]) {
        meetingsByDate[key] = [];
      }
      meetingsByDate[key].push(m);
    } catch (e) {
      console.error("Invalid meeting date:", m.start_time);
    }
  });

  // Calculate calendar grid days for current month
  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);
  const startingDayOfWeek = firstDayOfMonth.getDay(); // 0 = Sun, 1 = Mon ...
  const daysInMonth = lastDayOfMonth.getDate();

  // Days from previous month
  const prevMonthLastDay = new Date(year, month, 0).getDate();
  const prevMonthDays: Date[] = [];
  for (let i = startingDayOfWeek - 1; i >= 0; i--) {
    prevMonthDays.push(new Date(year, month - 1, prevMonthLastDay - i));
  }

  // Days for current month
  const currentMonthDays: Date[] = [];
  for (let day = 1; day <= daysInMonth; day++) {
    currentMonthDays.push(new Date(year, month, day));
  }

  // Days for next month to complete 35 or 42 grid cells
  const totalDaysSoFar = prevMonthDays.length + currentMonthDays.length;
  const totalGridCells = totalDaysSoFar > 35 ? 42 : 35;
  const nextMonthDays: Date[] = [];
  for (let day = 1; day <= totalGridCells - totalDaysSoFar; day++) {
    nextMonthDays.push(new Date(year, month + 1, day));
  }

  const allGridDays = [...prevMonthDays, ...currentMonthDays, ...nextMonthDays];

  // Navigation handlers
  const handlePrevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const handleToday = () => {
    const today = new Date();
    setCurrentDate(today);
    setSelectedDate(today);
  };

  const getUserNameById = (userId: string): string => {
    const found = users.find((u) => u.id === userId);
    return found ? found.name : userId;
  };

  const handleCopyLink = (link: string, id: string) => {
    navigator.clipboard.writeText(link);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const selectedDateKey = formatDateKey(selectedDate);
  const selectedMeetings = meetingsByDate[selectedDateKey] || [];
  const todayKey = formatDateKey(new Date());

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
  const dayOfWeekNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  return (
    <div className="space-y-6">
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 p-4 rounded-2xl backdrop-blur-xl">
        {/* Month Navigation */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded-xl p-1">
            <button
              onClick={handlePrevMonth}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              title="Previous Month"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={handleToday}
              className="px-3 py-1 rounded-lg text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
            >
              Today
            </button>
            <button
              onClick={handleNextMonth}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              title="Next Month"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <h2 className="text-xl font-bold text-white tracking-tight">
            {monthNames[month]} <span className="text-slate-500 font-normal">{year}</span>
          </h2>
        </div>

        {/* View Switcher & Action */}
        <div className="flex items-center gap-2 self-end sm:self-auto">
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-xl p-1">
            <button
              onClick={() => setViewMode("month")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                viewMode === "month"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Grid className="w-3.5 h-3.5" />
              <span>Calendar Grid</span>
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                viewMode === "list"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <List className="w-3.5 h-3.5" />
              <span>List View</span>
            </button>
          </div>

          {onOpenScheduleModal && (
            <button
              onClick={onOpenScheduleModal}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-semibold text-xs transition-all shadow-md"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Meeting</span>
            </button>
          )}
        </div>
      </div>

      {viewMode === "month" ? (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Month Grid (3 cols on desktop) */}
          <div className="lg:col-span-3 bg-slate-900/70 border border-slate-800 rounded-2xl p-4 sm:p-6 backdrop-blur-xl">
            {/* Days of Week Header */}
            <div className="grid grid-cols-7 mb-2 text-center text-xs font-semibold text-slate-400 border-b border-slate-800/80 pb-3">
              {dayOfWeekNames.map((d, i) => (
                <div key={d} className={i === 0 || i === 6 ? "text-slate-500" : "text-slate-300"}>
                  {d}
                </div>
              ))}
            </div>

            {/* Calendar Grid Cells */}
            <div className="grid grid-cols-7 gap-1 sm:gap-2">
              {allGridDays.map((dateObj, idx) => {
                const dateKey = formatDateKey(dateObj);
                const dayNum = dateObj.getDate();
                const isCurrentMonth = dateObj.getMonth() === month;
                const isToday = dateKey === todayKey;
                const isSelected = dateKey === selectedDateKey;
                const dayMeetings = meetingsByDate[dateKey] || [];

                return (
                  <div
                    key={idx}
                    onClick={() => {
                      setSelectedDate(dateObj);
                      if (!isCurrentMonth) {
                        setCurrentDate(new Date(dateObj.getFullYear(), dateObj.getMonth(), 1));
                      }
                    }}
                    className={`min-h-[90px] sm:min-h-[110px] p-1.5 sm:p-2 rounded-xl border transition-all cursor-pointer flex flex-col justify-between ${
                      isSelected
                        ? "bg-emerald-500/10 border-emerald-500/50 shadow-lg shadow-emerald-500/5"
                        : isToday
                        ? "bg-cyan-500/5 border-cyan-500/40"
                        : isCurrentMonth
                        ? "bg-slate-950/60 border-slate-800/60 hover:border-slate-700/80 hover:bg-slate-900/60"
                        : "bg-slate-950/20 border-slate-900 text-slate-600 hover:bg-slate-900/30 opacity-40"
                    }`}
                  >
                    {/* Date Number Badge */}
                    <div className="flex items-center justify-between">
                      <span
                        className={`text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center ${
                          isToday
                            ? "bg-cyan-500 text-slate-950 font-extrabold"
                            : isSelected
                            ? "bg-emerald-500 text-slate-950 font-bold"
                            : isCurrentMonth
                            ? "text-slate-200"
                            : "text-slate-600"
                        }`}
                      >
                        {dayNum}
                      </span>

                      {dayMeetings.length > 0 && (
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                      )}
                    </div>

                    {/* Day Meetings Pills */}
                    <div className="space-y-1 my-1 overflow-hidden">
                      {dayMeetings.slice(0, 2).map((m) => {
                        const timeStr = new Date(m.start_time).toLocaleTimeString([], {
                          hour: "numeric",
                          minute: "2-digit"
                        });
                        return (
                          <div
                            key={m.id}
                            className="bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 rounded px-1.5 py-0.5 text-[10px] truncate leading-tight font-medium"
                            title={`${timeStr} - ${m.title}`}
                          >
                            <span className="font-semibold text-emerald-400 mr-1">{timeStr}</span>
                            {m.title}
                          </div>
                        );
                      })}

                      {dayMeetings.length > 2 && (
                        <div className="text-[10px] font-semibold text-cyan-400 px-1">
                          +{dayMeetings.length - 2} more
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Selected Day Agenda Sidebar */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between backdrop-blur-xl">
            <div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
                <div>
                  <div className="text-xs uppercase tracking-wider font-semibold text-emerald-400">
                    Agenda Details
                  </div>
                  <h3 className="text-lg font-bold text-white mt-0.5">
                    {selectedDate.toLocaleDateString("en-US", {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                      year: "numeric"
                    })}
                  </h3>
                </div>

                <Badge variant={selectedMeetings.length > 0 ? "success" : "neutral"}>
                  {selectedMeetings.length} {selectedMeetings.length === 1 ? "Meeting" : "Meetings"}
                </Badge>
              </div>

              {selectedMeetings.length === 0 ? (
                <div className="py-12 text-center text-slate-400 space-y-3">
                  <div className="w-10 h-10 rounded-full bg-slate-800/80 flex items-center justify-center mx-auto text-slate-500">
                    <CalendarIcon className="w-5 h-5" />
                  </div>
                  <p className="text-xs text-slate-400">
                    No meetings scheduled for this date.
                  </p>
                  {onScheduleForDate && (
                    <button
                      onClick={() => onScheduleForDate(formatDateKey(selectedDate))}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium transition-colors"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Schedule Meeting</span>
                    </button>
                  )}
                </div>
              ) : (
                <div className="space-y-4 max-h-[480px] overflow-y-auto pr-1">
                  {selectedMeetings.map((m) => {
                    const startTime = new Date(m.start_time).toLocaleTimeString([], {
                      hour: "numeric",
                      minute: "2-digit"
                    });
                    const endTime = new Date(m.end_time).toLocaleTimeString([], {
                      hour: "numeric",
                      minute: "2-digit"
                    });

                    return (
                      <div
                        key={m.id}
                        className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-3 hover:border-slate-700/80 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <h4 className="font-bold text-white text-sm leading-snug">
                            {m.title}
                          </h4>
                          <span className="text-[11px] font-semibold text-emerald-400 shrink-0 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-md">
                            {startTime} - {endTime}
                          </span>
                        </div>

                        {m.description && (
                          <p className="text-xs text-slate-400 leading-relaxed line-clamp-2">
                            {m.description}
                          </p>
                        )}

                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          <Users className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                          <div className="flex flex-wrap gap-1">
                            {m.attendee_ids.map((attId) => (
                              <span
                                key={attId}
                                className="bg-slate-900 border border-slate-800 text-slate-300 px-1.5 py-0.5 rounded text-[10px] font-medium"
                              >
                                {getUserNameById(attId)}
                              </span>
                            ))}
                          </div>
                        </div>

                        <div className="pt-2 border-t border-slate-800/80 flex items-center gap-2">
                          <a
                            href={m.meeting_link || "https://meet.google.com/new"}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-semibold text-xs transition-colors"
                          >
                            <Video className="w-3.5 h-3.5" />
                            <span>Join Google Meet</span>
                            <ExternalLink className="w-3 h-3 ml-auto opacity-70" />
                          </a>

                          <button
                            onClick={() => handleCopyLink(m.meeting_link || "https://meet.google.com/new", m.id)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                            title="Copy Meeting Link"
                          >
                            {copiedId === m.id ? (
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="mt-4 pt-4 border-t border-slate-800 text-center">
              <span className="text-[11px] text-slate-500 flex items-center justify-center gap-1">
                <Sparkles className="w-3 h-3 text-cyan-400" />
                <span>Synchronized with Google Meet</span>
              </span>
            </div>
          </div>
        </div>
      ) : (
        /* List / Agenda View */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {meetings.map((m) => {
            const formattedTime = new Date(m.start_time).toLocaleString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
              hour: "numeric",
              minute: "2-digit",
              hour12: true
            });

            return (
              <div
                key={m.id}
                className="bg-slate-900/80 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-6 flex flex-col justify-between transition-all duration-200 hover:shadow-xl hover:shadow-slate-950/50 backdrop-blur-xl group"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <h3 className="font-bold text-white text-base leading-snug group-hover:text-emerald-400 transition-colors">
                      {m.title}
                    </h3>
                    <Badge variant="success">Scheduled</Badge>
                  </div>

                  {m.description && (
                    <p className="text-xs text-slate-400 line-clamp-2 mb-4 leading-relaxed">
                      {m.description}
                    </p>
                  )}

                  <div className="space-y-2 mb-6 text-xs text-slate-300">
                    <div className="flex items-center gap-2 text-slate-300">
                      <CalendarIcon className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>{formattedTime}</span>
                    </div>

                    <div className="flex items-center gap-2 text-slate-400">
                      <Users className="w-4 h-4 text-cyan-400 shrink-0" />
                      <div className="flex flex-wrap gap-1">
                        {m.attendee_ids.map((attId) => (
                          <span
                            key={attId}
                            className="bg-slate-800 border border-slate-700/60 text-slate-200 px-2 py-0.5 rounded-md text-[11px] font-medium"
                          >
                            {getUserNameById(attId)}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-800/80 space-y-2">
                  <a
                    href={m.meeting_link || "https://meet.google.com/new"}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-semibold text-xs transition-all duration-200 shadow-sm"
                  >
                    <Video className="w-4 h-4" />
                    <span>Join Google Meet</span>
                    <ExternalLink className="w-3.5 h-3.5 opacity-70 ml-auto" />
                  </a>

                  <button
                    onClick={() => handleCopyLink(m.meeting_link || "https://meet.google.com/new", m.id)}
                    className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 text-xs transition-colors"
                  >
                    {copiedId === m.id ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-emerald-400 font-medium">Link Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy Meet Link</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
