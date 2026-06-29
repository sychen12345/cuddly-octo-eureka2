---
name: xhs-content-workflow
description: Plan and execute a Xiaohongshu-style content production workflow from niche intake, benchmark account or note analysis, comment-demand mining, topic-bank creation, and image-text card package drafting. Use when Codex is asked to find comparable creators or notes, mine comments for user needs, build a reusable topic library, generate Chinese short-form social content, or turn a few instructions into a benchmark-to-card workflow.
---

# XHS Content Workflow

Use this skill to turn a niche, a few benchmark clues, and comment snippets into a reusable Xiaohongshu content plan and image-text card package.

## Quick Start

If the user gives only a short instruction, proceed with explicit assumptions and ask for missing data only when it materially changes the output. Prefer this minimal intake:

```text
领域/产品:
目标人群:
已知对标:
评论/私信原话:
限制:
账号语气:
```

When the user wants current market evidence, search the web or the target platform if tools and permissions allow it. If live data is unavailable, clearly mark the result as a research framework or hypothesis and provide a sampling checklist.

For the bundled Coze-style Python workflow, require runtime `grok_api_key` and `openai_api_key` inputs before any node runs. Never echo, log, or include those API keys in final outputs.

## Workflow

1. Frame the niche.
   - Define target audience, urgent scenario, desired transformation, and monetization or conversion boundary.
   - State what evidence is provided versus assumed.

2. Find or normalize benchmarks.
   - Use provided account names, note URLs, titles, screenshots, or copied text first.
   - Extract growth signal, content format, title pattern, opening hook, proof style, visual style, cadence, and CTA.
   - Do not copy original wording; learn structure and demand signals.

3. Mine comment demand.
   - Classify comments into pain, desired outcome, blocker, objection, vocabulary, urgency, and action intent.
   - Preserve short anonymized user phrases as evidence.
   - Separate explicit needs from inferred needs.

4. Build the topic bank.
   - Convert demand clusters into topic records.
   - Score each topic by demand clarity, content fit, proof availability, differentiation, and conversion potential.
   - Include source traces from benchmark notes or comments so future users can audit why the topic exists.

5. Generate the card package.
   - Pick the strongest topic unless the user chooses one.
   - Produce cover headline options, page-by-page card copy, visual direction, image prompts, caption, hashtags, CTA, and review checklist.
   - Keep cards scannable: one idea per page, concrete examples, minimal jargon, and no unsupported outcome claims.

For durable outputs or Coze workflow integration, read `references/output-schema.md`.

## Output Order

Return sections in this order unless the user asks for a different format:

1. `研究摘要`
2. `对标拆解`
3. `评论需求洞察`
4. `选题库`
5. `图文卡片包`
6. `下一步指令`
7. `审核清单`

## Quality Gates

- Never invent real account metrics, comments, or platform trends.
- Mark assumptions and sampling gaps.
- Avoid promising revenue, follower growth, medical/legal/financial outcomes, or guaranteed virality.
- Use benchmark material for structure, not plagiarism.
- Make each topic traceable to at least one demand, scene, or benchmark pattern.
- For card copy, prioritize clarity and usefulness over dramatic language.

## Good Trigger Prompts

- `Use $xhs-content-workflow to make a topic bank for AI side-hustle notes from these comments.`
- `Use $xhs-content-workflow to analyze these benchmark Xiaohongshu notes and draft a 6-page card post.`
- `Use $xhs-content-workflow to turn this niche into benchmark research, comment demand, topics, and a card package.`
