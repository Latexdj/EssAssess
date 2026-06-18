"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { classesApi, type ClassListItem } from "@/lib/api/classes";
import ClassCard from "@/components/lms/ClassCard";
import Button from "@/components/ui/Button";
import Alert from "@/components/ui/Alert";
import Spinner from "@/components/ui/Spinner";

export default function AdminClassesPage() {
  const [classes, setClasses] = useState<ClassListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  useEffect(() => {
    classesApi.list()
      .then(setClasses)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Classes</h1>
        <Link href="/admin/classes/new"><Button>New Class</Button></Link>
      </div>

      {error   && <Alert variant="error" message={error} />}
      {loading && <div className="flex justify-center py-8"><Spinner /></div>}

      {!loading && classes.length === 0 && (
        <p className="text-sm text-gray-500 py-6">No classes yet. Create one to get started.</p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {classes.map((cls) => (
          <ClassCard key={cls.id} cls={cls} href={`/admin/classes/${cls.id}`} />
        ))}
      </div>
    </div>
  );
}
