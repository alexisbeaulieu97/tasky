---
name: OpenSpec: Review
description: Review completed implementation against OpenSpec change documentation.
category: OpenSpec
tags: [openspec, review, validation]
---
<!-- OPENSPEC:START -->
**Guardrails**
- Be honest and thorough in your assessment—identify both strengths and gaps.
- Focus on spec compliance, not stylistic preferences.
- Validate that the implementation satisfies all requirements and scenarios from the spec deltas.
- Check that all tasks from `tasks.md` are actually completed.

**Steps**
Track these steps as TODOs and complete them one by one.
1. Determine the change ID to review:
   - If this prompt already includes a specific change ID (for example inside a `<ChangeId>` block populated by slash-command arguments), use that value after trimming whitespace.
   - If the conversation references a change loosely (for example by title or summary), run `openspec list` to surface likely IDs, share the relevant candidates, and confirm which one the user intends.
   - Otherwise, review the conversation, run `openspec list`, and ask the user which change to review; wait for a confirmed change ID before proceeding.
2. Read the change documentation:
   - Read `openspec/changes/<id>/proposal.md` to understand the "Why" and "What Changes"
   - Read `openspec/changes/<id>/tasks.md` to see what was supposed to be implemented
   - Read all spec deltas in `openspec/changes/<id>/specs/*/spec.md` to understand requirements and scenarios
3. Examine the actual implementation:
   - Locate and read all files mentioned in the "Affected code" section of the proposal
   - Check dependency declarations in relevant `pyproject.toml` files
   - Verify package structure (directories, marker files like `py.typed`, README files)
   - Review test files to ensure test coverage exists
4. Validate against requirements:
   - For each requirement in the spec deltas, verify the implementation satisfies it
   - For each scenario, check that the described behavior is implemented
   - Cross-reference the tasks list to ensure all items were actually completed
5. Check quality and completeness:
   - Run the test suite: `uv run pytest` (or scoped to relevant packages)
   - Check code quality: `uv run ruff check`
   - Verify that validation steps from `tasks.md` pass (if applicable)
   - Look for missing tests, incomplete integrations, or spec deviations
6. Provide structured feedback:
   - **What You Did Well**: Highlight correct implementations, good practices, excellent code quality
   - **Issues and Concerns**: Identify spec deviations, missing requirements, incomplete tasks, bugs
   - **Minor Observations**: Note positive architectural choices, documentation quality, code style
   - **Recommendations**: Suggest specific fixes for identified issues
   - **Overall Assessment**: Provide honest score (X/10) and summary of compliance level

**Reference**
- Use `openspec show <id>` to get structured change information
- Use `openspec show <id> --json --deltas-only` for detailed spec delta inspection
- Use `openspec list --specs` to see what specs exist and their relationships
- Cross-reference file paths with line numbers (e.g., `path/to/file.py:123`) when discussing specific implementation details
<!-- OPENSPEC:END -->
