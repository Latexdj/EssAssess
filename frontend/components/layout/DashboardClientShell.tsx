"use client";
import type { ReactNode } from "react";
import { ToastProvider } from "@/lib/context/ToastContext";
import ToastStack from "@/components/ui/Toast";
import OfflineBanner from "@/components/ui/OfflineBanner";
import ErrorBoundary from "@/components/ui/ErrorBoundary";

export default function DashboardClientShell({ children }: { children: ReactNode }) {
  return (
    <ToastProvider>
      <OfflineBanner />
      <ErrorBoundary>
        {children}
      </ErrorBoundary>
      <ToastStack />
    </ToastProvider>
  );
}
