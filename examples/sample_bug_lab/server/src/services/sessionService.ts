import type { Request } from "express";

export function requireSession(request: Request) {
  const authHeader = request.headers.authorization;

  // BUG B1: Accepts any non-empty bearer token and does not verify signature or expiry.
  if (authHeader && authHeader.startsWith("Bearer ")) {
    return { userId: "demo-user" };
  }

  throw new Error("Unauthorized");
}
