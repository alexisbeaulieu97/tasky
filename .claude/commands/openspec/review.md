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
- Treat task checkboxes with skepticism—verify the work exists, don't just trust `[x]` marks.
- Tasks marked `[x]` with labels like SKIPPED, DEFERRED, "justified", or "not needed" are NOT complete. Mark these as spec violations unless the spec was updated to reflect the reduced scope.
- If implementation is intentionally incomplete, `tasks.md` should reflect reality (use `[-]` for deferred, or remove tasks entirely, rather than marking them `[x]` complete).

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
   - For each task marked `[x]` in tasks.md:
     - Verify the corresponding artifact exists (code, test, doc, config change)
     - Check that the implementation is correct, not just present
     - Flag tasks with SKIPPED/DEFERRED labels as dishonest completion
     - Look for redundant or incorrect implementations (e.g., duplicate imports, suppressed warnings for claimed refactorings)
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
   - **Issues and Concerns**: Identify spec deviations, missing requirements, incomplete tasks, bugs, dishonest task completion
   - **Minor Observations**: Note positive architectural choices, documentation quality, code style
   - **Recommendations**: Suggest specific fixes for identified issues
   - **Overall Assessment**: Provide honest score (X/10) considering:
     - Implementation correctness (does it work?)
     - Spec compliance (does it meet requirements?)
     - Task honesty (are checkboxes accurate?)
     - Code quality (is it well-written?)
     - Deduct 2-3 points for tasks marked `[x]` that are incomplete, skipped, or deferred
     - Deduct points for misleading scope claims (e.g., "refactored complexity" but only added `# noqa` suppressions)

**Reference**
- Use `openspec show <id>` to get structured change information
- Use `openspec show <id> --json --deltas-only` for detailed spec delta inspection
- Use `openspec list --specs` to see what specs exist and their relationships
- Cross-reference file paths with line numbers (e.g., `path/to/file.py:123`) when discussing specific implementation details

**Red Flags to Watch For**
- Tasks marked `[x]` with parenthetical notes like "(DEFERRED)", "(SKIPPED)", "(not needed)", or "complexity justified"
- `# noqa` comments added for claimed refactorings (complexity wasn't reduced, just warnings suppressed)
- Comments in code saying "TODO" for tasks marked complete
- Tests that don't actually test the claimed behavior
- Duplicate or redundant code in files claimed to be "refactored" or "cleaned up"
- Spec requirements that the implementation violates but tasks.md claims are complete
- Local imports in files where circular imports were claimed to be resolved
<!-- OPENSPEC:END -->
