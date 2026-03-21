# Workflows

Workflows are multi-step pipelines that require structured documentation. They differ from skills (simple, self-contained actions) in that they involve multiple tools, have defined inputs/outputs, and need edge case handling.

## When something is a workflow (not a skill)

If it involves multiple steps, multiple tools, or has meaningful edge cases — it's a workflow.

## Creating a Workflow

1. Create a new `.md` file with a descriptive name (e.g., `job_application.md`)
2. Include:
   - **Objective**: What the workflow accomplishes
   - **Inputs**: What data/parameters are required
   - **Steps**: Sequence of tools and logic
   - **Outputs**: What the workflow produces
   - **Edge Cases**: How to handle errors and special scenarios
   - **Rate Limits/Constraints**: Any API or system constraints discovered
