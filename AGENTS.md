# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a pure-Python (stdlib only) project — no dependencies to install, no build step, no package manager. Python 3.7+ is the only system requirement.

### Running the scripts

All scripts are in `github-trending/scripts/` and documented in `README.md`. Key commands:

- **Phase 1 (trending repos, no API key):** `python3 github-trending/scripts/fetch_trending.py --since daily --count 12 --format json`
- **Phase 2 (author tweets, needs TinyFish key):** `python3 github-trending/scripts/search_social.py --repos "owner/repo" --api-key KEY`
- **Full pipeline:** `python3 github-trending/scripts/fetch_trending_full.py --since daily --count 12 --format markdown`

### Caveats

- There is no `requirements.txt`, `pyproject.toml`, or any package manifest — the project deliberately uses only Python stdlib (`urllib`, `json`, `argparse`, `html.parser`, etc.).
- There are no automated tests, no linter config, and no CI/CD pipeline in this repo.
- `search_social.py` and `fetch_trending_full.py` Phase 2 require a `TINYFISH_API_KEY` environment variable (or `--api-key`/`--tinyfish-key` flag). Without it, Phase 2 is skipped gracefully.
- TinyFish rate limit is 5 req/min; the scripts auto-sleep ~13s between requests. Enriching 12 repos takes ~2.5 min.
- GitHub Trending scraping uses HTML parsing — if GitHub changes their page structure, `fetch_trending.py` may need updates.
