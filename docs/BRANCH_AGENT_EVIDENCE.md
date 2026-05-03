# Pawara Branch Agent Evidence

## Assigned Contribution

- Member: Pawara Sasmina
- Branch: `pawara`
- Agent: Context Agent
- Tool: RepoContextFinderTool
- Evaluation: Context retrieval evaluation and attachment handling

## Evidence Files

- `src/flowforge/agents/context_agent.py`
- `src/flowforge/tools/repo_context_finder.py`
- `tests/unit/test_context_agent.py`
- `tests/evals/test_context_eval.py`

## Viva Summary

Pawara can defend the Context Agent as the repository evidence retrieval stage. The agent receives the normalized request from Intake, uses RepoContextFinderTool to retrieve relevant local files, prioritizes user attachments, blocks path traversal attempts, limits snippet size, and passes a structured ContextBundle to the Planning Agent.

## Main Challenge

Keeping repository retrieval useful while avoiding unsafe or excessive file access.

## Resolution

The tool uses attachment-first retrieval, root-bound path checks, large-file skipping, keyword scoring, and bounded snippets.

## Viva Demonstration Checklist

- Show `context_agent.py` and explain why the agent runs after Intake.
- Show `repo_context_finder.py` and explain attachment-first retrieval.
- Demonstrate the path traversal check using the context evaluation test.
- Explain why bounded snippets help local SLMs stay reliable.
- Show that the Context Agent passes `ContextBundle` forward to Planning.

## Key Defense Point

This contribution proves that the MAS uses a real custom tool to interact with the local repository. The Context Agent does not depend only on LLM memory; it retrieves concrete files and snippets before reasoning.
