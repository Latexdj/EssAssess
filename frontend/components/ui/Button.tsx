"use client";
import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "destructive";
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", loading = false, disabled, children, className = "", ...props }, ref) => {
    const base =
      "inline-flex items-center justify-center rounded-lg px-4 py-3 text-base font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px]";
    const variants = {
      primary:     "bg-blue-700 text-white hover:bg-blue-800 focus:ring-blue-500",
      secondary:   "bg-gray-100 text-gray-800 hover:bg-gray-200 focus:ring-gray-400",
      destructive: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
    };
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={`${base} ${variants[variant]} ${className}`}
        {...props}
      >
        {loading ? <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" /> : null}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
export default Button;
