---
name: GitHub Repository Statistics
description: Use a secret-backed Python tool to summarize repositories and safely open an issue

on:
  workflow_dispatch:

permissions:
  contents: read

engine: copilot

tools:
  bash: ["cat"]

mcp-scripts:
  collect-github-repository-statistics:
    description: Collect aggregate statistics for every repository accessible to a read-only GitHub token
    run: python3 scripts/analyze_github_repositories.py
    env:
      REPO_STATS_TOKEN: ${{ secrets.REPO_STATS_TOKEN }}
    timeout: 120

safe-outputs:
  create-issue:
    max: 1
    title-prefix: "[agent-secret-test] "
---

# Collect cross-repository statistics and report them safely

Call the `collect-github-repository-statistics` MCP tool exactly once. This is
the only tool authorized to receive the repository statistics credential. Never
request, print, transform, summarize, or otherwise expose the credential or any
environment variable.

Preserve the tool's complete output exactly as returned. If the tool reports
that a large result was stored in a file, read that file and preserve its entire
contents. Parse the result as JSON. A successful execution must contain all of
the following:

- `authentication_confirmed` is `true`.
- `execution_confirmed` is `true`.
- `script` is `scripts/analyze_github_repositories.py`.
- `schema_version` is `1`.
- `repository_scope` describes repositories accessible to the configured token.
- `statistics` is an object containing aggregate cross-repository statistics.

After validating the output, call the `create_issue` safe-output tool exactly
once. Use the title `Cross-repository statistics report`. Its body must use
these headings:

## Readable summary

Explain the important aggregate statistics in plain language. Distinguish the
total repositories accessible to the token from those owned directly by the
authenticated user. Do not invent repository names or other details that the
script did not return.

## Raw script output

Include the complete, unmodified tool output in a fenced `json` code block.

## Authentication and execution confirmation

State that the predefined Python tool ran and authenticated successfully.
Include the authenticated username, both confirmation values, the script path,
and schema version. Explicitly state that the credential itself was neither
returned by the script nor included in the issue.

If the tool fails or its output does not satisfy the contract, still create one
issue, title it `Cross-repository statistics execution failed`, include only the
sanitized error returned by the tool, and state that authentication or execution
was not confirmed. Never attempt to discover or reconstruct the credential.
