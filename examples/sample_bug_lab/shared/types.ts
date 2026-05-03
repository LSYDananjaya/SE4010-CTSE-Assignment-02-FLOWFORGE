export type TaskStatus = "todo" | "in_progress" | "done";

// BUG B4: The frontend sometimes uses "in-progress" while the backend expects "in_progress".
export const clientStatusOptions = ["todo", "in-progress", "done"] as const;

export interface TaskRecord {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  severity: "low" | "medium" | "high";
  dueDate?: string;
}

export interface TaskUpdatePayload {
  title?: string;
  description?: string;
  status?: string;
  severity?: string;
  dueDate?: string;
}

export function normalizeStatus(status: string): TaskStatus {
  if (status === "in-progress") {
    return "in_progress";
  }
  if (status === "todo" || status === "in_progress" || status === "done") {
    return status;
  }
  return "todo";
}
