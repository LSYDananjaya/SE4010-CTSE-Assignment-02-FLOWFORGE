import { Router } from "express";
import { requireSession } from "../services/sessionService";

export const authRouter = Router();

authRouter.get("/session", (request, response) => {
  // BUG B1: Returns success when any auth header exists; no real validation occurs.
  const authHeader = request.headers.authorization;
  if (authHeader) {
    return response.json({ authenticated: true, userId: "demo-user" });
  }

  return response.status(401).json({ authenticated: false });
});

authRouter.get("/admin", (request, response) => {
  requireSession(request);
  response.json({ dashboard: "admin" });
});
