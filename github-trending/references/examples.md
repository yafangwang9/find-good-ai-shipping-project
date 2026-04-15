# Usage Examples

## Example 1: Daily Trending (Phase 1 Only)

**User says:** "Show me what's trending on GitHub today"

**Agent runs:**

```bash
python scripts/fetch_trending.py --since daily --format json
```

**Agent presents:** Summary table with trending repos, then asks about Twitter enrichment.

---

## Example 2: Full Workflow with Twitter

**User says:** "GitHub trending 加上推特讨论"

**Phase 1:**

```bash
python scripts/fetch_trending.py --since daily --count 12 --format json
```

**Agent presents results, then asks:**

> 以上是今日 GitHub Trending 的结果。下一步可以为这些项目获取 Twitter/X 上的相关帖子。
> 这一步是可选的，需要 TinyFish API key，12 个项目预计 ~3 分钟。
> 请问是否需要？

**User provides key, Phase 2:**

```bash
python scripts/search_social.py \
  --repos "owner/repo1,owner/repo2,..." \
  --api-key USER_KEY \
  --platforms x \
  --count 12
```

---

## Example 3: Language-Specific Trending

**User says:** "What Rust projects are trending this week?"

```bash
python scripts/fetch_trending.py --language rust --since weekly --format json
```

Suggested presentation:
1. Full table of Rust trending repos
2. Top 3 brief summaries
3. Ask about Twitter enrichment

---

## Example 4: Quick Check (Few Projects)

**User says:** "Show me top 5 trending and their tweets"

**Phase 1:**

```bash
python scripts/fetch_trending.py --since daily --count 5 --format json
```

**Phase 2 (after user confirms, ~1 minute):**

```bash
python scripts/search_social.py \
  --repos "repo1,repo2,repo3,repo4,repo5" \
  --api-key KEY \
  --count 5
```

---

## Example 5: Single Command Pipeline

For users who already have a TinyFish key and want everything at once:

```bash
python scripts/fetch_trending_full.py \
  --tinyfish-key KEY \
  --since daily \
  --count 10 \
  --platforms x \
  --format markdown
```

---

## Example 6: Search Twitter for a Specific Repo

**User says:** "Search Twitter for posts about microsoft/markitdown"

```bash
python scripts/search_social.py \
  --repos "microsoft/markitdown" \
  --api-key KEY \
  --platforms x
```
