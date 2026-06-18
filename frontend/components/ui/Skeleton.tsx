interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = "" }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse rounded bg-gray-200 ${className}`}
      aria-hidden="true"
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-3" aria-hidden="true">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-3/5" />
          <Skeleton className="h-3 w-2/5" />
        </div>
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-4/5" />
    </div>
  );
}

export function SkeletonTable({ rows = 4 }: { rows?: number }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white overflow-hidden" aria-hidden="true">
      <div className="bg-gray-50 border-b border-gray-200 px-4 py-3">
        <Skeleton className="h-4 w-40" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="border-b border-gray-100 px-4 py-3 flex items-center gap-4">
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-2/5" />
            <Skeleton className="h-3 w-1/4" />
          </div>
          <Skeleton className="h-6 w-14 rounded-full" />
          <Skeleton className="h-4 w-16" />
        </div>
      ))}
    </div>
  );
}

export default Skeleton;
