interface AlertProps {
  variant?: "info" | "error" | "success" | "warning";
  message?: string;
  className?: string;
  children?: React.ReactNode;
}

const styles = {
  info:    "bg-blue-50 border-blue-300 text-blue-800",
  error:   "bg-red-50 border-red-300 text-red-800",
  success: "bg-green-50 border-green-300 text-green-800",
  warning: "bg-yellow-50 border-yellow-300 text-yellow-800",
};

export function Alert({ variant = "info", message, className = "", children }: AlertProps) {
  return (
    <div role="alert" className={`rounded-lg border px-4 py-3 text-sm ${styles[variant]} ${className}`}>
      {message ?? children}
    </div>
  );
}

export default Alert;
