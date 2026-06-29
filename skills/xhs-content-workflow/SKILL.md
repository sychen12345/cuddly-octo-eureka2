---
name: xhs-content-workflow
description: Plan and execute a Xiaohongshu-style content production workflow from niche intake, benchmark account or note analysis, comment-demand mining, high-view topic selection, editable prompt design, OpenAI text generation, Grok Expert 3:4 cartoon image-set generation, and final card package drafting. Use when Codex is asked to find comparable creators or notes, mine comments for user needs, build a reusable topic library, generate Chinese short-form social content, create 3:4 cartoon image prompts from reference images, or turn a few instructions into a benchmark-to-card workflow.
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
高浏览证据:
用户指定选题:
参考图规则:
限制:
账号语气:
```

When the user wants current market evidence, search the web or the target platform if tools and permissions allow it. If live data is unavailable, clearly mark the result as a research framework or hypothesis and provide a sampling checklist.

For the bundled Coze-style Python workflow, require runtime `grok_api_key` and `openai_api_key` inputs before any node runs. Never echo, log, or include those API keys in final outputs. Treat `prompt_overrides` as the online prompt editor for the workflow. Keep `execute_model_calls=false` for dry-run request plans; set it to `true` only when the workflow should directly call OpenAI Responses API and xAI/Grok image generation with the runtime keys.

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

4. Select the high-view topic.
   - Convert demand clusters into topic records.
   - Score each topic by demand clarity, content fit, proof availability, differentiation, conversion potential, and evidence such as views, saves, comments, search terms, or hot-word notes.
   - Use `user_selected_topic` when present, while still carrying evidence and risk notes.
   - Include source traces from benchmark notes or comments so future users can audit why the topic exists.

5. Build editable prompts.
   - Produce prompt blocks for topic selection, OpenAI text generation, Grok Expert image generation, and final review.
   - Apply user-provided overrides without losing the default prompts.

6. Generate text with OpenAI.
   - Use GPT5.5 ultra-high reasoning mode when available/configured.
   - In the Python workflow, `ultra_high` maps to OpenAI API `reasoning.effort=xhigh`.
   - Produce title options, page-by-page card script, caption, CTA, and a visual brief for the image model.

7. Generate a Grok Expert image set.
   - Produce 3:4 vertical cartoon prompts for each card page.
   - Use the configured xAI image model, defaulting to `grok-imagine-image-quality`, while keeping `grok_image_mode=Expert` as the workflow mode.
   - Use reference image notes to define character, color, line, lens, mood, and composition rules.
   - Keep the image set visually consistent across pages.

8. Generate the card package.
   - Pick the strongest topic unless the user chooses one.
   - Produce cover headline options, page-by-page card copy, Grok image prompts, caption, hashtags, CTA, and review checklist.
   - Keep cards scannable: one idea per page, concrete examples, minimal jargon, and no unsupported outcome claims.

For durable outputs or Coze workflow integration, read `references/output-schema.md`.

## Output Order

Return sections in this order unless the user asks for a different format:

1. `研究摘要`
2. `对标拆解`
3. `评论需求洞察`
4. `选题库`
5. `选中的高浏览选题`
6. `完整工作流节点`
7. `可在线编辑提示词`
8. `OpenAI GPT5.5 文案包`
9. `Grok Expert 3:4 卡通套图`
10. `图文卡片包`
11. `下一步指令`
12. `审核清单`

## Quality Gates

- Never invent real account metrics, comments, or platform trends.
- Mark assumptions and sampling gaps.
- Avoid promising revenue, follower growth, medical/legal/financial outcomes, or guaranteed virality.
- Use benchmark material for structure, not plagiarism.
- Make each topic traceable to at least one demand, scene, or benchmark pattern.
- Prefer topics with explicit views, saves, comments, search terms, or user-selected priority.
- Require 3:4 vertical aspect ratio for image-set prompts unless the user explicitly changes it.
- Use cartoon style by default; absorb reference-image rules without copying protected artwork.
- Keep prompt blocks editable and preserve both default and final prompt values.
- For card copy, prioritize clarity and usefulness over dramatic language.

## Good Trigger Prompts

- `Use $xhs-content-workflow to make a topic bank for AI side-hustle notes from these comments.`
- `Use $xhs-content-workflow to analyze these benchmark Xiaohongshu notes and draft a 6-page card post.`
- `Use $xhs-content-workflow to turn this niche into benchmark research, comment demand, topics, and a card package.`
