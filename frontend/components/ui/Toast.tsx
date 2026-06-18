"use client";
import { useToast } from "@/lib/context/ToastContext";

const STYLES = {
  success: "bg-green-700 text-white",
  error:   "bg-red-700 text-white",
  info:    "bg-gray-800 text-white",
};

const ICONS = {
  success: "✓",
  error:   "✕",
  info:    "ℹ",
};

export default function ToastStack() {
  const { toasts, dismiss } = useToast();
  if (!toasts.length) return null;

  return (
    <div
      aria-live="polite"
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-start gap-3 rounded-lg px-4 py-3 shadow-lg animate-in slide-in-from-bottom-2 pointer-events-auto ${STYLES[t.variant]}`}
        >
          <span className="text-lg leading-none mt-0.5 shrink-0">{ICONS[t.variant]}</span>
          <p className="flex-1 text-sm font-medium leading-snug">{t.message}</p>
          <button
            onClick={() => dismiss(t.id)}
            className="shrink-0 opacity-80 hover:opacity-100 text-lg leading-none min-h-[44px] min-w-[44px] flex items-center justify-center -mr-2"
            aria-label="Dismiss"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
