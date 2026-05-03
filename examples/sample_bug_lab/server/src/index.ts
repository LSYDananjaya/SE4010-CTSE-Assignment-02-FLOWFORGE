import express from "express";
import { authRouter } from "./routes/auth";
import { statsRouter } from "./routes/stats";
import { tasksRouter } from "./routes/tasks";

export function createServer() {
  const app = express();
  app.use(express.json());
  app.use("/api/auth", authRouter);
  app.use("/api/tasks", tasksRouter);
  app.use("/api/stats", statsRouter);
  return app;
}
