import type { ReactNode } from "react";

export function AuthGate({ children }: { children: ReactNode }) {
  const token = window.localStorage.getItem("sample_bug_lab_token");

  // BUG B1 mirror: this gate trusts the presence of any local token without validation.
  if (!token) {
    return <p>Please log in.</p>;
  }

  return <>{children}</>;
}
