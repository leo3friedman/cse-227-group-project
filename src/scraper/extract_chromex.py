import os
import sys
import json
import asyncio
import aiohttp
import re
import base64
from urllib.parse import urlparse
from typing import Optional, List, Tuple

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_PATH = os.path.join(BASE_DIR, "secret.json")
LINKS_PATH = os.path.join(BASE_DIR, "extracted_urls", "github_links.json")


with open(SECRET_PATH) as f:
    token = json.load(f)["github_access_token"]
HEADERS = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

CHROME_LINK_RE = re.compile(
    r'https?://(?:chrome\.google\.com/webstore/detail/[^\s)]+|chromewebstore\.google\.com/[^\s)]+)'
)

# Progress bar
def print_progress(current: int, total: int, bar_length: int = 40) -> None:
    percent = current / total if total else 1
    filled_len = int(bar_length * percent)
    bar = '=' * filled_len + '-' * (bar_length - filled_len)
    sys.stdout.write(f"\rProgress: [{bar}] {current}/{total}")
    sys.stdout.flush()

# Extract owner/repo
def repo_from_url(url: str) -> Tuple[str, str]:
    parts = urlparse(url).path.strip("/\n").split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {url}")
    return parts[0], parts[1]

# Fetch manifest presence and README extraction
async def fetch_and_extract(session: aiohttp.ClientSession, url: str) -> Tuple[str, Optional[List[str]]]:
    owner, repo = repo_from_url(url)

    # Check for manifest.json at root
    manifest_api = f"https://api.github.com/repos/{owner}/{repo}/contents/manifest.json"
    async with session.get(manifest_api) as resp:
        manifest_found = (resp.status == 200)
    if not manifest_found:
        return url, None

    # Fetch README
    readme_api = f"https://api.github.com/repos/{owner}/{repo}/readme"
    async with session.get(readme_api) as resp:
        if resp.status == 200:
            data = await resp.json()
            content = data.get("content", "")
            text = base64.b64decode(content).decode("utf-8", errors="replace")
        else:
            text = ""

    # Extract and dedupe Chrome store links
    links = CHROME_LINK_RE.findall(text)
    links = list(dict.fromkeys(links))
    return url, links

async def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Scrape Chrome extension links with slicing and indexed outputs"
    )
    parser.add_argument(
        "--start", type=int, default=0,
        help="Start index (0-based) of repos list"
    )
    parser.add_argument(
        "--end", type=int, default=None,
        help="End index (exclusive) of repos list"
    )
    args = parser.parse_args()

    # Load URLs and slice
    with open(LINKS_PATH) as f:
        repo_urls = json.load(f)
    total_repos = len(repo_urls)
    start = args.start
    end = args.end if args.end is not None else total_repos
    if start < 0 or start >= total_repos or end < start:
        print(f"Invalid range: start={start}, end={end}, total={total_repos}")
        return
    subset = repo_urls[start:end]
    total = len(subset)

    results_with = {}
    results_noext = []
    connector = aiohttp.TCPConnector(limit=20)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        tasks = [asyncio.create_task(fetch_and_extract(session, url)) for url in subset]
        for idx, fut in enumerate(asyncio.as_completed(tasks), start=1):
            repo_url, links = await fut
            if links is None:
                # no manifest: skip
                pass
            elif links:
                results_with[repo_url] = links
            else:
                # manifest but no Chrome links
                results_noext.append(repo_url)
            print_progress(idx, total)


    out_dir = os.path.join(BASE_DIR, "extracted_urls")
    os.makedirs(out_dir, exist_ok=True)

    # Generate indexed output file names
    suffix = f"_{start}_{end}"
    out_with = os.path.join(out_dir, f"chrome_links{suffix}.json")
    out_noext = os.path.join(out_dir, f"chrome_links_noext{suffix}.json")

    # Report counts
    passed = len(results_with)
    no_ext = len(results_noext)
    print(f"\nRepos with manifest and links: {passed}/{total}. Repos with manifest but no links: {no_ext}/{total}.")

    # Write outputs
    with open(out_with, "w") as f:
        json.dump(results_with, f, indent=2)
    with open(out_noext, "w") as f:
        json.dump(results_noext, f, indent=2)
    print(f"Saved extension link JSON to {out_with} and no-link list to {out_noext}")

if __name__ == "__main__":
    asyncio.run(main())













