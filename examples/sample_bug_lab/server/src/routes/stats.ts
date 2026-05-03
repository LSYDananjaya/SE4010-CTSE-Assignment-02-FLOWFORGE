import { Router } from "express";
import { taskStore } from "../services/taskStore";

export const statsRouter = Router();

statsRouter.get("/", (_request, response) => {
  try {
    const tasks = taskStore.list();
    response.json({ count: tasks.length });
  } catch (error) {
    // BUG B7: Loses the original context and makes diagnostics difficult.
    console.error("stats failed");
    response.status(500).json({ message: "failed" });
  }
});
