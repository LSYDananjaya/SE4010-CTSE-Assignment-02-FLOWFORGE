import { describe, expect, it } from "vitest";
import { taskStore } from "../server/src/services/taskStore";

describe("taskStore", () => {
  it("lists tasks", () => {
    expect(taskStore.list().length).toBeGreaterThan(0);
  });

  // Intentionally incomplete: there is no regression test for destructive updates or broad deletes.
  it("does not yet cover delete safety", () => {
    expect(true).toBe(true);
  });
});
