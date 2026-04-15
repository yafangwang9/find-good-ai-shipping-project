[中文版](README_CN.md)

# GitHub Trending Skill

> **Note:** Currently only GitHub Trending is supported. More discovery channels will be added over time.

The best shipping AI projects are rarely in funding lists or news. [GitHub Trending](https://github.com/trending) is where you find them. This skill fetches trending repos daily or weekly, and optionally pulls the authors' own social media posts via [TinyFish](https://tinyfish.ai) — helping you decide which builders are worth following.

## How It Works

```
Step 0   Ask: daily or weekly? Chinese or English?
            |
Phase 1  Fetch GitHub Trending → present results (instant)
            |
Phase 2  Resolve author Twitter via GitHub API
(optional)  → Search author's tweets via TinyFish
            → Present with project details
```

**Phase 1** is instant and requires no API key. **Phase 2** is optional, requires a free TinyFish API key, and prioritizes tweets from the project author themselves — not KOL reposts.

## Install

### Cursor

```bash
# Personal (available across all projects)
cp -r github-trending/ ~/.cursor/skills/github-trending/

# Or project-specific
cp -r github-trending/ .cursor/skills/github-trending/
```

### Claude.ai

1. Zip the `github-trending/` folder
2. Settings → Capabilities → Skills → Upload

### Claude Code

```bash
cp -r github-trending/ ~/.claude/skills/github-trending/
```

## First-time Setup

After installation, the skill will guide you through a one-time setup on first use:

1. **Choose default time range** — Daily / Weekly / Monthly
2. **Choose output language** — 中文 / English
3. **TinyFish API key (optional)** — for author tweet enrichment

Your preferences are saved to `config.json` automatically and reused in future sessions.

## Setup TinyFish API Key (Optional)

Social media enrichment requires a TinyFish API key. Without it, you still get full GitHub Trending data.

Get your key: [agent.tinyfish.ai/api-keys](https://agent.tinyfish.ai/api-keys)

```bash
# Set once, never asked again
export TINYFISH_API_KEY="sk-tinyfish-your-key-here"
```

## Usage

Once installed, the skill triggers when you ask about GitHub trending:

- "Show me this week's trending repos"
- "What's trending on GitHub today?"
- "Trending Rust projects this week"

### What You Get

**Phase 1 — Trending repos (instant):**

```
1. forrestchang/andrej-karpathy-skills — Stars 37,254 / Today +9,263
   A CLAUDE.md file to improve Claude Code behavior

2. thedotmack/claude-mem — Stars 56,521 / Today +2,997
   Claude Code persistent memory plugin
...
```

**Phase 2 — Author tweets (optional):**

```
1. forrestchang/andrej-karpathy-skills — Stars 37,254 / Today +9,263
   Author: Jiayuan Zhang (@jiayuan_jy)

   - I let Claude Code turn @karpathy's post into agent skills.
     It first generated a bunch of skill files and around 800 lines...
```

### Manual Script Usage

```bash
# Trending repos (no API key needed)
python github-trending/scripts/fetch_trending.py --since daily --count 12 --format json

# Weekly trending in Python
python github-trending/scripts/fetch_trending.py --since weekly --language python

# Author tweets for specific repos
python github-trending/scripts/search_social.py \
  --repos "microsoft/markitdown,forrestchang/andrej-karpathy-skills" \
  --api-key YOUR_KEY

# Full pipeline
python github-trending/scripts/fetch_trending_full.py \
  --tinyfish-key YOUR_KEY --since daily --count 12 --format markdown
```

## How Author Tweets Work

The skill doesn't just search "project name" on Twitter (which returns KOL reposts). Instead:

1. Extracts the repo owner from `owner/repo`
2. Calls GitHub API to get the owner's **actual Twitter handle**
3. Searches `"project from:author_handle site:x.com"` for precise results
4. If no Twitter is set, falls back to `"owner project github site:x.com"`

| Scenario | Search Strategy | Label |
|----------|----------------|-------|
| Author has Twitter | `from:handle` precise search | Author |
| Org with Twitter | `from:org_handle` search | Org |
| No Twitter set | `owner + repo + github` fallback | Community |

## Project Structure

```
github-trending/
├── SKILL.md                        # Skill instructions (read by AI)
├── config.json                     # User preferences (auto-generated on first use)
├── scripts/
│   ├── fetch_trending.py           # GitHub trending scraper (zero deps)
│   ├── search_social.py            # Author tweet search (GitHub API + TinyFish)
│   └── fetch_trending_full.py      # Single-command full pipeline
└── references/
    ├── api-guide.md                # API details and rate limits
    └── examples.md                 # Usage examples
```

## Requirements

- Python 3.7+
- Internet access
- No external packages (stdlib only)
- **Optional:** TinyFish API key for social media enrichment

## License

MIT

---

Built with [Cursor](https://cursor.com)
