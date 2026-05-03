# Context Agent Test Cases

These test cases support Pawara's Context Agent contribution.

## Test Case 1: Relevant Bug Context Retrieval

- Input: bug report about login timeout.
- Expected output: selected snippets include authentication or login-related files.
- Assertion focus: `ContextBundle.selected_snippets` is not empty and includes the expected file path.
- Purpose: verifies that the agent can retrieve useful repository evidence for a backend bug.

## Test Case 2: Attached File Priority

- Input: feature request that explicitly references `src/components/CategoryPicker.tsx`.
- Expected output: the attached file is selected before general keyword matches.
- Assertion focus: first selected snippet path equals the attached path.
- Purpose: verifies that user-specified evidence is respected.

## Test Case 3: Missing Attachment Handling

- Input: request containing an attachment path that does not exist.
- Expected output: workflow raises a controlled missing attachment error.
- Assertion focus: error message contains `Missing attachment`.
- Purpose: prevents silent planning based on incomplete evidence.

## Test Case 4: Path Traversal Blocking

- Input: attachment such as `../../outside.txt`.
- Expected output: file is marked as missing and is not read.
- Assertion focus: `missing_attachments` contains the unsafe path.
- Purpose: validates local repository boundary protection.

## Test Case 5: Snippet Bound Enforcement

- Input: query with `snippet_chars=80`.
- Expected output: every retrieved candidate has content length less than or equal to 80.
- Assertion focus: all candidate snippets respect the configured length.
- Purpose: keeps prompts compact for local SLM execution.
