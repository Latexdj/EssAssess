"use client";
import Link from "next/link";
import type { ClassListItem } from "@/lib/api/classes";

interface Props {
  cls: ClassListItem;
  href: string;
}

export default function ClassCard({ cls, href }: Props) {
  return (
    <Link
      href={href}
      className="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:border-blue-400 hover:shadow-md transition-shadow"
    >
      <p className="text-lg font-semibold text-gray-900">{cls.name}</p>
      {cls.programme && (
        <p className="text-sm text-gray-500 mt-0.5">{cls.programme}</p>
      )}
      <div className="mt-3 flex gap-4 text-sm text-gray-600">
        {cls.year_group && <span>Year {cls.year_group}</span>}
        {cls.academic_year && <span>{cls.academic_year}</span>}
        <span>{cls.student_count} student{cls.student_count !== 1 ? "s" : ""}</span>
      </div>
    </Link>
  );
}
