"use client";
import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from "react";

export type ToastVariant = "success" | "error" | "info";

export interface ToastItem {
  id:      string;
  message: string;
  variant: ToastVariant;
}

interface ToastContextValue {
  toasts: ToastItem[];
  toast:  (message: string, variant?: ToastVariant) => void;
  dismiss:(id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

let _counter = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (message: string, variant: ToastVariant = "info") => {
      const id = `toast-${++_counter}`;
      setToasts((prev) => [...prev.slice(-3), { id, message, variant }]);
      setTimeout(() => dismiss(id), 4000);
    },
    [dismiss],
  );

  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside ToastProvider");
  return ctx;
}
