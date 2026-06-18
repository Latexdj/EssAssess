"use client";
import { useState, useEffect } from "react";

export default function OfflineBanner() {
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    // Check initial state — may be offline on mount
    setOffline(!navigator.onLine);
    const go = () => setOffline(false);
    const stop = () => setOffline(true);
    window.addEventListener("online",  go);
    window.addEventListener("offline", stop);
    return () => {
      window.removeEventListener("online",  go);
      window.removeEventListener("offline", stop);
    };
  }, []);

  if (!offline) return null;

  return (
    <div
      role="alert"
      className="flex items-center gap-2 bg-amber-400 text-amber-900 px-4 py-2 text-sm font-medium"
    >
      <span className="text-base">⚠</span>
      <span>No internet connection — you may still type a draft, but cannot submit until reconnected.</span>
    </div>
  );
}
