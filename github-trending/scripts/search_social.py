#!/usr/bin/env python3
"""Search Twitter/X for GitHub project authors' own tweets using TinyFish Search API.

Workflow:
1. Extract repo owner from "owner/repo" format
2. Call GitHub API to get owner's twitter_username
3. Search TinyFish for "project-name from:twitter_username site:x.com"
4. If no twitter_username, fallback to generic "project-name site:x.com"

API docs: https://docs.tinyfish.ai/search-api
Rate limit: TinyFish 5 req/min, GitHub 60 req/hour (unauthenticated)
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse


SEARCH_ENDPOINT = "https://api.search.tinyfish.ai"
GITHUB_API = "https://api.github.com"
RATE_LIMIT_DELAY = 13  # 5 req/min → 12s + 1s buffer

_twitter_cache = {}


def get_author_twitter(owner: str) -> dict:
    """Fetch owner's Twitter username and type via GitHub API. Results are cached."""
    if owner in _twitter_cache:
        return _twitter_cache[owner]

    url = f"{GITHUB_API}/users/{owner}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-trending-skill",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result = {
                "owner": owner,
                "name": data.get("name") or owner,
                "type": data.get("type", "User"),  # "User" or "Organization"
                "twitter_username": data.get("twitter_username"),
            }
            _twitter_cache[owner] = result
            return result
    except Exception as e:
        print(f"    [github api] {e}", file=sys.stderr)
        result = {"owner": owner, "name": owner, "type": "User", "twitter_username": None}
        _twitter_cache[owner] = result
        return result


def search_tinyfish(query: str, api_key: str, retries: int = 1) -> list:
    """Call TinyFish Search API. Returns list of {position, site_name, title, snippet, url}."""
    params = urllib.parse.urlencode({"query": query, "language": "en"})
    url = f"{SEARCH_ENDPOINT}?{params}"

    req = urllib.request.Request(url, headers={"X-API-Key": api_key})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("results", [])
    except urllib.error.HTTPError as e:
        if e.code == 429 and retries > 0:
            print(f"    [rate limited] waiting 15s before retry...", file=sys.stderr)
            time.sleep(15)
            return search_tinyfish(query, api_key, retries - 1)
        print(f"    [search error] HTTP {e.code}: {e.reason}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"    [search error] {e}", file=sys.stderr)
        return []


def search_author_tweets(repo_name: str, api_key: str) -> dict:
    """Search Twitter for a repo author's own tweets about the project.

    Returns {author: {...}, source: "author"|"org"|"community", posts: [...]}.
    """
    owner = repo_name.split("/")[0] if "/" in repo_name else repo_name
    short_name = repo_name.split("/")[-1] if "/" in repo_name else repo_name

    # Step 1: Get author's Twitter username from GitHub
    author_info = get_author_twitter(owner)
    twitter_user = author_info["twitter_username"]
    is_org = author_info["type"] == "Organization"

    # Step 2: Build search query
    if twitter_user:
        query = f"{short_name} from:{twitter_user} site:x.com"
        source = "org" if is_org else "author"
        label = f"@{twitter_user}" + (" (org)" if is_org else "")
        print(f"    Twitter: {label} → searching '{short_name}'...", file=sys.stderr)
    else:
        # Use "owner repo github" to anchor results to the actual project
        query = f"{owner} {short_name} github site:x.com"
        source = "community"
        print(f"    Twitter: no account found → community search '{owner} {short_name}'...", file=sys.stderr)

    # Step 3: Search
    results = search_tinyfish(query, api_key)

    # Step 4: Filter to x.com/twitter.com URLs, take top 2
    posts = []
    for r in results[:4]:
        url = r.get("url", "")
        if "x.com" not in url and "twitter.com" not in url:
            continue
        # If searching author, prefer posts from their account
        if twitter_user:
            site_name = r.get("site_name", "").lower()
            is_from_author = twitter_user.lower() in site_name or twitter_user.lower() in url.lower()
        else:
            is_from_author = False

        posts.append({
            "platform": "X (Twitter)",
            "url": url,
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "is_author_post": is_from_author,
        })
        if len(posts) >= 2:
            break

    return {
        "author": author_info,
        "source": source,
        "posts": posts,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Search Twitter/X for GitHub project authors' tweets"
    )
    parser.add_argument(
        "--repos",
        required=True,
        help="Comma-separated repo names (e.g. 'owner/repo,owner/repo') "
             "or path to JSON file from fetch_trending.py --format json",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("TINYFISH_API_KEY", ""),
        help="TinyFish API key (or set TINYFISH_API_KEY env var)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=12,
        help="Max number of repos to search (default: 12)",
    )

    args = parser.parse_args()

    if not args.api_key:
        print("Error: TinyFish API key required. Use --api-key or set TINYFISH_API_KEY.", file=sys.stderr)
        sys.exit(1)

    # Parse repos input
    repos_input = args.repos.strip()
    if repos_input.endswith(".json"):
        with open(repos_input, "r") as f:
            trending_data = json.load(f)
            repo_names = [item["repo"] for item in trending_data[:args.count]]
    else:
        repo_names = [r.strip() for r in repos_input.split(",")][:args.count]

    total = len(repo_names)
    est_minutes = (total * RATE_LIMIT_DELAY) / 60
    print(f"\n  Will search {total} repos for author tweets", file=sys.stderr)
    print(f"  Step 1: Fetching author Twitter handles from GitHub API...", file=sys.stderr)

    # Batch fetch all author Twitter handles first (GitHub API, fast, no TinyFish cost)
    for repo in repo_names:
        owner = repo.split("/")[0]
        info = get_author_twitter(owner)
        tw = info["twitter_username"]
        typ = info["type"]
        if tw:
            print(f"    {owner} → @{tw} ({typ})", file=sys.stderr)
        else:
            print(f"    {owner} → no Twitter ({typ})", file=sys.stderr)

    print(f"\n  Step 2: Searching Twitter ({total} searches, ~{est_minutes:.1f} min)...\n", file=sys.stderr)

    enriched = {}
    for i, repo in enumerate(repo_names):
        print(f"  [{i+1}/{total}] {repo}", file=sys.stderr)
        result = search_author_tweets(repo, args.api_key)
        enriched[repo] = result

        found = len(result["posts"])
        src = result["source"]
        if found:
            print(f"    Found {found} post(s) [source: {src}]", file=sys.stderr)
        else:
            print(f"    No posts found [source: {src}]", file=sys.stderr)

        # Rate limit (skip after last)
        if i < total - 1:
            time.sleep(RATE_LIMIT_DELAY)

    print(json.dumps(enriched, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
