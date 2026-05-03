import type { TaskRecord, TaskUpdatePayload } from "../../../shared/types";

// BUG B4: The client sends status values that do not always match the server contract.
export async function updateTask(taskId: string, payload: TaskUpdatePayload): Promise<TaskRecord> {
  const response = await fetch(`/api/tasks/${taskId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      ...payload,
      status: payload.status === "in_progress" ? "in-progress" : payload.status
    })
  });

  if (!response.ok) {
    // BUG B7: Weak client-side diagnostics hide the actual server error details.
    throw new Error("Task update failed");
  }

  return response.json();
}
