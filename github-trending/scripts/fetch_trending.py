#!/usr/bin/env python3
"""Fetch GitHub trending repositories and developers by scraping github.com/trending."""

import argparse
import json
import re
import sys
import urllib.request
import urllib.error
from html.parser import HTMLParser


class TrendingRepoParser(HTMLParser):
    """Parse GitHub trending page HTML to extract repository data."""

    def __init__(self):
        super().__init__()
        self.repos = []
        self._current = {}
        self._in_article = False
        self._in_repo_name = False
        self._in_description = False
        self._in_language = False
        self._in_stars = False
        self._in_forks = False
        self._in_today_stars = False
        self._capture_text = False
        self._text_buf = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        itemprop = attrs_dict.get("itemprop", "")

        if tag == "article" and "Box-row" in cls:
            self._in_article = True
            self._current = {
                "rank": len(self.repos) + 1,
                "repo": "",
                "description": "",
                "language": "",
                "stars": "",
                "forks": "",
                "today_stars": "",
                "url": "",
            }

        if not self._in_article:
            return

        if tag == "h2" and "lh-condensed" in cls:
            self._in_repo_name = True

        if self._in_repo_name and tag == "a":
            href = attrs_dict.get("href", "")
            if href and not self._current["repo"]:
                self._current["url"] = f"https://github.com{href}"
                self._current["repo"] = href.strip("/")

        if tag == "p" and "color-fg-muted" in cls and "my-1" in cls:
            self._in_description = True
            self._capture_text = True
            self._text_buf = ""

        if tag == "span" and itemprop == "programmingLanguage":
            self._in_language = True
            self._capture_text = True
            self._text_buf = ""

        if tag == "a" and "Link--muted" in cls:
            href = attrs_dict.get("href", "")
            if "/stargazers" in href:
                self._in_stars = True
                self._capture_text = True
                self._text_buf = ""
            elif "/forks" in href or "/network" in href:
                self._in_forks = True
                self._capture_text = True
                self._text_buf = ""

        if tag == "span" and "d-inline-block" in cls and "float-sm-right" in cls:
            self._in_today_stars = True
            self._capture_text = True
            self._text_buf = ""

    def handle_endtag(self, tag):
        if tag == "article" and self._in_article:
            self._in_article = False
            if self._current.get("repo"):
                self.repos.append(self._current)
            self._current = {}

        if tag == "h2" and self._in_repo_name:
            self._in_repo_name = False

        if tag == "p" and self._in_description:
            self._in_description = False
            self._capture_text = False
            self._current["description"] = " ".join(self._text_buf.split())

        if self._in_language and tag == "span":
            self._in_language = False
            self._capture_text = False
            lang = self._text_buf.strip()
            if lang:
                self._current["language"] = lang

        if self._in_stars and tag == "a":
            self._in_stars = False
            self._capture_text = False
            self._current["stars"] = self._text_buf.strip().replace(",", "").replace(" ", "")

        if self._in_forks and tag == "a":
            self._in_forks = False
            self._capture_text = False
            self._current["forks"] = self._text_buf.strip().replace(",", "").replace(" ", "")

        if self._in_today_stars and tag == "span":
            self._in_today_stars = False
            self._capture_text = False
            raw = self._text_buf.strip()
            match = re.search(r"([\d,]+)", raw)
            self._current["today_stars"] = match.group(1).replace(",", "") if match else raw

    def handle_data(self, data):
        if self._capture_text:
            self._text_buf += data


class TrendingDevParser(HTMLParser):
    """Parse GitHub trending developers page."""

    def __init__(self):
        super().__init__()
        self.developers = []
        self._current = {}
        self._in_article = False
        self._in_name = False
        self._in_username = False
        self._in_repo = False
        self._capture_text = False
        self._text_buf = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")

        if tag == "article" and "Box-row" in cls:
            self._in_article = True
            self._current = {
                "rank": len(self.developers) + 1,
                "name": "",
                "username": "",
                "popular_repo": "",
                "url": "",
            }

        if not self._in_article:
            return

        if tag == "h1" and "h3" in cls:
            self._in_name = True
            self._capture_text = True
            self._text_buf = ""

        if self._in_name and tag == "a":
            href = attrs_dict.get("href", "")
            if href:
                self._current["url"] = f"https://github.com{href}"
                self._current["username"] = href.strip("/")

        if tag == "p" and "f6" in cls:
            self._in_username = True
            self._capture_text = True
            self._text_buf = ""

        if tag == "article" and "my-2" in cls:
            self._in_repo = True

        if self._in_repo and tag == "a" and "css-truncate" in cls:
            href = attrs_dict.get("href", "")
            self._capture_text = True
            self._text_buf = ""
            if href:
                self._current["popular_repo"] = href.strip("/")

    def handle_endtag(self, tag):
        if tag == "article" and self._in_article and self._current.get("username"):
            self._in_article = False
            self.developers.append(self._current)
            self._current = {}
        elif tag == "article" and self._in_repo:
            self._in_repo = False
            self._capture_text = False

        if tag == "h1" and self._in_name:
            self._in_name = False
            self._capture_text = False
            name = self._text_buf.strip()
            if name:
                self._current["name"] = " ".join(name.split())

        if tag == "p" and self._in_username:
            self._in_username = False
            self._capture_text = False

    def handle_data(self, data):
        if self._capture_text:
            self._text_buf += data


def fetch_page(url: str) -> str:
    """Fetch a URL and return the response body as text."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network Error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def build_url(type_: str, language: str, since: str, spoken_language: str) -> str:
    """Build the GitHub trending URL with query parameters."""
    base = "https://github.com/trending"
    if type_ == "developers":
        base += "/developers"
    if language:
        base += f"/{language}"

    params = []
    if since and since != "daily":
        params.append(f"since={since}")
    if spoken_language:
        params.append(f"spoken_language_code={spoken_language}")

    if params:
        base += "?" + "&".join(params)
    return base


def format_table(repos: list, type_: str) -> str:
    """Format results as an ASCII table."""
    if type_ == "developers":
        lines = [
            f"{'#':<4} {'Username':<25} {'Name':<30} {'Popular Repo':<40}",
            "-" * 99,
        ]
        for d in repos:
            lines.append(
                f"{d['rank']:<4} {d['username']:<25} {d['name']:<30} {d.get('popular_repo', ''):<40}"
            )
        return "\n".join(lines)

    lines = [
        f"{'#':<4} {'Repository':<40} {'Language':<15} {'Stars':<10} {'Forks':<10} {'Today':<10}",
        "-" * 89,
    ]
    for r in repos:
        lines.append(
            f"{r['rank']:<4} {r['repo']:<40} {r.get('language', ''):<15} "
            f"{r.get('stars', ''):<10} {r.get('forks', ''):<10} {r.get('today_stars', ''):<10}"
        )
    return "\n".join(lines)


def format_markdown(repos: list, type_: str) -> str:
    """Format results as a Markdown table."""
    if type_ == "developers":
        lines = [
            "| # | Username | Name | Popular Repo |",
            "|---|----------|------|--------------|",
        ]
        for d in repos:
            username = f"[{d['username']}]({d['url']})" if d.get("url") else d["username"]
            lines.append(
                f"| {d['rank']} | {username} | {d['name']} | {d.get('popular_repo', '')} |"
            )
        return "\n".join(lines)

    lines = [
        "| # | Repository | Language | Stars | Forks | Today |",
        "|---|-----------|----------|-------|-------|-------|",
    ]
    for r in repos:
        repo_link = f"[{r['repo']}]({r['url']})" if r.get("url") else r["repo"]
        desc = r.get("description", "")
        if desc:
            repo_link += f" - {desc}"
        lines.append(
            f"| {r['rank']} | {repo_link} | {r.get('language', '')} | "
            f"{r.get('stars', '')} | {r.get('forks', '')} | {r.get('today_stars', '')} |"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub trending repositories and developers")
    parser.add_argument("--type", choices=["repos", "developers"], default="repos", help="What to fetch")
    parser.add_argument("--language", default="", help="Programming language filter (e.g. python, rust)")
    parser.add_argument("--since", choices=["daily", "weekly", "monthly"], default="daily", help="Time range")
    parser.add_argument("--spoken-language", default="", help="Spoken language code (e.g. zh, en, ja)")
    parser.add_argument("--count", type=int, default=25, help="Number of results (1-25)")
    parser.add_argument("--format", choices=["table", "json", "markdown"], default="table", help="Output format")

    args = parser.parse_args()
    count = min(max(args.count, 1), 25)

    url = build_url(args.type, args.language, args.since, args.spoken_language)
    html = fetch_page(url)

    if args.type == "developers":
        p = TrendingDevParser()
        p.feed(html)
        results = p.developers[:count]
    else:
        p = TrendingRepoParser()
        p.feed(html)
        results = p.repos[:count]

    if not results:
        print("No trending results found. Try broader filters or a different time range.", file=sys.stderr)
        sys.exit(0)

    if args.format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(format_markdown(results, args.type))
    else:
        print(format_table(results, args.type))


if __name__ == "__main__":
    main()
