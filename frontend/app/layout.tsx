import React from "react";
import "./globals.css";
import { Shell } from "@/components/layout/Shell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Work Operating System",
  description: "AI-powered project management and team collaboration platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen">
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
