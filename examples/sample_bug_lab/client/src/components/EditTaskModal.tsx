import { useState } from "react";

export function EditTaskModal() {
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");

  function handleSave() {
    // BUG B3: Empty title and obviously invalid due dates are accepted.
    console.log("Saving task", { title, dueDate });
  }

  return (
    <section>
      <h2>Edit Task</h2>
      <label>
        Title
        <input value={title} onChange={(event) => setTitle(event.target.value)} />
      </label>
      <label>
        Due Date
        <input value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
      </label>
      {/* BUG B3: No Escape handling, no focus trap, and the close action is not keyboard-friendly. */}
      <button onClick={handleSave}>Save</button>
    </section>
  );
}
