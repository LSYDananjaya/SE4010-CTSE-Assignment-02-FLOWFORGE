import { Router } from "express";
import { normalizeStatus } from "../../../shared/types";
import { requireSession } from "../services/sessionService";
import { taskStore } from "../services/taskStore";

export const tasksRouter = Router();

tasksRouter.patch("/:taskId", (request, response) => {
  requireSession(request);

  const payload = request.body;

  // BUG B2: This can throw when payload is missing, causing a server crash path.
  const updatedTask = taskStore.update(request.params.taskId, {
    title: payload.title,
    description: payload.description,
    status: normalizeStatus(payload.status),
    severity: payload.severity,
    dueDate: payload.dueDate
  });

  response.json(updatedTask);
});

tasksRouter.delete("/:taskId", (request, response) => {
  requireSession(request);

  // BUG B2: deleteByPrefix is too broad and can remove multiple tasks unintentionally.
  taskStore.deleteByPrefix(request.params.taskId);
  response.status(204).send();
});
