# Agent Script Test

This repository contains two experiments that test whether GitHub Agentic
Workflows can run repository-owned Python scripts, interpret their JSON output,
use credentials without exposing them, and request GitHub issues through the
safe-outputs mechanism.

## Experiment 1: allowlisted Bash execution

The manually triggered workflow in
`.github/workflows/repository-script-analysis.md`:

1. Checks out the repository with read-only contents permission.
2. Adds exactly one non-default command to the agent's Bash allowlist:
   `python3 scripts/analyze_repository.py`.
3. Requires the agent to interpret the analyzer's statistics while preserving
   its raw JSON output.
4. Gives the agent no direct issue write permission. Instead, the agent requests
   one issue through the `create-issue` safe output, which runs in a separate,
   permission-controlled job.

The resulting issue contains a readable summary, the complete script output,
and execution evidence.

## Experiment 2: secret-backed cross-repository analysis

The manually triggered workflow in
`.github/workflows/github-repository-statistics.md`:

1. Exposes `scripts/analyze_github_repositories.py` as a predefined, read-only
   MCP Script tool.
2. Injects `REPO_STATS_TOKEN` only into the MCP Script process. The generated
   workflow explicitly excludes it from the AI agent's sandbox.
3. Authenticates to GitHub and aggregates every repository accessible to the
   configured token, including visibility, language, ownership, star, issue,
   archive, fork, and size statistics.
4. Returns aggregate data only. It never returns repository names or the token.
5. Uses the separate `create-issue` safe-output job to publish the interpreted
   summary, raw JSON, and authentication/execution confirmation in this
   repository.

Use a dedicated fine-grained PAT with read-only access to only the repositories
you want counted. Do not reuse a broad personal or classic `repo` token. Add it
as a repository secret; this command prompts for the value without putting it
in the command itself:

```bash
gh secret set REPO_STATS_TOKEN
```

## Local verification

Run the local repository analyzer:

```bash
python3 scripts/analyze_repository.py
```

Run its tests:

```bash
python3 -m pytest -q
```

## Compile and run the workflow

The editable Markdown workflow must be compiled into a GitHub Actions lock file
before GitHub can run it:

```bash
gh auth login
gh extension install github/gh-aw
gh aw secrets bootstrap
gh aw compile
```

Commit each Markdown workflow and its generated `.lock.yml` file. Then use the
repository's **Actions** tab or trigger either experiment from the CLI:

```bash
gh aw run repository-script-analysis
gh aw run github-repository-statistics
```

GitHub Actions and repository Issues must be enabled, and the selected AI engine
must be available to the repository. This example uses GitHub Copilot.
