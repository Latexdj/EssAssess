import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login"];

const ROLE_HOME: Record<string, string> = {
  admin:   "/admin",
  teacher: "/teacher",
  student: "/student",
};

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));
  const token = request.cookies.get("access_token")?.value;

  if (!token && !isPublic) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Decode role from JWT payload (no verification — server handles that)
  if (token && pathname === "/") {
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      const home = ROLE_HOME[payload.role as string] ?? "/login";
      return NextResponse.redirect(new URL(home, request.url));
    } catch {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  // Exclude Next.js internals, static files, and /api/* so rewrites can proxy to backend
  matcher: ["/((?!_next/static|_next/image|favicon.ico|public/|api/).*)"],
};
