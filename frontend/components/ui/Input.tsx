"use client";
import { InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, id, className = "", ...props }, ref) => {
    const inputId = id ?? label.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flex-col gap-1">
        <label htmlFor={inputId} className="text-sm font-medium text-gray-700">
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          className={`rounded-lg border px-3 py-3 text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px] ${
            error ? "border-red-500" : "border-gray-300"
          } ${className}`}
          {...props}
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";
