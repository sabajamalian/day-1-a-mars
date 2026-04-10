---
description: "Runs daily to research and report the latest Data Science advancements with focus on Retail, Consumer Goods, and Snacking industry applications"
on:
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:

permissions:
  contents: read
  issues: write

engine:
  id: copilot
  agent: ds-news-reporter

safe-outputs:
  noop:
    report-as-issue: false
---

# Daily Data Science Advancements Report

You are generating a daily report on the most recent advancements in Data Science with a focus on applications in Retail, Consumer Goods, and the Snacking industry.

## Step 1: Search for Recent Data Science Advancements

Use GitHub's search tools to find recent repositories, papers, and projects related to:
- Machine learning and AI for retail analytics
- Consumer goods demand forecasting and inventory optimization
- Product recommendation systems
- Customer behavior analysis and segmentation
- Computer vision for retail (shelf analysis, checkout automation)
- Natural language processing for product reviews and consumer sentiment
- Anomaly detection in supply chains
- Pricing optimization with ML
- Snacking industry: flavor preference prediction, market basket analysis, product formulation with ML

Search for repositories created or updated in the last 30 days. Focus on practical, usable tools and proven techniques.

## Step 2: Compile and Format the Report

Following your `ds-news-reporter` agent instructions, produce a comprehensive markdown report covering:
1. An **Executive Summary** with top 3-5 key takeaways
2. **Featured Repositories** — recent GitHub projects with high relevance and links
3. **Emerging AI/ML Techniques** applicable to retail and snacking
4. **Retail & Consumer Goods Applications** — specific use cases and examples
5. **Snacking Industry Spotlight** — focused findings for snacks and food products
6. **Tools & Frameworks Update** — new or updated tools relevant to the industries
7. **Trend Analysis** — patterns observed across this research cycle
8. **Recommendations** — 3-5 actionable items for the data science team

## Step 3: Save the Report

Write the complete report to `/tmp/gh-aw/ds-report.md`.

Then call the `noop` tool with message: "Daily Data Science Advancements Report generated and saved."

The workflow will automatically create a GitHub issue with your report after you complete this step.
