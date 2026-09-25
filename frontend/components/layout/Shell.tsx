"use client";

import React, { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { AuthProvider, useAuth } from "@/lib/auth";

function ShellContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading } = useAuth();
  const [mounted, setMounted] = React.useState(false);
  const isPublicAuthPage = pathname === "/login" || pathname === "/signup";

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !loading && !user && !isPublicAuthPage) {
      router.replace("/login");
    }
  }, [mounted, loading, user, isPublicAuthPage, router]);

  if (!mounted || (loading && !isPublicAuthPage) || (!loading && !user && !isPublicAuthPage)) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950 text-slate-400">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-semibold">Initializing Workspace...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-emerald-500/30 selection:text-emerald-200">
      {!isPublicAuthPage && <Sidebar />}
      <div className="flex-1 flex flex-col min-w-0">
        {!isPublicAuthPage && <Header />}
        <main className={isPublicAuthPage ? "flex-1" : "flex-1 p-6 md:p-8 overflow-y-auto"}>
          {children}
        </main>
      </div>
    </div>
  );
}

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <ShellContent>{children}</ShellContent>
    </AuthProvider>
  );
}

