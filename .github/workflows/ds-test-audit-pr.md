---
description: "Audits pull request code changes for data science testing opportunities using the ds-test-auditor agent"
on:
  pull_request:
    types: [opened, synchronize]
    paths:
      - '**/*.py'
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

You are reviewing a pull request. Your goal is to analyze only the changed `.py` files in the PR diff and identify testing opportunities.

## Step 1: Get the PR diff for Python files only

Use the GitHub tools to read the pull request diff. Filter the diff to include **only `.py` files** — ignore all other file types. Do NOT read the entire repository; focus exclusively on the diff content of `.py` files in this PR.

## Step 2: Analyze the diff content

Review the `.py` diff hunks from Step 1. Analyze only the added and modified code shown in the diff — do not read the full source files. Identify testing opportunities from the changed code by examining:
- Data loading and validation changes
- Target/label engineering logic
- Feature engineering transformations
- Potential data leakage risks
- Train/test split configuration
- Model training and evaluation code
- Output artifact handling

## Step 3: Post a checklist comment on the PR

Post a comment on the pull request containing a checklist of testing opportunities found in the diff. Each item should be a single short title summarizing the test opportunity. Use this format:

```
### 🧪 Test Opportunities

- [ ] Short title describing test opportunity 1
- [ ] Short title describing test opportunity 2
- [ ] Short title describing test opportunity 3
```

Keep each checklist item to one concise line. Do not include detailed descriptions, code references, or priority labels in the checklist — just a clear, short title for each test.

If no `.py` files were changed in the PR, call the `noop` tool with a message explaining that no Python code changes were detected.
