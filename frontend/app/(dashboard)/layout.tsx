import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";
import DashboardClientShell from "@/components/layout/DashboardClientShell";
import type { User } from "@/lib/types/auth";

async function getCurrentUser(): Promise<User | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) return null;

  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/auth/me`,
      {
        headers: { Cookie: `access_token=${token}` },
        cache: "no-store",
      }
    );
    if (!res.ok) return null;
    const data = await res.json();
    return data.user as User;
  } catch {
    return null;
  }
}

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar role={user.role} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Navbar user={user} />
        <DashboardClientShell>
          <main className="flex-1 overflow-y-auto p-6">{children}</main>
        </DashboardClientShell>
      </div>
    </div>
  );
}
