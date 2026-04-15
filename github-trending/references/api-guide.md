# GitHub Trending API Guide

## Overview

GitHub does not provide an official API for trending data. This skill scrapes the public GitHub trending page at `https://github.com/trending`.

## URL Structure

### Trending Repositories

```
https://github.com/trending[/{language}][?since={daily|weekly|monthly}&spoken_language_code={code}]
```

### Trending Developers

```
https://github.com/trending/developers[/{language}][?since={daily|weekly|monthly}]
```

## Parameters

| Parameter | Location | Values | Notes |
|-----------|----------|--------|-------|
| language | path | Any GitHub language slug | Use lowercase, hyphens for spaces (e.g. `c++` → `c++`, `objective-c`) |
| since | query | `daily`, `weekly`, `monthly` | Default: `daily` |
| spoken_language_code | query | ISO 639-1 codes | e.g. `zh` (Chinese), `en` (English), `ja` (Japanese) |

## Common Language Slugs

| Language | Slug |
|----------|------|
| Python | `python` |
| JavaScript | `javascript` |
| TypeScript | `typescript` |
| Rust | `rust` |
| Go | `go` |
| Java | `java` |
| C++ | `c++` |
| C | `c` |
| Swift | `swift` |
| Kotlin | `kotlin` |
| Ruby | `ruby` |
| PHP | `php` |
| C# | `c%23` |
| Shell | `shell` |
| Dart | `dart` |
| Scala | `scala` |
| Lua | `lua` |
| Zig | `zig` |

## Rate Limiting

- GitHub trending page is publicly accessible without authentication
- Excessive scraping may trigger temporary IP blocks
- Recommended: no more than 1 request per 10 seconds
- If blocked, wait 60 seconds before retrying

## Response Data

### Repository Fields

| Field | Type | Description |
|-------|------|-------------|
| rank | int | Position on trending page (1-25) |
| repo | string | `owner/name` format |
| description | string | Repository description |
| language | string | Primary programming language |
| stars | string | Total star count |
| forks | string | Total fork count |
| today_stars | string | Stars gained in the selected period |
| url | string | Full GitHub URL |

### Developer Fields

| Field | Type | Description |
|-------|------|-------------|
| rank | int | Position on trending page |
| name | string | Display name |
| username | string | GitHub username |
| popular_repo | string | Featured repository `owner/name` |
| url | string | Profile URL |

## Error Handling

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 200 | Success | Parse HTML |
| 429 | Rate limited | Wait 60s, retry |
| 503 | Service unavailable | Retry after 30s |
| Other | Unexpected error | Report to user |
