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
Step 0: Ask user preferences (time range, output language)
            |
Phase 1: Fetch GitHub Trending -> present results immediately
            |
Phase 2 (optional): Resolve author Twitter -> search author tweets
```

## Step 0: Ask User Preferences

Before fetching data, ask the user two questions (if not already clear from their request):

> **1. 时间范围 / Time Range**
> - 今日热门 (Daily)
> - 本周热门 (Weekly)
> - 本月热门 (Monthly)
>
> **2. 输出语言 / Output Language**
> - 中文
> - English

If the user's message is in Chinese, default to 中文 output. If in English, default to English.
If the user already specified (e.g. "本周热门" or "this week's trending"), skip the question.

Map the choices:

| Choice | `--since` flag | Output |
|--------|---------------|--------|
| 今日 / Daily | `daily` | Present in chosen language |
| 本周 / Weekly | `weekly` | Present in chosen language |
| 本月 / Monthly | `monthly` | Present in chosen language |

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

**CRITICAL: After presenting, proceed to Phase 2 prompt.**

## Phase 2: Author Tweet Enrichment (Optional)

### Step 3: Check TinyFish API Key

Check if `TINYFISH_API_KEY` environment variable is already set.

**If key is already configured:** Skip asking, proceed directly to Step 4. The user has already set up their key and expects automatic enrichment.

**If key is NOT configured (first time):** Ask the user (in their chosen language):

**Chinese:**

> 以上是 GitHub Trending 的结果。
>
> 下一步获取这些项目的社交媒体分享，优先获取作者分享的内容。
> **这一步是可选的。** 如果需要，请提供 TinyFish API key（可在 [agent.tinyfish.ai/api-keys](https://agent.tinyfish.ai/api-keys) 免费获取）。
>
> 设置后无需每次提供：`export TINYFISH_API_KEY="your-key"`

**English:**

> Here are the GitHub Trending results.
>
> Next, I can fetch social media posts about these projects, prioritizing content shared by the authors themselves.
> **This step is optional.** If needed, provide a TinyFish API key (free at [agent.tinyfish.ai/api-keys](https://agent.tinyfish.ai/api-keys)).
>
> Set it once to skip this step in the future: `export TINYFISH_API_KEY="your-key"`

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
