---
description: "Audits pull request code changes for data science testing opportunities using the ds-test-auditor agent"
on:
  pull_request:
    types: [opened, synchronize]
  reaction: "eyes"
  status-comment: true

permissions:
  contents: read
  pull-requests: read

engine:
  id: copilot
  agent: ds-test-auditor

safe-outputs:
  add-comment:
    target: "triggering"
    hide-older-comments: true
---

# Data Science Test Audit for Pull Requests

You are reviewing a pull request. Your goal is to analyze all changed Python files in this PR and produce a comprehensive testing audit.

## Step 1: Get the PR diff

Use the GitHub tools to read the pull request diff. Identify all Python files that were added or modified. Focus on files in the `solutions/` directory.

## Step 2: Read the full source files

For every changed Python file, read the COMPLETE file contents — not just the diff. Also read any README or documentation files in the same directory. Understand the full pipeline before auditing.

## Step 3: Run the DS-TEST-AUDIT-REPORT analysis

Following your ds-test-auditor instructions, analyze each pipeline stage:
- Data Loading & Ingestion
- Target/Label Engineering
- Feature Engineering
- Data Leakage Detection
- Train/Test Split
- Model Training
- Model Evaluation
- Output Artifacts
- Data Science Principles

Be thorough. Every test must include `code_reference`, concrete `input_spec`, and `expected_behavior`.

## Step 4: Format as PR comment

Convert your DS-TEST-AUDIT-REPORT into a clear, actionable PR comment with:

1. A **summary section** at the top with total tests found, counts by priority (critical/high/medium/low), and whether leakage risks were found
2. A **checklist of testing opportunities** grouped by category, formatted as GitHub task list checkboxes:
   ```
   ### Testing Opportunities

   #### Data Loading
   - [ ] `data_loading_01` — (critical) Verify CSV schema matches expected columns
   - [ ] `data_loading_02` — (high) Test handling of malformed rows

   #### Feature Engineering
   - [ ] `feature_engineering_01` — (critical) Check for target leakage in symptom text features
   ```
3. A **key concerns** section highlighting the most important findings, especially any data leakage risks

Log your full analysis to stdout so it appears in the workflow output window. Then post the checklist summary as a comment on the pull request.

If no Python data science files were changed in the PR, call the `noop` tool with a message explaining that no data science code changes were detected.
