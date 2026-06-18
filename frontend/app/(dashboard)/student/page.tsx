export default function StudentDashboard() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Student Dashboard</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-3xl font-bold text-gray-400">—</p>
          <p className="text-sm text-gray-600 mt-1">Open Assignments</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-3xl font-bold text-gray-400">—</p>
          <p className="text-sm text-gray-600 mt-1">Graded Submissions</p>
        </div>
      </div>
      <p className="text-sm text-gray-500">Assignments will appear here once your teacher publishes them.</p>
    </div>
  );
}
