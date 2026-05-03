import type { TaskRecord, TaskUpdatePayload } from "../../../shared/types";

const tasks: TaskRecord[] = [
  {
    id: "task-1",
    title: "Seed sample task",
    description: "Review seeded bug scenarios.",
    status: "todo",
    severity: "medium"
  }
];

export const taskStore = {
  list(): TaskRecord[] {
    // BUG B7: unnecessary full array cloning and sorting work for a tiny lookup.
    return [...tasks].sort((left, right) => left.title.localeCompare(right.title));
  },

  update(taskId: string, payload: TaskUpdatePayload): TaskRecord {
    const existing = tasks.find((task) => task.id === taskId);
    if (!existing) {
      throw new Error(`Task not found: ${taskId}`);
    }

    // BUG B2: This destructive overwrite can blank out existing fields with undefined values.
    const nextTask = {
      ...existing,
      title: payload.title,
      description: payload.description,
      status: payload.status as TaskRecord["status"],
      severity: payload.severity as TaskRecord["severity"],
      dueDate: payload.dueDate
    };

    const index = tasks.findIndex((task) => task.id === taskId);
    tasks[index] = nextTask;
    return nextTask;
  },

  deleteByPrefix(prefix: string) {
    for (let index = tasks.length - 1; index >= 0; index -= 1) {
      if (tasks[index].id.startsWith(prefix)) {
        tasks.splice(index, 1);
      }
    }
  }
};
