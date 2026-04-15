#!/usr/bin/env python3
"""Full GitHub Trending workflow: fetch trending repos + enrich with authors' Twitter posts.

Phase 1: Fetch GitHub trending (instant, no API key)
Phase 2: For each repo, find author's Twitter via GitHub API, then search their tweets

TinyFish API key is optional — without it, only trending data is returned.
"""

import argparse
import json
import os
import sys
import time
import importlib.util

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_module(name, path):
    """Dynamically load a Python module from file path."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    parser = argparse.ArgumentParser(
        description="Fetch GitHub trending + optionally enrich with authors' Twitter posts"
    )
    parser.add_argument("--language", default="", help="Programming language filter")
    parser.add_argument("--since", choices=["daily", "weekly", "monthly"], default="daily")
    parser.add_argument("--spoken-language", default="", help="Spoken language code")
    parser.add_argument("--count", type=int, default=12, help="Number of trending repos")
    parser.add_argument(
        "--tinyfish-key",
        default=os.environ.get("TINYFISH_API_KEY", ""),
        help="TinyFish API key for Twitter enrichment (optional)",
    )
    parser.add_argument("--enrich-count", type=int, default=12, help="How many repos to enrich")
    parser.add_argument("--format", choices=["json", "markdown", "table"], default="markdown")

    args = parser.parse_args()

    trending_mod = load_module("fetch_trending", os.path.join(SCRIPT_DIR, "fetch_trending.py"))
    social_mod = load_module("search_social", os.path.join(SCRIPT_DIR, "search_social.py"))

    # Phase 1: Fetch trending
    print("=== Phase 1: Fetching GitHub Trending ===", file=sys.stderr)
    url = trending_mod.build_url("repos", args.language, args.since, args.spoken_language)
    html = trending_mod.fetch_page(url)
    p = trending_mod.TrendingRepoParser()
    p.feed(html)
    repos = p.repos[:args.count]

    if not repos:
        print("No trending repos found.", file=sys.stderr)
        sys.exit(0)

    print(f"  Found {len(repos)} trending repos.", file=sys.stderr)

    # Phase 2: Enrich with author tweets (if API key provided)
    social_data = {}
    if args.tinyfish_key:
        enrich_count = min(args.enrich_count, len(repos))
        est_min = (enrich_count * 13) / 60

        print(f"\n=== Phase 2: Fetching Authors' Twitter Posts ({enrich_count} repos) ===", file=sys.stderr)

        # Step 2a: Batch fetch all author Twitter handles (fast, no TinyFish cost)
        print(f"  Resolving author Twitter handles...", file=sys.stderr)
        for repo_info in repos[:enrich_count]:
            owner = repo_info["repo"].split("/")[0]
            info = social_mod.get_author_twitter(owner)
            tw = info["twitter_username"]
            typ = info["type"]
            if tw:
                print(f"    {owner} -> @{tw} ({typ})", file=sys.stderr)
            else:
                print(f"    {owner} -> no Twitter ({typ})", file=sys.stderr)

        print(f"\n  Searching Twitter (~{est_min:.1f} min)...\n", file=sys.stderr)

        # Step 2b: Search author tweets
        for i, repo_info in enumerate(repos[:enrich_count]):
            repo_name = repo_info["repo"]
            print(f"  [{i+1}/{enrich_count}] {repo_name}", file=sys.stderr)

            result = social_mod.search_author_tweets(repo_name, args.tinyfish_key)
            social_data[repo_name] = result

            found = len(result["posts"])
            src = result["source"]
            if found:
                print(f"    Found {found} post(s) [source: {src}]", file=sys.stderr)
            else:
                print(f"    No posts found [source: {src}]", file=sys.stderr)

            if i < enrich_count - 1:
                time.sleep(13)
    else:
        print("\n  [skip] No TinyFish API key — Twitter enrichment skipped.", file=sys.stderr)

    # Output
    if args.format == "json":
        output = []
        for repo in repos:
            entry = dict(repo)
            entry["twitter"] = social_data.get(repo["repo"], {})
            output.append(entry)
        print(json.dumps(output, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(format_markdown_enriched(repos, social_data))
    else:
        print(format_table_enriched(repos, social_data))


def _source_label(result: dict) -> str:
    """Human-readable label for tweet source type."""
    src = result.get("source", "community")
    author = result.get("author", {})
    tw = author.get("twitter_username", "")
    if src == "author":
        return f"Author @{tw}"
    elif src == "org":
        return f"Org @{tw}"
    return "Community"


def format_markdown_enriched(repos: list, social_data: dict) -> str:
    lines = [
        "# GitHub Trending Report",
        "",
        "| # | Repository | Language | Stars | Today |",
        "|---|-----------|----------|-------|-------|",
    ]
    for r in repos:
        repo_link = f"[{r['repo']}]({r['url']})" if r.get("url") else r["repo"]
        lines.append(
            f"| {r['rank']} | {repo_link} | {r.get('language', '-')} | "
            f"{r.get('stars', '')} | +{r.get('today_stars', '')} |"
        )

    if social_data:
        lines += ["", "---", "", "## Project Details & Author Tweets", ""]
        for r in repos:
            repo_name = r["repo"]
            lines.append(f"### {r['rank']}. [{repo_name}]({r.get('url', '')})")
            lines.append("")
            if r.get("description"):
                lines.append(f"> {r['description']}")
                lines.append("")

            result = social_data.get(repo_name, {})
            author = result.get("author", {})
            tw = author.get("twitter_username", "")
            author_name = author.get("name", "")

            author_line = f"**Author:** {author_name}"
            if tw:
                author_line += f" ([@{tw}](https://x.com/{tw}))"
            lines.append(
                f"{author_line} | "
                f"**Language:** {r.get('language', '-')} | "
                f"**Stars:** {r.get('stars', '?')} | "
                f"**Today:** +{r.get('today_stars', '?')}"
            )
            lines.append("")

            posts = result.get("posts", [])
            if posts:
                source = _source_label(result)
                lines.append(f"**Tweets** (source: {source}):")
                lines.append("")
                for post in posts:
                    title = post.get("title", "").replace("|", "-")
                    url = post.get("url", "")
                    snippet = post.get("snippet", "").replace("\n", " ").strip()
                    if len(snippet) > 300:
                        snippet = snippet[:300].rsplit(" ", 1)[0] + "..."
                    lines.append(f"- [{title}]({url})")
                    if snippet:
                        lines.append(f"  > {snippet}")
                    lines.append("")
            else:
                lines.append("*No tweets found from this author.*")
                lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def format_table_enriched(repos: list, social_data: dict) -> str:
    lines = [
        f"{'#':<4} {'Repository':<40} {'Lang':<15} {'Stars':<10} {'Today':<10}",
        "=" * 79,
    ]
    for r in repos:
        result = social_data.get(r["repo"], {})
        author = result.get("author", {})
        tw = author.get("twitter_username", "")

        lines.append(
            f"{r['rank']:<4} {r['repo']:<40} {r.get('language', ''):<15} "
            f"{r.get('stars', ''):<10} +{r.get('today_stars', ''):<10}"
        )
        if r.get("description"):
            lines.append(f"     {r['description'][:74]}")
        if tw:
            lines.append(f"     Author: @{tw} ({author.get('name', '')})")

        posts = result.get("posts", [])
        for post in posts:
            title = post.get("title", "")[:60]
            lines.append(f"     -> {title}")
            snippet = post.get("snippet", "").replace("\n", " ").strip()[:100]
            if snippet:
                lines.append(f"        {snippet}")
        lines.append("-" * 79)
    return "\n".join(lines)


if __name__ == "__main__":
    main()
