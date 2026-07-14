---
name: github-agentic-workflows
description: Build, edit, compile, and review GitHub Agentic Workflows that execute repository scripts or Python files, pass GitHub Actions secrets to narrowly scoped script tools, interpret structured output, and perform controlled GitHub writes through safe outputs. Use for `.github/workflows/*.md` agentic workflows involving Bash allowlists, `mcp-scripts`, credentials or PATs, cross-repository API access, issue creation, or stale/missing `.lock.yml` files.
---

# GitHub Agentic Workflows

Create the workflow source in `.github/workflows/<workflow-id>.md`. Treat its YAML frontmatter as capabilities and its Markdown body as the agent prompt. Keep capabilities minimal, keep credentials outside the agent process, and compile every change.

## Choose the execution pattern

Use direct Bash only when the script needs no secret:

```yaml
tools:
  bash: ["python3 scripts/analyze_repository.py"]
```

Tell the agent to run the exact allowlisted command. Prefer a single fixed command over `bash: ["*"]`, especially when the workflow consumes issue, PR, comment, filename, or other untrusted input.

Use `mcp-scripts` when the script needs a secret:

```yaml
mcp-scripts:
  collect-repository-statistics:
    description: Collect repository statistics with read-only API access
    run: python3 scripts/analyze_github_repositories.py
    env:
      REPO_STATS_TOKEN: ${{ secrets.REPO_STATS_TOKEN }}
    timeout: 120
```

This scopes the secret to the predefined tool process. Do not place the credential in the prompt, command arguments, ordinary agent Bash environment, tool inputs, or output. Describe this as passing or scoping a secret to the script tool—not exposing the secret to the agent.

## Build the workflow

1. Inspect the script and establish its command, inputs, network needs, output contract, and failure behavior.
2. Use `workflow_dispatch` for a controlled manual experiment unless another trigger is required.
3. Set least-privilege workflow permissions, normally beginning with `contents: read`.
4. Select direct Bash or `mcp-scripts` using the rule above.
5. Define GitHub mutations under `safe-outputs`; do not give the agent an unrestricted write tool.
6. Write an imperative prompt that names the exact tool or command, validation rules, and output action.
7. Run the script locally, compile the workflow, inspect the generated lock file, and commit both files.

Minimal non-secret workflow:

```markdown
---
name: Repository Script Analysis
on:
  workflow_dispatch:
permissions:
  contents: read
engine: codex
tools:
  bash: ["python3 scripts/analyze_repository.py"]
safe-outputs:
  create-issue:
    max: 1
    title-prefix: "[script-analysis] "
---

Run `python3 scripts/analyze_repository.py` exactly once. Parse its stdout as
JSON, validate the documented fields, summarize the results, and call the
`create_issue` safe-output tool exactly once. Include the complete script output
and the validated execution-confirmation fields. If execution or validation
fails, create one failure issue containing only the actual sanitized error.
```

For a secret-backed workflow, replace direct Bash execution with an `mcp-scripts` definition and tell the agent to call that named MCP tool exactly once.

## Design the script output

Return machine-readable JSON on stdout. Keep progress and diagnostics on stderr only when the workflow can capture them safely. Include explicit contract fields such as:

```json
{
  "schema_version": 1,
  "script": "scripts/analyze_repository.py",
  "execution_confirmed": true,
  "statistics": {}
}
```

For authenticated calls, add a boolean such as `authentication_confirmed` and a non-secret identity such as the authenticated username. Never return tokens, authorization headers, environment dumps, credential-bearing URLs, or transformed fragments of secrets.

Require the agent to validate the contract before claiming success. An `execution_confirmed` field is useful experimental evidence, not cryptographic proof.

## Handle secrets safely

Create the secret in the repository or environment under **Settings → Secrets and variables → Actions**. Match its name exactly to `${{ secrets.NAME }}` in the workflow.

Apply these rules:

- Prefer a fine-grained PAT or GitHub App token with access only to required repositories and read-only permissions needed by the script.
- Remember that a token can report only repositories it is authorized to see. “All repositories” means all repositories granted to that token, not every repository on GitHub.
- Avoid classic PATs for read-only private-repository experiments: the classic `repo` scope is broad. A classic token with no scopes is suitable only for public data available to that user.
- Give the agent no general-purpose shell command capable of reading the secret-bearing process environment.
- Keep `set -x`, environment dumps, authorization headers, and token values out of script logs and exceptions.
- Sanitize HTTP errors before returning them. Do not rely only on GitHub log masking; encoded, split, or transformed credentials may evade masking.
- Never include the secret itself in a safe output, issue, artifact, cache, or raw script-output section.
- Do not run secret-dependent workflows for untrusted forked pull requests. GitHub normally withholds Actions secrets from fork-triggered workflows; do not weaken that boundary.

Keep the model engine credential separate from the business credential used by the script. For example, an engine API key authenticates `engine: codex`, while `REPO_STATS_TOKEN` belongs only to the statistics MCP script.

## Use controlled GitHub writes

Declare each intended mutation explicitly:

```yaml
safe-outputs:
  create-issue:
    max: 1
    title-prefix: "[agent-report] "
```

Tell the agent to call the corresponding safe-output tool, cap the number of outputs, and constrain titles, target repositories, and allowed files where supported. Use `staged: true` while testing a write path when a preview is sufficient.

For a cross-repository write, configure the safe output's supported `target-repo`/allowlist and a separately scoped `github-token: ${{ secrets.* }}` if the default `GITHUB_TOKEN` cannot perform it. Do not reuse a broad analysis PAT automatically.

## Compile and verify

GitHub runs the generated `.lock.yml`, not the Markdown source directly. After every source change, run:

```bash
python3 scripts/analyze_repository.py
gh aw compile <workflow-id>
gh aw compile <workflow-id> --strict
git diff -- .github/workflows/<workflow-id>.md \
  .github/workflows/<workflow-id>.lock.yml
```

Use the actual repository script in the first command. Review the generated workflow for the expected engine, command allowlist or MCP script, secret reference, permissions, and safe-output jobs. Commit both `.md` and `.lock.yml`. A stale lock file can make a correct source edit appear to have no effect or cause the run to use older capabilities.

Before handoff, verify:

- The script succeeds locally and emits only the documented JSON on stdout.
- Secret and non-secret scripts use the appropriate execution pattern.
- The agent cannot read or print the credential directly.
- Script output and exceptions are sanitized.
- The safe output is bounded and matches the requested GitHub action.
- `gh aw compile <workflow-id> --strict` succeeds.
- The source and regenerated lock file are both included in the change.

Consult the current official references when syntax may have changed: [MCP Scripts](https://github.github.com/gh-aw/reference/mcp-scripts/), [Tools](https://github.github.com/gh-aw/reference/tools/), [Safe Outputs](https://github.github.com/gh-aw/reference/safe-outputs/), and [CLI compilation](https://github.github.com/gh-aw/setup/cli/#compile).
