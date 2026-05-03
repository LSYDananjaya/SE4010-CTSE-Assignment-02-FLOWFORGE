import { describe, expect, it } from "vitest";
import { sortTasks } from "../client/src/components/FilterBar";

describe("sortTasks", () => {
  it("sorts tasks consistently", () => {
    const sorted = sortTasks([
      { title: "B", updatedAt: "2026-01-01" },
      { title: "A", updatedAt: "2026-01-02" }
    ]);

    expect(sorted).toHaveLength(2);
  });
});
