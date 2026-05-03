export function sortTasks(tasks: Array<{ title: string; updatedAt: string }>) {
  // BUG B5: Users expect newest-first, but this sorts oldest-first.
  return [...tasks].sort((left, right) => left.updatedAt.localeCompare(right.updatedAt));
}

export function FilterBar() {
  return (
    <section>
      <label>
        Search
        <input placeholder="Search tasks" />
      </label>
      <select defaultValue="updated">
        <option value="updated">Recently updated</option>
        <option value="severity">Severity</option>
      </select>
    </section>
  );
}
