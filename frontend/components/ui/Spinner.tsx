export function Spinner({ className = "" }: { className?: string }) {
  return (
    <div
      aria-label="Loading"
      className={`h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent ${className}`}
    />
  );
}

export default Spinner;
