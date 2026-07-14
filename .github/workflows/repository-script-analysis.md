---
name: Repository Script Analysis
description: Run the repository analyzer and safely publish its results as an issue

on:
  workflow_dispatch:

permissions:
  contents: read

engine: copilot

tools:
  bash: ["python3 scripts/analyze_repository.py"]

safe-outputs:
  create-issue:
    max: 1
    title-prefix: "[agent-script-test] "
---

# Run the repository analyzer and report its results

Run this exact command once:

`python3 scripts/analyze_repository.py`

Do not substitute another command, modify the script, or calculate repository
statistics yourself. Preserve the command's complete standard output exactly as
returned by the Bash tool.

Parse the standard output as JSON. A successful execution must contain all of
the following:

- `execution_confirmed` is `true`.
- `script` is `scripts/analyze_repository.py`.
- `schema_version` is `1`.
- `statistics` is an object containing the repository statistics.

After validating the output, call the `create_issue` safe-output tool exactly
once. Use the title `Repository analyzer execution report`. Its body must use
these headings:

## Readable summary

Explain the important statistics in plain language. This summary must be your
interpretation of the script results, not merely a copy of the JSON.

## Raw script output

Include the complete, unmodified standard output in a fenced `json` code block.

## Execution confirmation

State that the allowlisted command ran successfully. Include the exact command,
the `execution_confirmed` value, the script path, and the schema version as
evidence. Do not claim successful execution unless the required fields were
present in the actual command output.

If the command fails or its output does not satisfy the contract, still create
one issue, title it `Repository analyzer execution failed`, include the actual
output or error, and clearly state that execution was not confirmed. Never
invent missing output or statistics.
