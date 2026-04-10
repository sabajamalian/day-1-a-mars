---
description: "Runs daily to research and report the latest Data Science advancements with focus on Retail, Consumer Goods, and Snacking industry applications"
on:
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:

permissions:
  contents: read

engine:
  id: copilot
  agent: ds-news-reporter

safe-outputs:
  create-issue:
    labels: ["ds-news-reporter"]
    max: 1
    title-prefix: "[ds-news-reporter]"
  noop:
    report-as-issue: true
---

# Daily Data Science Find

**IMPORTANT**: Do NOT read any files from this repository. Do NOT invoke any skills. Your task is external research only.

## Step 1: Search GitHub for One Notable Finding

Run a single GitHub search for a recent repository (last 30 days) related to data science for retail, consumer goods, or snacking. Pick the single most interesting result.

If GitHub search tools are unavailable, use your training knowledge and note this.

## Step 2: Write a Short Report

Follow the format in your `ds-news-reporter` agent instructions. Keep it to one finding with a brief explanation and one team recommendation.

## Step 3: Save the Report

Use whichever approach works with your available tools:

1. **Preferred**: Call the `create_issue` safe-output tool with title "DS Daily Find — [DATE]" and the report as body.
2. **Alternative**: Write to `/tmp/gh-aw/ds-report.md`, then call `noop` with message: "DS Daily Find saved to /tmp/gh-aw/ds-report.md."
3. **Last resort**: Write to `/tmp/gh-aw/ds-report.md` using file-editing tools.
