---
name: github-trending
description: >-
  Fetch and analyze GitHub trending repositories, developers, and topics,
  with optional author Twitter enrichment via TinyFish API.
  Use when the user asks about "GitHub trending", "trending repos",
  "popular repositories", "what's hot on GitHub", "trending developers",
  "trending by language", or wants to discover new open-source projects.
  Supports filtering by language, time range (daily/weekly/monthly),
  and spoken language. Can find what project authors themselves tweet
  about their own projects.
license: MIT
metadata:
  author: github-trending-skill
  version: 2.2.0
  tags: [github, trending, open-source, developer-tools, social-media]
---

# GitHub Trending

Fetch, analyze, and summarize GitHub trending repositories and developers. Optionally enrich with project authors' own Twitter posts.

## Workflow Overview

```
Step 0: Check config → ask user preferences (MANDATORY on first use)
            |
Phase 1: Fetch GitHub Trending -> present results immediately
            |
Phase 2 (optional): Prompt for TinyFish → enrich with author tweets
```

## Step 0: User Preferences (MANDATORY)

**MANDATORY: You MUST complete this step before running any script. Do NOT skip it.**

### Step 0a: Check for saved config

Look for `config.json` in the skill directory (same directory as this SKILL.md file).

- **If `config.json` exists:** Read saved preferences (`since`, `language`). Greet the user with their saved preferences and ask if they want to change anything, or proceed directly.
- **If `config.json` does NOT exist:** This is the first time. You MUST run the first-time setup below.

### Step 0b: First-time setup (when no config.json)

**MANDATORY: You MUST ask the user these two questions. Do NOT assume defaults. Do NOT skip. Wait for the user's answer before proceeding.**

Present exactly this prompt (detect language from the user's message — Chinese message → Chinese prompt, English message → English prompt):

**Chinese:**

> 👋 欢迎使用 GitHub Trending Skill！首次使用需要简单配置：
>
> **1. 默认时间范围？**
> - 今日热门 (Daily)
> - 本周热门 (Weekly)
> - 本月热门 (Monthly)
>
> **2. 输出语言？**
> - 中文
> - English
>
> 你的选择会被保存，下次无需重复设置。

**English:**

> 👋 Welcome to GitHub Trending Skill! Quick first-time setup:
>
> **1. Default time range?**
> - Daily
> - Weekly
> - Monthly
>
> **2. Output language?**
> - 中文
> - English
>
> Your choices will be saved for future use.

### Step 0c: Save preferences

After the user answers, save their choices to `config.json` in the skill directory:

```json
{
  "since": "daily",
  "language": "zh"
}
```

| Choice | `since` value | `language` value |
|--------|--------------|-----------------|
| 今日 / Daily | `"daily"` | `"zh"` or `"en"` |
| 本周 / Weekly | `"weekly"` | |
| 本月 / Monthly | `"monthly"` | |

**Exception:** If the user's request already explicitly specifies both time range AND language (e.g. "Show me this week's trending in English"), you may skip asking and save those as defaults directly. If only one is specified, still ask for the other.

## Phase 1: Fetch GitHub Trending

### Step 1: Run Script

```bash
python scripts/fetch_trending.py --since {daily|weekly|monthly} --count 12 --format json
```

### Step 2: Present Results

Present results in the user's chosen language.

**Chinese format:**

```
1. owner/repo — Stars 数量 / 今日(本周) +增长数
   项目描述（翻译为中文）
```

**English format:**

```
1. owner/repo — Stars count / Today(This week) +growth
   Project description
```

**CRITICAL: After presenting Phase 1 results, you MUST proceed to Phase 2 prompt. Do NOT end your response here.**

## Phase 2: Author Tweet Enrichment (Optional)

### Step 3: Check TinyFish API Key

**MANDATORY: You MUST perform this check and present the appropriate prompt. Do NOT skip this step.**

Check if `TINYFISH_API_KEY` environment variable is already set.

**If key is already configured:** Proceed directly to Step 4. The user has already set up their key and expects automatic enrichment.

**If key is NOT configured:** You MUST present the following prompt to the user. Do NOT skip it. Do NOT assume the user doesn't want enrichment. Always ask.

**Chinese:**

> 以上是 GitHub Trending 的结果。
>
> 📌 **下一步（可选）：** 我可以获取这些项目作者在 Twitter/X 上的原创帖子，帮你了解作者本人对项目的看法。
>
> 需要一个免费的 TinyFish API key：
> 1. 访问 [agent.tinyfish.ai/api-keys](https://agent.tinyfish.ai/api-keys) 获取
> 2. 设置环境变量（设置一次后续自动使用）：`export TINYFISH_API_KEY="your-key"`
>
> **是否需要获取作者推文？** 如果有 key 请直接提供，或者跳过此步。

**English:**

> Here are the GitHub Trending results.
>
> 📌 **Next step (optional):** I can fetch the project authors' own Twitter/X posts to help you understand their perspective on these projects.
>
> This requires a free TinyFish API key:
> 1. Get one at [agent.tinyfish.ai/api-keys](https://agent.tinyfish.ai/api-keys)
> 2. Set it once: `export TINYFISH_API_KEY="your-key"`
>
> **Want author tweets?** Provide your key to continue, or skip this step.

### Step 4: Run Search

```bash
python scripts/search_social.py \
  --repos "owner/repo1,owner/repo2,..." \
  --api-key USER_PROVIDED_KEY \
  --count 12
```

### Step 5: Present Enriched Results

For each project (in the user's chosen language):

**Chinese:**

```
1. owner/repo — Stars 数量 / 今日 +增长
   项目描述
   作者：Name (@twitter_handle)

   - 推文标题
     推文摘要内容
   - 推文标题
     推文摘要内容
```

**English:**

```
1. owner/repo — Stars count / Today +growth
   Description
   Author: Name (@twitter_handle)

   - Tweet title
     Tweet snippet
   - Tweet title
     Tweet snippet
```

If no tweets found, note:
- Chinese: "暂未找到作者相关推文"
- English: "No tweets found from this author."

## Single Command Pipeline

For users who want everything at once:

```bash
python scripts/fetch_trending_full.py \
  --tinyfish-key KEY \
  --since daily \
  --count 12 \
  --format markdown
```

## Troubleshooting

### Author has no Twitter set on GitHub

Normal. The script falls back to community search using "owner repo github site:x.com".

### GitHub API rate limit

60 req/hour without auth, plenty for 12 repos.

### TinyFish rate limit (429)

Auto-retries with backoff. ~13s interval between searches.

## Additional Resources

- For API details, see [references/api-guide.md](references/api-guide.md)
- For usage examples, see [references/examples.md](references/examples.md)
