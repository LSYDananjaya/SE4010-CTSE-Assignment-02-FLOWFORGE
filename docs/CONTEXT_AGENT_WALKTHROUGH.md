# Context Agent Walkthrough

This note explains the Context Agent contribution on the `pawara` branch.

## Pipeline Position

The Context Agent runs after the Intake Agent has converted the raw request into structured goals, severity, scope, and summary. It uses that structured intake output to build a repository search query.

## Handoff Contract

Input from previous stage:

- `state.request.title`
- `state.request.description`
- `state.request.constraints`
- `state.request.attachments`
- `state.intake_result.goals`
- `state.intake_result.category`

Output to next stage:

- `state.context_bundle.files_considered`
- `state.context_bundle.selected_snippets`
- `state.context_bundle.constraints`
- `state.context_bundle.summary`

The Planning Agent should treat this bundle as its evidence source instead of searching the repository again.

## Main Responsibility

The agent must find the smallest useful set of local repository snippets for the Planning Agent. It should not invent files or rely only on LLM memory. Repository evidence is collected through `RepoContextFinderTool`.

## Tool Flow

1. Resolve the repository root.
2. Prioritize explicitly attached files.
3. Reject attachments that escape the repository root.
4. Skip dependency, build, cache, and hidden folders.
5. Score safe source/documentation files using keyword overlap.
6. Return bounded snippets to avoid overloading the local SLM prompt.

## Output

The agent produces a `ContextBundle` containing selected snippets, constraints, and a summary explaining why the snippets matter. This becomes the evidence base for the Planning Agent.

## Security Notes

The most important safety behavior is root-bound file access. Attachments such as `../../secret.txt` are treated as missing instead of being read from outside the selected project.
